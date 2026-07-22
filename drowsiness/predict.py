"""
predict.py
----------
Single source of truth for loading the trained model and running inference
on a frame / image. Imported by app.py so the Flask routes stay thin.
"""

import os
import json

import numpy as np
import cv2
import tensorflow as tf

IMG_SIZE = 227

MODEL_PATH = os.path.join("models", "drowsiness_cnn.h5")
LABELS_PATH = os.path.join("models", "labels.json")
RISK_MAP_PATH = os.path.join("models", "risk_map.json")

# Haar cascade shipped with OpenCV -- used only to draw a bounding box around
# the driver's face for the UI overlay. Classification itself runs on the
# full frame (or the cropped face if one is found), not on the box alone.
_FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


class DrowsinessDetector:
    def __init__(self, model_path=MODEL_PATH, labels_path=LABELS_PATH,
                 risk_map_path=RISK_MAP_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. Run train.py first, or "
                f"place a trained drowsiness_cnn.h5 in the models/ folder."
            )
        self.model = tf.keras.models.load_model(model_path)

        with open(labels_path) as f:
            self.classes = json.load(f)  # full 9-class list the model outputs

        # The app only ever surfaces two states: Drowsy / Non-Drowsy. Those
        # were also the two classes with by far the most training data
        # (~22k / ~19k images vs. hundreds-to-low-thousands for the rest),
        # so they're the classes the model is actually reliable on. We keep
        # the full 9-way softmax internally (the model's output layer still
        # has 9 units) but only ever read these two indices back out.
        if "Drowsy" not in self.classes or "Non-Drowsy" not in self.classes:
            raise ValueError("labels.json must contain 'Drowsy' and 'Non-Drowsy'.")
        self.drowsy_idx = self.classes.index("Drowsy")
        self.non_drowsy_idx = self.classes.index("Non-Drowsy")

        # Final display risk map -- intentionally overrides whatever
        # risk_map.json contains, since the app only ever emits these three
        # labels now.
        self.risk_map = {
            "Drowsy": "danger",
            "Non-Drowsy": "safe",
            "No Face Detected": "warning",
        }

    def _preprocess(self, bgr_image):
        rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (IMG_SIZE, IMG_SIZE))
        arr = resized.astype("float32")
        return np.expand_dims(arr, axis=0)  # model has its own Rescaling layer

    def detect_face(self, bgr_frame):
        """Returns (x, y, w, h) of the largest detected face, or None."""
        gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
        faces = _FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1,
                                                minNeighbors=5, minSize=(60, 60))
        if len(faces) == 0:
            return None
        # largest face = most likely the driver
        return max(faces, key=lambda f: f[2] * f[3])

    def _crop_face(self, bgr_frame, face_box, pad_ratio=0.35):
        """Crops to the face box with extra padding, since the training
        images (DDD dataset) are tight face/eye close-ups, not full-body
        webcam frames. Classifying the raw uncropped frame is a domain
        mismatch that tanks live accuracy even for an otherwise-good model."""
        h_frame, w_frame = bgr_frame.shape[:2]
        x, y, w, h = face_box
        pad_x, pad_y = int(w * pad_ratio), int(h * pad_ratio)
        x0 = max(0, x - pad_x)
        y0 = max(0, y - pad_y)
        x1 = min(w_frame, x + w + pad_x)
        y1 = min(h_frame, y + h + pad_y)
        crop = bgr_frame[y0:y1, x0:x1]
        if crop.size == 0:
            return bgr_frame
        return crop

    def predict(self, bgr_frame):
        """Runs the classifier on a single BGR frame (as returned by cv2).

        Returns a dict:
            {
              "label": "Drowsy" | "Non-Drowsy" | "No Face Detected",
              "confidence": float,       # 0-1
              "risk": "safe"|"warning"|"danger",
              "face_box": [x, y, w, h] | None,
              "no_face": bool,           # True only for the no-face case
              "probs": {"Drowsy": p, "Non-Drowsy": p}
            }
        """
        face_box = self.detect_face(bgr_frame)

        # No face -> don't classify at all. Running the model on a random
        # full-frame image (background, dashboard, an empty room) is exactly
        # what produced nonsense, overconfident predictions before -- there
        # is nothing driver-related for the model to actually read.
        if face_box is None:
            return {
                "label": "No Face Detected",
                "confidence": 0.0,
                "risk": "warning",
                "face_box": None,
                "no_face": True,
                "probs": {},
            }

        region = self._crop_face(bgr_frame, face_box)
        batch = self._preprocess(region)
        preds = self.model.predict(batch, verbose=0)[0]

        # Renormalize over just the two classes we actually surface, so the
        # other 7 (Yawn, Distracted, Drinking, etc.) never leak into the
        # decision or dilute the confidence score.
        p_drowsy = float(preds[self.drowsy_idx])
        p_non_drowsy = float(preds[self.non_drowsy_idx])
        total = p_drowsy + p_non_drowsy
        if total <= 0:
            p_drowsy, p_non_drowsy = 0.5, 0.5
        else:
            p_drowsy, p_non_drowsy = p_drowsy / total, p_non_drowsy / total

        if p_drowsy >= p_non_drowsy:
            label, confidence = "Drowsy", p_drowsy
        else:
            label, confidence = "Non-Drowsy", p_non_drowsy

        return {
            "label": label,
            "confidence": confidence,
            "risk": self.risk_map[label],
            "face_box": [int(v) for v in face_box],
            "no_face": False,
            "probs": {"Drowsy": p_drowsy, "Non-Drowsy": p_non_drowsy},
        }


# Lazily-instantiated singleton so app.py can `from predict import get_detector`
_detector_instance = None


def get_detector():
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = DrowsinessDetector()
    return _detector_instance
