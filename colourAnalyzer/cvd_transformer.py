# backend/cvd_transformer.py
import os
import json
import numpy as np
import cv2

# SUPPRESS TENSORFLOW VERBOSE OUTPUT
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
tf.get_logger().setLevel('ERROR')

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
import warnings
warnings.filterwarnings('ignore')

# ============================================
# FIX: Keras-version compatibility shim.
# ============================================
# This is what actually fixes the crash you were hitting:
#   TypeError: Error when deserializing class 'InputLayer' using config=
#   {'batch_shape': [None, 3], ... 'optional': False}.
#   Exception encountered: Unrecognized keyword arguments:
#   ['batch_shape', 'optional']
#
# That error is a Keras-version mismatch between the environment that
# saved cvd_model.keras and the Keras version installed here - NOT a
# problem with your trained weights. safe_load_model() patches InputLayer
# deserialization so the installed (older) Keras can read the (newer)
# saved config, then loads the model completely normally. See
# keras_compat.py for the full explanation.
from keras_compat import safe_load_model


def _film_modulate(x, condition, channels, name):
    gamma = layers.Dense(channels, name=f'{name}_gamma')(condition)
    beta = layers.Dense(channels, name=f'{name}_beta')(condition)
    gamma = layers.Reshape((1, 1, channels))(gamma)
    beta = layers.Reshape((1, 1, channels))(beta)
    return layers.Add()([layers.Multiply()([x, gamma]), beta])


def _conv_block(x, filters, name):
    x = layers.Conv2D(filters, 3, padding='same', name=f'{name}_conv1')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    x = layers.Conv2D(filters, 3, padding='same', name=f'{name}_conv2')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    return x


def _upsample_block(x, skip, filters, name):
    x = layers.Conv2DTranspose(filters, 3, strides=2, padding='same', name=f'{name}_up')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    if skip is not None:
        if x.shape[1] != skip.shape[1] or x.shape[2] != skip.shape[2]:
            skip = layers.Resizing(x.shape[1], x.shape[2])(skip)
        x = layers.Concatenate()([x, skip])
    x = _conv_block(x, filters, name)
    return x


def build_cvd_transform_model(input_shape=(224, 224, 3), num_conditions=3):

    image_input = keras.Input(shape=input_shape, name='shirt_image')
    condition_input = keras.Input(shape=(num_conditions,), name='cvd_condition')

    base = MobileNetV2(input_shape=input_shape, include_top=False, weights=None)

    skip_names = ['block_1_expand_relu', 'block_3_expand_relu',
                  'block_6_expand_relu', 'block_13_expand_relu']
    skip_outputs = [base.get_layer(n).output for n in skip_names]
    bottleneck_output = base.output  # 7x7x1280 for 224 input

    encoder = keras.Model(base.input, skip_outputs + [bottleneck_output], name='mobilenetv2_encoder')
    s1, s2, s3, s4, bottleneck = encoder(image_input)

    cond_embed = layers.Dense(64, activation='relu', name='dense_2')(condition_input)
    cond_embed = layers.Dense(64, activation='relu', name='dense_3')(cond_embed)

    x = _film_modulate(bottleneck, cond_embed, bottleneck.shape[-1], name='bottleneck_film')
    x = _conv_block(x, 512, 'bottleneck')

    x = _upsample_block(x, s4, 256, 'up1')   # 7x7   -> 14x14
    x = _upsample_block(x, s3, 128, 'up2')   # 14x14 -> 28x28
    x = _upsample_block(x, s2, 64, 'up3')    # 28x28 -> 56x56
    x = _upsample_block(x, s1, 32, 'up4')    # 56x56 -> 112x112
    x = _upsample_block(x, None, 16, 'up5')  # 112x112 -> 224x224

    outputs = layers.Conv2D(3, 1, padding='same', activation='sigmoid',
                             name='recoloured_shirt')(x)

    model = keras.Model([image_input, condition_input], outputs, name='cvd_colour_transform')
    return model


class ModelWeightsNotLoadedError(RuntimeError):
    """Raised when the CVD model loaded but its weights are clearly not the
    trained weights (e.g. random/near-flat output). This exists so a broken
    model NEVER silently serves garbage images to users - it fails loudly
    at startup instead, with an explanation in the server log."""
    pass


class CVDTransformer:
    """
    Wrapper for Model 2: Conditional U-Net CVD Color Transformer.

    This model takes an RGB image and a CVD type and generates a simulated
    version of how a person with that CVD type would see the image.

    The model was trained on matched quadruplets of original + 3 CVD types.

    =========================================================================
    FIX #1 (blurry output): the network only ever runs at self.input_size
    (224x224, per training). transform() now extracts the CVD *colour
    change* the network learned (in LAB space, at 224x224), upsamples only
    that smooth colour-delta map with high-quality interpolation, and
    applies it onto the ORIGINAL full-resolution image - instead of
    stretching the network's small raw output back up (which is what made
    results blurry).

    FIX #2 (flat grey / blank output - the more serious bug): the old code
    had a silent fallback: if keras.models.load_model() failed for any
    reason, it would rebuild the architecture from scratch and call
    model.load_weights(path, skip_mismatch=True). For a native .keras
    archive (as opposed to a .h5/.weights.h5 file), load_weights() is NOT
    reliable - it can report "success" while loading few or none of the
    real trained weights, leaving the network essentially randomly
    initialized. A randomly-initialized sigmoid-output network produces
    almost exactly what you saw: a flat, near-uniform grey image with no
    shirt structure, because random weights average out to ~0.5 everywhere.

    This version:
      - Still tries load_model() first (the correct, exact way to restore
        your trained model) - unchanged behaviour when it works.
      - FIX #3 (this is the crash you hit most recently): load_model() now
        goes through safe_load_model(), which patches Keras InputLayer
        deserialization to tolerate the newer `batch_shape` / `optional`
        config keys. Previously, a Keras-version mismatch between the
        training environment and this server made load_model() raise a
        TypeError before it ever got to your weights, which then tripped
        the "not a .h5 file, refusing an unreliable fallback" guard below
        and crashed the whole request. This fix resolves the version
        mismatch directly instead of falling back to anything unreliable.
      - Only falls back to rebuild+load_weights for .h5 / .weights.h5 files,
        where by-name weight loading is actually reliable. For a .keras
        file, if load_model() still fails after the compatibility patch,
        it raises immediately with the real underlying error instead of
        quietly limping along.
      - Runs an automatic sanity check right after loading: feeds two very
        different synthetic images through the model and verifies the
        outputs are non-flat and actually differ from one another. If the
        model looks untrained/random, it raises ModelWeightsNotLoadedError
        with a clear diagnostic message instead of letting broken images
        reach your users.
    =========================================================================
    """

    # Below this per-channel std-dev, an output is considered "suspiciously
    # flat" (a properly trained model's output on a real/random-noise image
    # should show meaningfully more per-pixel variation than this).
    _FLATNESS_STD_THRESHOLD = 0.02

    def __init__(self, model_path, config_path):
        """
        Args:
            model_path: Path to the trained .keras model file (renamed to cvd_model.keras)
            config_path: Path to the preprocessing_config.json file
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.input_size = tuple(self.config['input_size'])
        self.cvd_types = self.config['cvd_types']
        self.normalization = self.config.get('normalization', 'divide_by_255')

        def combined_loss(y_true, y_pred):
            l1 = tf.reduce_mean(tf.abs(y_true - y_pred))
            ssim_term = 1.0 - tf.reduce_mean(tf.image.ssim(y_true, y_pred, max_val=1.0))
            return 0.85 * l1 + 0.15 * ssim_term

        def color_accuracy(y_true, y_pred):
            PIXEL_TOLERANCE = 0.06
            diff = tf.abs(y_true - y_pred)
            correct = tf.cast(tf.reduce_all(diff < PIXEL_TOLERANCE, axis=-1), tf.float32)
            return tf.reduce_mean(correct)

        def psnr_metric(y_true, y_pred):
            return tf.image.psnr(y_true, y_pred, max_val=1.0)

        def ssim_metric(y_true, y_pred):
            return tf.image.ssim(y_true, y_pred, max_val=1.0)

        custom_objects = {
            'combined_loss': combined_loss,
            'color_accuracy': color_accuracy,
            'psnr_metric': psnr_metric,
            'ssim_metric': ssim_metric,
            'Functional': keras.Model,
        }

        print(f"  Loading CVD model from: {model_path}")

        self.model = None
        load_model_error = None

        # --- Attempt 1: safe_load_model() - the correct, exact restore,   ---
        # --- now patched against the InputLayer batch_shape/optional bug ---
        try:
            self.model = safe_load_model(
                model_path, custom_objects=custom_objects, compile=False
            )
            print("  CVD model loaded successfully via safe_load_model().")
        except Exception as e:
            load_model_error = e
            print(f"  \u26a0\ufe0f  Full load_model() failed ({type(e).__name__}): {e}")

        # --- Attempt 2: rebuild + load_weights - ONLY reliable for .h5 files ---
        if self.model is None:
            is_h5 = str(model_path).lower().endswith(('.h5', '.weights.h5'))
            if not is_h5:
                # For a native .keras archive, load_weights() is not a safe
                # fallback - it can silently skip most/all real weights.
                # Fail loudly with the real error instead of guessing.
                raise RuntimeError(
                    "CVD model failed to load via keras.models.load_model() (even "
                    "with the Keras-version compatibility shim applied) and the "
                    "file is not a .h5/.weights.h5 file, so a weights-only fallback "
                    "would be unreliable and was skipped on purpose (this is what "
                    "previously caused flat grey output). "
                    f"Underlying load_model() error: {type(load_model_error).__name__}: "
                    f"{load_model_error}\n"
                    "If this is still the InputLayer batch_shape/optional TypeError, "
                    "double-check keras_compat.py is present next to this file and "
                    "importable. Otherwise this points to a deeper TensorFlow/Keras "
                    "version mismatch between the environment that trained/saved the "
                    "model (your Colab notebook) and the environment running this "
                    "Flask server. Check `tf.__version__` / `keras.__version__` in "
                    "both places and align them, or re-save the model from the "
                    "notebook using the exact TF/Keras version installed here."
                )
            print("  Falling back to architecture rebuild + weight loading (.h5 file detected)...")
            try:
                rebuilt = build_cvd_transform_model(
                    input_shape=(*self.input_size, 3),
                    num_conditions=len(self.cvd_types),
                )
                rebuilt.load_weights(model_path, by_name=True, skip_mismatch=True)
                self.model = rebuilt
                print("  CVD model weights restored via rebuild + load_weights().")
            except Exception as e2:
                raise RuntimeError(
                    f"Both load_model() and rebuild+load_weights() failed. "
                    f"load_model() error: {load_model_error}. "
                    f"load_weights() error: {e2}"
                ) from e2

        print(f"  CVD model ready. Input shape: {self.model.input_shape}")

        # --- Sanity check: catch "loaded but weights are garbage" cases ---
        self._verify_weights_are_real()

    def _verify_weights_are_real(self):
        """Runs two very different synthetic inputs through the model and
        checks the outputs are (a) not flat and (b) actually different from
        each other. Raises ModelWeightsNotLoadedError if the model looks
        untrained/randomly-initialized - this is what would have caught the
        flat-grey-image bug at server startup instead of in front of users.
        """
        h, w = self.input_size
        n_cond = len(self.cvd_types)

        rng = np.random.RandomState(42)
        img_a = rng.uniform(0, 1, size=(1, h, w, 3)).astype(np.float32)   # random noise
        img_b = np.zeros((1, h, w, 3), dtype=np.float32)
        img_b[:, : h // 2, :, 0] = 1.0    # solid-red top half
        img_b[:, h // 2:, :, 2] = 1.0     # solid-blue bottom half

        cond = np.zeros((1, n_cond), dtype=np.float32)
        cond[0, 0] = 1.0

        try:
            out_a = self.model.predict([img_a, cond], verbose=0)[0]
            out_b = self.model.predict([img_b, cond], verbose=0)[0]
        except Exception as e:
            raise ModelWeightsNotLoadedError(
                f"CVD model loaded but failed to run a test prediction: {e}"
            ) from e

        std_a = float(np.std(out_a))
        std_b = float(np.std(out_b))
        diff_ab = float(np.mean(np.abs(out_a - out_b)))

        if std_a < self._FLATNESS_STD_THRESHOLD and std_b < self._FLATNESS_STD_THRESHOLD:
            raise ModelWeightsNotLoadedError(
                f"CVD model loaded, but its output is suspiciously flat/uniform for "
                f"two very different test inputs (output std: {std_a:.4f} and "
                f"{std_b:.4f}). This is the signature of a model running on "
                f"random/untrained weights rather than your actual trained weights - "
                f"exactly what causes solid-grey output images. Re-check that "
                f"cvd_model.keras is the correct file exported from Cell 12 of "
                f"ColourBlind2_V9.ipynb (final_model.keras, renamed), and that it "
                f"wasn't truncated/corrupted during download or upload."
            )

        if diff_ab < self._FLATNESS_STD_THRESHOLD:
            raise ModelWeightsNotLoadedError(
                "CVD model loaded, but produced nearly identical output for two very "
                "different test inputs - the model does not appear to be responding "
                "to the input image at all, which points to the same "
                "untrained/random-weights problem described above."
            )

        print(f"  \u2705 Weight sanity check passed (output std: {std_a:.4f}/{std_b:.4f}, "
              f"input-sensitivity: {diff_ab:.4f}).")

    def transform(self, rgb_uint8_image, cvd_type):
        """
        Apply a CVD type transformation to the input image.

        Args:
            rgb_uint8_image: Input image as numpy array (H, W, 3) in RGB format, uint8.
            cvd_type: String, one of ['protanopia', 'deuteranopia', 'tritanopia'].

        Returns:
            Recoloured image as numpy array (H, W, 3) in RGB format, uint8,
            at the ORIGINAL input resolution with full original detail.
        """
        if cvd_type not in self.cvd_types:
            raise ValueError(f"cvd_type must be one of {self.cvd_types}")

        original_shape = rgb_uint8_image.shape[:2]  # (H, W)

        # --- 1. Run the network at its native resolution (unchanged) ---
        # INTER_AREA is the correct choice for shrinking - avoids the
        # aliasing/detail loss plain resize causes when downsampling.
        img_resized = cv2.resize(rgb_uint8_image, self.input_size, interpolation=cv2.INTER_AREA)

        if self.normalization == 'divide_by_255':
            img_input = img_resized.astype(np.float32) / 255.0
        else:
            img_input = img_resized.astype(np.float32) / 127.5 - 1.0

        cond_idx = self.cvd_types.index(cvd_type)
        cond_vec = np.zeros((1, len(self.cvd_types)), dtype=np.float32)
        cond_vec[0, cond_idx] = 1.0

        pred = self.model.predict(
            [np.expand_dims(img_input, 0), cond_vec],
            verbose=0
        )[0]

        # Bring both the network's input and output back to [0,1] regardless
        # of which normalization scheme is configured, so the delta below is
        # always computed in a consistent 0-1 RGB space.
        if self.normalization == 'divide_by_255':
            net_in_01 = img_resized.astype(np.float32) / 255.0
            net_out_01 = np.clip(pred, 0.0, 1.0)
        else:
            net_in_01 = (img_resized.astype(np.float32) / 127.5 - 1.0 + 1.0) / 2.0
            net_out_01 = np.clip((pred + 1.0) / 2.0, 0.0, 1.0)

        # --- 2. Compute the CVD colour change the network learned, in LAB ---
        # LAB separates lightness (L) from colour (a, b), which is exactly
        # what a colour-vision-deficiency shift should modify - so we only
        # transplant the a/b (and L) *delta*, not raw pixel values.
        lab_in = cv2.cvtColor(net_in_01, cv2.COLOR_RGB2LAB)
        lab_out = cv2.cvtColor(net_out_01.astype(np.float32), cv2.COLOR_RGB2LAB)
        delta_lab_small = (lab_out - lab_in).astype(np.float32)  # (input_size_h, input_size_w, 3)

        # --- 3. Upsample the smooth colour-delta map to full resolution ---
        delta_lab_full = cv2.resize(
            delta_lab_small,
            (original_shape[1], original_shape[0]),
            interpolation=cv2.INTER_CUBIC
        )

        # --- 4. Apply the delta onto the ORIGINAL full-resolution image ---
        original_01 = rgb_uint8_image.astype(np.float32) / 255.0
        lab_original_full = cv2.cvtColor(original_01, cv2.COLOR_RGB2LAB)

        lab_result_full = lab_original_full + delta_lab_full
        lab_result_full[:, :, 0] = np.clip(lab_result_full[:, :, 0], 0, 100)
        lab_result_full[:, :, 1] = np.clip(lab_result_full[:, :, 1], -127, 127)
        lab_result_full[:, :, 2] = np.clip(lab_result_full[:, :, 2], -127, 127)

        result_01 = cv2.cvtColor(lab_result_full, cv2.COLOR_LAB2RGB)
        output = np.clip(result_01 * 255.0, 0, 255).astype(np.uint8)

        return output