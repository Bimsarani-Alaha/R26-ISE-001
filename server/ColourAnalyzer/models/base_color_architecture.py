"""
Standalone, version-agnostic architecture for Model 1a (base 10-colour CNN).
Import build_base_color_model() to get a freshly-initialised model with the
exact same architecture as the trained model, then load
base_color_model_weights.npz into it. Works on any TensorFlow/Keras version
(2.x or 3.x) because it never deserialises a saved model graph -- it only
rebuilds from code and loads raw weight arrays.
"""
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2


def build_base_color_model(num_classes, img_size=(224, 224), backbone_weights=None):
    base_model = MobileNetV2(input_shape=img_size + (3,), include_top=False, weights=backbone_weights)
    base_model.trainable = False

    inputs = layers.Input(shape=img_size + (3,))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs, name="BaseColorClassifier")
    return model, base_model
