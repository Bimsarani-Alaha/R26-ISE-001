import os
import json
import numpy as np

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
# ARCHITECTURE (was pattern_architecture.py)
# ============================================================

def build_unet_encoder(input_shape=(224, 224, 3), backbone_weights=None):
    base = MobileNetV2(input_shape=input_shape, include_top=False, weights=backbone_weights)
    skip_names = [
        'block_1_expand_relu',   # 112x112
        'block_3_expand_relu',   # 56x56
        'block_6_expand_relu',   # 28x28
        'block_13_expand_relu',  # 14x14
    ]
    skip_outputs = [base.get_layer(n).output for n in skip_names]
    bottleneck = base.get_layer('block_16_project').output   # 7x7
    encoder = keras.Model(inputs=base.input, outputs=skip_outputs + [bottleneck], name='mnv2_encoder')
    return encoder


def decoder_block(x, skip, filters, name):
    x = layers.Conv2DTranspose(filters, 3, strides=2, padding='same', name=f'{name}_upconv')(x)
    x = layers.Concatenate(name=f'{name}_concat')([x, skip])
    x = layers.Conv2D(filters, 3, padding='same', activation='relu', name=f'{name}_conv1')(x)
    x = layers.BatchNormalization(name=f'{name}_bn1')(x)
    x = layers.Conv2D(filters, 3, padding='same', activation='relu', name=f'{name}_conv2')(x)
    x = layers.BatchNormalization(name=f'{name}_bn2')(x)
    return x


def build_pattern_segmentation_model(input_shape=(224, 224, 3), encoder_trainable=False, backbone_weights=None):
    encoder = build_unet_encoder(input_shape, backbone_weights=backbone_weights)
    encoder.trainable = encoder_trainable

    inputs = keras.Input(shape=input_shape)
    s1, s2, s3, s4, bottleneck = encoder(inputs)

    x = decoder_block(bottleneck, s4, 256, 'dec4')   # 7  -> 14
    x = decoder_block(x,          s3, 128, 'dec3')   # 14 -> 28
    x = decoder_block(x,          s2, 64,  'dec2')   # 28 -> 56
    x = decoder_block(x,          s1, 32,  'dec1')   # 56 -> 112

    x = layers.Conv2DTranspose(16, 3, strides=2, padding='same', activation='relu')(x)  # 112 -> 224
    x = layers.Conv2D(16, 3, padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)

    outputs = layers.Conv2D(1, 1, activation='sigmoid', dtype='float32', name='pixel_mask')(x)

    model = keras.Model(inputs, outputs, name='PatternSegmentationUNet')
    return model, encoder


# ============================================================
# TRANSFORMER WRAPPER (was pattern_transformer.py)
# ============================================================

class ModelWeightsNotLoadedError(RuntimeError):
    """Raised when the pattern model loaded but its weights are clearly not the trained weights."""
    pass


class PatternTransformer:
    """
    Wrapper for Model 3: Pattern Segmentation U-Net.

    weights_path must point at models/pattern_model_weights.npz, NOT a .keras file.
    """

    _FLATNESS_STD_THRESHOLD = 0.02

    def __init__(self, weights_path, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.input_size = tuple(self.config['input_size'])

        print("  Building architecture (model_pattern.py)...")
        self.model, _ = build_pattern_segmentation_model(
            input_shape=(*self.input_size, 3),
            encoder_trainable=False,
            backbone_weights=None,
        )

        print(f"  Loading weights (pure NumPy, Keras-version-agnostic) from: {weights_path}")
        if not os.path.exists(weights_path):
            raise FileNotFoundError(
                f"{weights_path} not found. Place pattern_model_weights.npz in models/."
            )
        load_layer_weights_into(self.model, weights_path, strict=True)

        self._verify_weights_are_real()

    def _verify_weights_are_real(self):
        h, w = self.input_size

        rng = np.random.RandomState(42)
        img_a = rng.uniform(0, 1, size=(1, h, w, 3)).astype(np.float32)
        img_b = np.zeros((1, h, w, 3), dtype=np.float32)
        img_b[:, : h // 2, :, 0] = 1.0
        img_b[:, h // 2:, :, 2] = 1.0

        try:
            out_a = self.model.predict(img_a, verbose=0)[0]
            out_b = self.model.predict(img_b, verbose=0)[0]
        except Exception as e:
            raise ModelWeightsNotLoadedError(
                f"Pattern model loaded but failed to run a test prediction: {e}"
            ) from e

        std_a = float(np.std(out_a))
        std_b = float(np.std(out_b))
        diff_ab = float(np.mean(np.abs(out_a - out_b)))

        if std_a < self._FLATNESS_STD_THRESHOLD and std_b < self._FLATNESS_STD_THRESHOLD:
            raise ModelWeightsNotLoadedError(
                f"Pattern model output is suspiciously flat/uniform for two very different "
                f"test inputs (output std: {std_a:.4f} and {std_b:.4f})."
            )

        if diff_ab < self._FLATNESS_STD_THRESHOLD:
            raise ModelWeightsNotLoadedError(
                "Pattern model produced nearly identical output for two very different "
                "test inputs - the model does not appear to be responding to the input."
            )

        print(f"  \u2705 Weight sanity check passed (output std: {std_a:.4f}/{std_b:.4f}, "
              f"input-sensitivity: {diff_ab:.4f}).")

    def predict(self, input_tensor):
        """input_tensor: (1, H, W, 3) float32 in [0,1]. Returns raw (1, H, W, 1) sigmoid output."""
        return self.model.predict(input_tensor, verbose=0)