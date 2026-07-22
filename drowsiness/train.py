"""
train.py
--------
Trains a single multi-class CNN on the union of two Kaggle datasets:

  Dataset 1 - Driver Drowsiness Dataset (DDD)
      dataset/DDD/Drowsy/*.png
      dataset/DDD/Non Drowsy/*.png        (folder name may also be "Non-Drowsy")

  Dataset 2 - Thesis_dataset2
      dataset/Thesis_dataset2/DangerousDriving/*
      dataset/Thesis_dataset2/Distracted/*
      dataset/Thesis_dataset2/Drinking/*
      dataset/Thesis_dataset2/Openeye/*
      dataset/Thesis_dataset2/SafeDriving/*
      dataset/Thesis_dataset2/Yawn/*
      dataset/Thesis_dataset2/closed/*

Rather than training two separate models, this script builds ONE combined
directory (dataset/combined/<class_name>/...) using symlinks (falls back to
copies on filesystems without symlink support, e.g. some Windows setups),
so a single `flow_from_directory` / `image_dataset_from_directory` call
sees all 9 classes at once. This keeps the Flask app simple: one model,
one predict() call, one softmax output.

Run:
    python train.py --ddd_dir dataset/DDD --thesis_dir dataset/Thesis_dataset2

Outputs:
    models/drowsiness_cnn.h5
    models/labels.json           (class list, in the exact order used by the model)
    models/risk_map.json         (class -> risk level, used for alerting)
    models/training_history.png
"""

import os
import json
import shutil
import argparse

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks
import matplotlib.pyplot as plt

IMG_SIZE = 227
BATCH_SIZE = 32
SEED = 42

# Final unified class list. Order matters -- this exact order is written to
# models/labels.json and must never be re-sorted after training.
CLASSES = [
    "DangerousDriving",
    "Distracted",
    "Drinking",
    "Drowsy",
    "Non-Drowsy",
    "Openeye",
    "SafeDriving",
    "Yawn",
    "closed",
]

# Risk bucket used by the Flask app to decide alert color / alarm sound.
# safe = green, warning = orange, danger = red (alarm fires)
RISK_MAP = {
    "SafeDriving": "safe",
    "Openeye": "safe",
    "Non-Drowsy": "safe",
    "Distracted": "warning",
    "Drinking": "warning",
    "Yawn": "warning",
    "DangerousDriving": "danger",
    "Drowsy": "danger",
    "closed": "danger",
}

DDD_FOLDER_ALIASES = {
    "Drowsy": ["Drowsy", "drowsy"],
    "Non-Drowsy": ["Non Drowsy", "Non-Drowsy", "NonDrowsy", "non_drowsy", "Non_drowsy"],
}


def _link_or_copy(src, dst):
    if os.path.exists(dst):
        return
    try:
        os.symlink(os.path.abspath(src), dst)
    except (OSError, NotImplementedError):
        shutil.copytree(src, dst)


def build_combined_dataset(ddd_dir, thesis_dir, combined_dir="dataset/combined"):
    """Create dataset/combined/<class>/ as symlinks into the two source dirs."""
    os.makedirs(combined_dir, exist_ok=True)

    # --- Dataset 2 (Thesis_dataset2): folder names already match class names
    thesis_classes = ["DangerousDriving", "Distracted", "Drinking", "Openeye",
                       "SafeDriving", "Yawn", "closed"]
    for cls in thesis_classes:
        src = os.path.join(thesis_dir, cls)
        dst = os.path.join(combined_dir, cls)
        if os.path.isdir(src):
            _link_or_copy(src, dst)
        else:
            print(f"[warn] missing folder for class '{cls}': {src}")

    # --- Dataset 1 (DDD): handle naming variations
    for cls, aliases in DDD_FOLDER_ALIASES.items():
        found = None
        for alias in aliases:
            candidate = os.path.join(ddd_dir, alias)
            if os.path.isdir(candidate):
                found = candidate
                break
        if found:
            _link_or_copy(found, os.path.join(combined_dir, cls))
        else:
            print(f"[warn] missing folder for class '{cls}' under {ddd_dir}")

    print(f"Combined dataset built at: {combined_dir}")
    missing = []
    for cls in CLASSES:
        p = os.path.join(combined_dir, cls)
        n = len(os.listdir(p)) if os.path.isdir(p) else 0
        print(f"  {cls:<18s}: {n} images")
        if n == 0:
            missing.append(cls)

    if missing:
        raise RuntimeError(
            f"These classes have ZERO images: {missing}. Fix --ddd_dir / "
            f"--thesis_dir (or the folder names under them) before training "
            f"-- otherwise the model silently learns nothing about these "
            f"classes and will never predict them correctly."
        )
    return combined_dir


def build_model(num_classes=len(CLASSES), img_size=IMG_SIZE):
    """Compact CNN sized for 227x227 RGB input. No pretrained weights are
    used so the whole pipeline is self-contained and reproducible offline."""
    inputs = layers.Input(shape=(img_size, img_size, 3))
    x = layers.Rescaling(1.0 / 255)(inputs)

    x = layers.Conv2D(32, 3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.Conv2D(64, 3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.Conv2D(128, 3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.Conv2D(256, 3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs, name="driver_drowsiness_cnn")
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def get_generators(combined_dir, img_size=IMG_SIZE, batch_size=BATCH_SIZE):
    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=None,  # rescaling is baked into the model via layers.Rescaling
        rotation_range=12,
        width_shift_range=0.08,
        height_shift_range=0.08,
        zoom_range=0.1,
        brightness_range=(0.8, 1.2),
        horizontal_flip=True,
        validation_split=0.2,
    )
    train_gen = train_datagen.flow_from_directory(
        combined_dir,
        target_size=(img_size, img_size),
        batch_size=batch_size,
        classes=CLASSES,
        class_mode="categorical",
        subset="training",
        seed=SEED,
    )
    val_gen = train_datagen.flow_from_directory(
        combined_dir,
        target_size=(img_size, img_size),
        batch_size=batch_size,
        classes=CLASSES,
        class_mode="categorical",
        subset="validation",
        seed=SEED,
    )
    return train_gen, val_gen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ddd_dir", default="dataset/DDD")
    parser.add_argument("--thesis_dir", default="dataset/Thesis_dataset2")
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--out_dir", default="models")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    combined_dir = build_combined_dataset(args.ddd_dir, args.thesis_dir)
    train_gen, val_gen = get_generators(combined_dir)

    model = build_model()
    model.summary()

    # class_weight: with 9 classes of very different sizes, unweighted
    # training biases hard toward the largest classes (this is exactly what
    # produced a collapsed 2-class model in an earlier run where dataset 2
    # was missing entirely). Always weight, even if counts look balanced.
    from sklearn.utils.class_weight import compute_class_weight
    present_labels = train_gen.classes
    unique_present = np.unique(present_labels)
    weights = compute_class_weight(class_weight="balanced", classes=unique_present, y=present_labels)
    class_weight = {int(c): float(w) for c, w in zip(unique_present, weights)}
    print("Class weights:", class_weight)

    ckpt_path = os.path.join(args.out_dir, "drowsiness_cnn.h5")
    cbs = [
        callbacks.ModelCheckpoint(ckpt_path, monitor="val_accuracy",
                                   save_best_only=True, verbose=1),
        callbacks.EarlyStopping(monitor="val_accuracy", patience=6,
                                 restore_best_weights=True),
        callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3),
    ]

    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=args.epochs,
        callbacks=cbs,
        class_weight=class_weight,
    )

    # Save labels + risk map alongside the model so app.py / predict.py never
    # have to hardcode class order.
    with open(os.path.join(args.out_dir, "labels.json"), "w") as f:
        json.dump(CLASSES, f, indent=2)
    with open(os.path.join(args.out_dir, "risk_map.json"), "w") as f:
        json.dump(RISK_MAP, f, indent=2)

    # Plot + save training curves
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(history.history["accuracy"], label="train_acc")
    axes[0].plot(history.history["val_accuracy"], label="val_acc")
    axes[0].set_title("Accuracy")
    axes[0].legend()
    axes[1].plot(history.history["loss"], label="train_loss")
    axes[1].plot(history.history["val_loss"], label="val_loss")
    axes[1].set_title("Loss")
    axes[1].legend()
    fig.savefig(os.path.join(args.out_dir, "training_history.png"))

    print(f"\nSaved model to {ckpt_path}")
    print(f"Saved labels to {os.path.join(args.out_dir, 'labels.json')}")


if __name__ == "__main__":
    main()
