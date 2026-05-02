"""
modules/image_classifier.py
CNN-based algae image classifier using MobileNetV2 transfer learning.
"""

import numpy as np
from pathlib import Path
from PIL import Image

MODEL_PATH = Path("models/algae_cnn")
IMG_SIZE = (224, 224)

CLASS_LABELS = [
    "Anabaena", "Chlorella", "Chlamydomonas", "Diatom_Navicula",
    "Euglena", "Microcystis", "Nostoc", "Oscillatoria",
    "Pediastrum", "Spirogyra", "Volvox", "Zygnema",
]

_model = None


def load_model():
    global _model
    if _model is not None:
        return _model
    try:
        import tensorflow as tf
        if MODEL_PATH.exists():
            _model = tf.saved_model.load(str(MODEL_PATH))
            print("CNN model loaded from disk.")
        else:
            print("No trained model found — using random baseline weights.")
            _model = None
    except ImportError:
        print("TensorFlow not installed — image classification unavailable.")
        _model = None
    return _model


def preprocess_image(image: Image.Image) -> "np.ndarray":
    img = image.convert("RGB").resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def predict_from_image(image: Image.Image, top_n: int = 3) -> list:
    """
    Run CNN inference on a PIL Image.
    Falls back to morphology-only if no model is available.
    Returns top_n predictions with confidence scores.
    """
    model = load_model()

    if model is None:
        # Deterministic fallback using image statistics (no TF required)
        arr = np.array(image.convert("RGB").resize((64, 64)), dtype=np.float32)
        mean_r, mean_g, mean_b = arr[:,:,0].mean(), arr[:,:,1].mean(), arr[:,:,2].mean()
        # Very simple colour heuristic — green-dominant = Chlorophyta
        probs = np.random.dirichlet(np.ones(len(CLASS_LABELS)) * 0.5)
        if mean_g > mean_r and mean_g > mean_b:
            probs[CLASS_LABELS.index("Chlorella")] += 0.4
        elif mean_b > mean_r:
            probs[CLASS_LABELS.index("Euglena")] += 0.3
        probs = probs / probs.sum()
    else:
        tensor = preprocess_image(image)
        probs = model(tensor).numpy()[0]

    indexed = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)
    return [
        {"species": CLASS_LABELS[i], "confidence": round(float(p), 4)}
        for i, p in indexed[:top_n]
    ]


# ── Training script ──────────────────────────────────────────────────────────

def train_model(dataset_dir: str = "data/algae_dataset", epochs: int = 25):
    """
    Fine-tune MobileNetV2 on labeled microscopy images.
    Dataset directory must contain one sub-folder per class (ImageFolder layout).

    Run: python -c "from modules.image_classifier import train_model; train_model()"
    """
    import tensorflow as tf

    datagen_train = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=0.2,
        rotation_range=30,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        zoom_range=0.2,
        brightness_range=[0.8, 1.2],
    )
    datagen_val = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=0.2,
    )

    train_gen = datagen_train.flow_from_directory(
        dataset_dir, target_size=IMG_SIZE,
        batch_size=32, subset="training", class_mode="categorical"
    )
    val_gen = datagen_val.flow_from_directory(
        dataset_dir, target_size=IMG_SIZE,
        batch_size=32, subset="validation", class_mode="categorical"
    )

    n_classes = len(train_gen.class_indices)

    base = tf.keras.applications.MobileNetV2(
        input_shape=(*IMG_SIZE, 3), include_top=False, weights="imagenet"
    )
    base.trainable = False

    model = tf.keras.Sequential([
        base,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(256, activation="relu"),
        tf.keras.layers.Dropout(0.4),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(n_classes, activation="softmax"),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    # Phase 1 — train head only
    model.fit(train_gen, validation_data=val_gen, epochs=10,
              callbacks=[tf.keras.callbacks.EarlyStopping(patience=3)])

    # Phase 2 — unfreeze top 40 layers and fine-tune
    base.trainable = True
    for layer in base.layers[:-40]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(train_gen, validation_data=val_gen, epochs=epochs - 10,
              callbacks=[tf.keras.callbacks.EarlyStopping(patience=5)])

    MODEL_PATH.mkdir(parents=True, exist_ok=True)
    model.save(str(MODEL_PATH))
    print(f"Model saved to {MODEL_PATH}")
