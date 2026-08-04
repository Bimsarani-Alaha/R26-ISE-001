import os
import json
import numpy as np
import cv2

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
tf.get_logger().setLevel('ERROR')

import warnings
warnings.filterwarnings('ignore')

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2

from models_common import load_layer_weights_into


# ============================================================
# ARCHITECTURE (was cvd_generator_architecture.py)
# ============================================================

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
    """Rebuilds the exact ColourBlind-2 architecture. weights=None -- the ImageNet
    backbone weights are NOT re-downloaded; they come back from the trained weights
    file along with everything else, so this works with no internet access at all."""
    image_input = keras.Input(shape=input_shape, name='shirt_image')
    condition_input = keras.Input(shape=(num_conditions,), name='cvd_condition')

    base = MobileNetV2(input_shape=input_shape, include_top=False, weights=None)

    skip_names = ['block_1_expand_relu', 'block_3_expand_relu',
                  'block_6_expand_relu', 'block_13_expand_relu']
    skip_outputs = [base.get_layer(n).output for n in skip_names]
    bottleneck_output = base.output

    encoder = keras.Model(base.input, skip_outputs + [bottleneck_output], name='mobilenetv2_encoder')
    s1, s2, s3, s4, bottleneck = encoder(image_input)

    cond_embed = layers.Dense(64, activation='relu', name='dense_2')(condition_input)
    cond_embed = layers.Dense(64, activation='relu', name='dense_3')(cond_embed)

    x = _film_modulate(bottleneck, cond_embed, bottleneck.shape[-1], name='bottleneck_film')
    x = _conv_block(x, 512, 'bottleneck')

    x = _upsample_block(x, s4, 256, 'up1')
    x = _upsample_block(x, s3, 128, 'up2')
    x = _upsample_block(x, s2, 64, 'up3')
    x = _upsample_block(x, s1, 32, 'up4')
    x = _upsample_block(x, None, 16, 'up5')

    outputs = layers.Conv2D(3, 1, padding='same', activation='sigmoid',
                             dtype='float32', name='recoloured_shirt')(x)

    model = keras.Model([image_input, condition_input], outputs, name='cvd_colour_transform')
    return model


# ============================================================
# TRANSFORMER WRAPPER (was cvd_transformer.py)
# ============================================================

class ModelWeightsNotLoadedError(RuntimeError):
    """Raised when the CVD model loaded but its weights are clearly not the trained weights."""
    pass


class CVDTransformer:
    """
    Wrapper for Model 2: Conditional U-Net CVD Color Transformer.

    weights_path should point at the .npz file (models/cvd_generator_weights.npz),
    NOT a .keras file.
    """

    _FLATNESS_STD_THRESHOLD = 0.02

    def __init__(self, weights_path, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.input_size = tuple(self.config['input_size'])
        self.cvd_types = self.config['cvd_types']
        self.normalization = self.config.get('normalization', 'divide_by_255')

        print("  Building architecture (model_cvd.py)...")
        self.model = build_cvd_transform_model(
            input_shape=(*self.input_size, 3),
            num_conditions=len(self.cvd_types),
        )

        print(f"  Loading weights (pure NumPy, Keras-version-agnostic) from: {weights_path}")
        if not os.path.exists(weights_path):
            raise FileNotFoundError(
                f"{weights_path} not found. This .npz file must be exported once, "
                f"in an environment where the original trained .keras file loads "
                f"successfully."
            )
        load_layer_weights_into(self.model, weights_path, strict=True)

        self._verify_weights_are_real()

    def _verify_weights_are_real(self):
        h, w = self.input_size
        n_cond = len(self.cvd_types)

        rng = np.random.RandomState(42)
        img_a = rng.uniform(0, 1, size=(1, h, w, 3)).astype(np.float32)
        img_b = np.zeros((1, h, w, 3), dtype=np.float32)
        img_b[:, : h // 2, :, 0] = 1.0
        img_b[:, h // 2:, :, 2] = 1.0

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
                f"CVD model output is suspiciously flat/uniform for two very different "
                f"test inputs (output std: {std_a:.4f} and {std_b:.4f})."
            )

        if diff_ab < self._FLATNESS_STD_THRESHOLD:
            raise ModelWeightsNotLoadedError(
                "CVD model produced nearly identical output for two very different "
                "test inputs - the model does not appear to be responding to the input."
            )

        print(f"  \u2705 Weight sanity check passed (output std: {std_a:.4f}/{std_b:.4f}, "
              f"input-sensitivity: {diff_ab:.4f}).")

    def transform(self, rgb_uint8_image, cvd_type):
        """
        Apply a CVD type transformation to the input image.
        (The LAB delta-blending post-processing is Model 2's actual "skill"
        and has nothing to do with the loading mechanism above.)
        """
        if cvd_type not in self.cvd_types:
            raise ValueError(f"cvd_type must be one of {self.cvd_types}")

        original_shape = rgb_uint8_image.shape[:2]

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

        if self.normalization == 'divide_by_255':
            net_in_01 = img_resized.astype(np.float32) / 255.0
            net_out_01 = np.clip(pred, 0.0, 1.0)
        else:
            net_in_01 = (img_resized.astype(np.float32) / 127.5 - 1.0 + 1.0) / 2.0
            net_out_01 = np.clip((pred + 1.0) / 2.0, 0.0, 1.0)

        lab_in = cv2.cvtColor(net_in_01, cv2.COLOR_RGB2LAB)
        lab_out = cv2.cvtColor(net_out_01.astype(np.float32), cv2.COLOR_RGB2LAB)
        delta_lab_small = (lab_out - lab_in).astype(np.float32)

        delta_lab_full = cv2.resize(
            delta_lab_small,
            (original_shape[1], original_shape[0]),
            interpolation=cv2.INTER_CUBIC
        )

        original_01 = rgb_uint8_image.astype(np.float32) / 255.0
        lab_original_full = cv2.cvtColor(original_01, cv2.COLOR_RGB2LAB)

        lab_result_full = lab_original_full + delta_lab_full
        lab_result_full[:, :, 0] = np.clip(lab_result_full[:, :, 0], 0, 100)
        lab_result_full[:, :, 1] = np.clip(lab_result_full[:, :, 1], -127, 127)
        lab_result_full[:, :, 2] = np.clip(lab_result_full[:, :, 2], -127, 127)

        result_01 = cv2.cvtColor(lab_result_full, cv2.COLOR_LAB2RGB)
        output = np.clip(result_01 * 255.0, 0, 255).astype(np.uint8)

        return output