import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import numpy as np
from tensorflow import keras
from tensorflow.keras.layers import InputLayer as _RealInputLayer


class CompatInputLayer(_RealInputLayer):
    """Drop-in replacement for tf.keras.layers.InputLayer that tolerates
    the newer `batch_shape` / `optional` config keys produced by newer
    Keras versions, translating them to what this (older) installed
    Keras version's InputLayer actually accepts."""

    def __init__(self, *args, **kwargs):
        kwargs = dict(kwargs)
        if 'batch_shape' in kwargs:
            batch_shape = kwargs.pop('batch_shape')
            if batch_shape is not None and 'batch_input_shape' not in kwargs:
                kwargs['batch_input_shape'] = batch_shape
        kwargs.pop('optional', None)
        super().__init__(*args, **kwargs)

    @classmethod
    def from_config(cls, config):
        config = dict(config)
        if 'batch_shape' in config:
            batch_shape = config.pop('batch_shape')
            if batch_shape is not None and 'batch_input_shape' not in config:
                config['batch_input_shape'] = batch_shape
        config.pop('optional', None)
        return cls(**config)


def safe_load_model(model_path, custom_objects=None, compile=False):
    """
    Drop-in replacement for keras.models.load_model() that automatically
    patches InputLayer deserialization so models saved with a newer Keras
    version can still be restored correctly by this (older) installed
    Keras version.
    """
    merged_custom_objects = {'InputLayer': CompatInputLayer}
    if custom_objects:
        merged_custom_objects.update(custom_objects)

    return keras.models.load_model(
        model_path,
        custom_objects=merged_custom_objects,
        compile=compile,
    )


def export_layer_weights(model, out_path):
    """One-time export helper: dump every layer's weights to a plain
    NumPy .npz file. Not called during normal app startup -- only needed
    if you ever retrain a model and need to re-export its weights."""
    flat = {}
    n_layers_with_weights = 0

    for i, layer in enumerate(model.layers):
        weights = layer.get_weights()
        if not weights:
            continue
        n_layers_with_weights += 1
        safe_name = layer.name.replace("/", "_")
        for j, w in enumerate(weights):
            flat[f"{i:04d}__{safe_name}__w{j}"] = np.asarray(w)

    np.savez(out_path, **flat)
    print(f"[models_common] Exported {len(flat)} arrays from "
          f"{n_layers_with_weights} weighted layers -> {out_path}")


def load_layer_weights_into(model, npz_path, strict=True):
    """Restore a model's weights from a plain-NumPy .npz file produced by
    export_layer_weights(). Matches purely by layer index + shape, so it
    works on any TensorFlow/Keras version as long as the architecture code
    that built `model` is unchanged from what was exported."""
    data = np.load(npz_path)

    by_layer = {}
    for key in data.files:
        idx_str, _name, w_str = key.split("__")
        idx = int(idx_str)
        w_idx = int(w_str[1:])
        by_layer.setdefault(idx, {})[w_idx] = data[key]

    layers = model.layers
    copied = 0

    for idx, weight_map in by_layer.items():
        if idx >= len(layers):
            msg = (f"[models_common] Saved weights reference layer index {idx}, but the "
                   f"rebuilt model only has {len(layers)} layers. Architecture code "
                   f"does not match the exported model.")
            if strict:
                raise RuntimeError(msg)
            print("WARNING:", msg)
            continue

        layer = layers[idx]
        ordered = [weight_map[j] for j in sorted(weight_map)]
        current = layer.get_weights()

        if len(current) != len(ordered) or any(
            c.shape != o.shape for c, o in zip(current, ordered)
        ):
            msg = (f"[models_common] Shape mismatch at layer index {idx} "
                   f"(name='{layer.name}'). Rebuilt layer expects "
                   f"{[c.shape for c in current]}, saved weights are "
                   f"{[o.shape for o in ordered]}. Architecture code does not match "
                   f"the exported model -- refusing to load.")
            if strict:
                raise RuntimeError(msg)
            print("WARNING:", msg)
            continue

        layer.set_weights(ordered)
        copied += 1

    print(f"[models_common] Loaded weights into {copied} layers from {npz_path}")
    if copied == 0:
        raise RuntimeError(
            "[models_common] Loaded ZERO layers -- something is wrong (wrong file, "
            "wrong architecture, or empty export)."
        )
    return copied