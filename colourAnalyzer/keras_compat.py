
import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
 
import tensorflow as tf
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
        # 'optional' has no equivalent in older Keras and is not needed to
        # restore a trained model's structure or weights - safe to drop.
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
 
    Args:
        model_path: path to the .keras file.
        custom_objects: any additional custom objects (losses, metrics,
            custom layers) the caller already needs - these are preserved
            and merged with the InputLayer patch, never overwritten.
        compile: passed straight through to keras.models.load_model().
 
    Returns:
        The restored keras.Model, exactly as keras.models.load_model()
        would return it once the version-mismatch parsing issue is out
        of the way. Any OTHER kind of load failure (truly corrupted file,
        genuinely incompatible architecture, etc.) still raises normally -
        this shim only fixes the InputLayer batch_shape/optional issue.
    """
    merged_custom_objects = {'InputLayer': CompatInputLayer}
    if custom_objects:
        merged_custom_objects.update(custom_objects)
 
    return keras.models.load_model(
        model_path,
        custom_objects=merged_custom_objects,
        compile=compile,
    )
 