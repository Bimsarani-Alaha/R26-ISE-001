from tensorflow.keras import layers, models


def build_color_name_model(num_classes):
    return models.Sequential([
        layers.Input(shape=(3,)),
        layers.Dense(256, activation="relu"),
        layers.Dense(256, activation="relu"),
        layers.Dense(128, activation="relu"),
        layers.Dense(num_classes, activation="softmax"),
    ], name="ColourNameClassifier")
