"""
app.py
------
Flask web app for the Driver Drowsiness Detection system.

Routes
------
GET  /                  landing page
GET  /upload            upload form
POST /upload            handle uploaded video, run frame-by-frame detection,
                         return an annotated results page
GET  /live               live webcam viewer page (browser captures frames)
POST /predict_frame      receives a single base64 JPEG frame from the browser,
                         returns JSON prediction + face box (used for both
                         the live page and can be reused for custom clients)
GET  /outputs/<filename> serves generated annotated videos / clips

Live webcam detection runs client-side (getUserMedia) and streams frames to
the server for inference -- this works for any deployment target (including
servers with no physical camera attached), unlike server-side cv2.VideoCapture.
"""

import os
import io
import json
import base64
import time
import uuid

import cv2
import numpy as np
from flask import (Flask, render_template, request, redirect, url_for,
                    jsonify, flash, send_from_directory)
from werkzeug.utils import secure_filename

from predict import get_detector

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
ALLOWED_VIDEO_EXT = {"mp4", "avi", "mov", "mkv", "webm"}
MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


@app.context_processor
def inject_globals():
    return {"model_loaded": os.path.exists(os.path.join("models", "drowsiness_cnn.h5"))}

# Colors (BGR) per risk bucket, used for both drawn boxes and JSON responses
RISK_COLORS = {
    "safe": (46, 204, 113),      # green
    "warning": (0, 165, 255),    # orange
    "danger": (60, 60, 231),     # red
}

# How many consecutive "danger" frames (video) / seconds (live) before the
# alarm flag is raised, to avoid false positives from a single bad frame.
DANGER_STREAK_THRESHOLD = 5
FRAME_SAMPLE_STRIDE = 5  # analyze every Nth frame of an uploaded video


def allowed_video(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXT


@app.route("/")
def index():
    return render_template("index.html", active="home")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("upload.html", result=None, active="upload")

    if "video" not in request.files:
        flash("No file part in the request.")
        return redirect(url_for("upload"))

    file = request.files["video"]
    if file.filename == "":
        flash("No file selected.")
        return redirect(url_for("upload"))

    if not allowed_video(file.filename):
        flash("Unsupported file type. Please upload mp4, avi, mov, mkv or webm.")
        return redirect(url_for("upload"))

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    in_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file.save(in_path)

    try:
        result = process_video(in_path, unique_name)
    except Exception as exc:
        flash(f"Error processing video: {exc}")
        return redirect(url_for("upload"))
    finally:
        # keep the uploaded source only as long as needed for debugging;
        # comment this out if you want to retain originals
        pass

    return render_template("upload.html", result=result, active="upload")


def process_video(in_path, unique_name):
    """Runs detection every FRAME_SAMPLE_STRIDE frames, writes an annotated
    output video, and returns a summary dict for the results page."""
    detector = get_detector()

    cap = cv2.VideoCapture(in_path)
    if not cap.isOpened():
        raise RuntimeError("Could not open uploaded video file.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    out_name = f"annotated_{unique_name.rsplit('.', 1)[0]}.mp4"
    out_path = os.path.join(OUTPUT_FOLDER, out_name)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    class_counts = {}
    danger_streak = 0
    max_danger_streak = 0
    alarm_events = []  # list of {time_sec, label, confidence}
    frame_idx = 0
    last_result = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % FRAME_SAMPLE_STRIDE == 0:
            last_result = detector.predict(frame)
            class_counts[last_result["label"]] = class_counts.get(last_result["label"], 0) + 1

            if last_result["risk"] == "danger":
                danger_streak += 1
                max_danger_streak = max(max_danger_streak, danger_streak)
                if danger_streak == DANGER_STREAK_THRESHOLD:
                    alarm_events.append({
                        "time_sec": round(frame_idx / fps, 1),
                        "label": last_result["label"],
                        "confidence": round(last_result["confidence"], 3),
                    })
            else:
                danger_streak = 0

        annotated = draw_overlay(frame, last_result) if last_result else frame
        writer.write(annotated)
        frame_idx += 1

    cap.release()
    writer.release()

    total_analyzed = sum(class_counts.values()) or 1
    distribution = {
        cls: round(100 * count / total_analyzed, 1)
        for cls, count in sorted(class_counts.items(), key=lambda kv: -kv[1])
    }

    overall_risk = "safe"
    if any(detector.risk_map.get(c) == "danger" for c in class_counts):
        overall_risk = "danger" if max_danger_streak >= DANGER_STREAK_THRESHOLD else "warning"
    elif any(detector.risk_map.get(c) == "warning" for c in class_counts):
        overall_risk = "warning"

    return {
        "video_url": url_for("serve_output", filename=out_name),
        "duration_sec": round(total_frames / fps, 1) if fps else None,
        "distribution": distribution,
        "alarm_events": alarm_events,
        "overall_risk": overall_risk,
        "frames_analyzed": total_analyzed,
    }


def draw_overlay(frame, result):
    frame = frame.copy()
    # No face detected renders in red (RISK_COLORS["danger"]) even though its
    # risk value is "warning" -- it's a distinct, more urgent visual state:
    # we can't verify the driver's state at all versus a known warning class.
    color = RISK_COLORS["danger"] if result.get("no_face") else RISK_COLORS.get(result["risk"], (255, 255, 255))
    box = result.get("face_box")
    if box:
        x, y, w, h = box
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        label_y = max(y - 12, 20)
    else:
        label_y = 30

    text = f"{result['label']} ({result['confidence']*100:.1f}%)"
    cv2.putText(frame, text, (20, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    return frame


@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)


@app.route("/live")
def live():
    return render_template("live.html", active="live")


@app.route("/predict_frame", methods=["POST"])
def predict_frame():
    """Accepts JSON: { "image": "data:image/jpeg;base64,..." }
    Returns JSON: { label, confidence, risk, face_box, color }"""
    data = request.get_json(silent=True)
    if not data or "image" not in data:
        return jsonify({"error": "Missing 'image' field."}), 400

    try:
        header, encoded = data["image"].split(",", 1) if "," in data["image"] else (None, data["image"])
        img_bytes = base64.b64decode(encoded)
        np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Could not decode image.")
    except Exception as exc:
        return jsonify({"error": f"Invalid image payload: {exc}"}), 400

    try:
        detector = get_detector()
        result = detector.predict(frame)
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503

    return jsonify({
        "label": result["label"],
        "confidence": round(result["confidence"], 4),
        "risk": result["risk"],
        "face_box": result["face_box"],
        "no_face": result.get("no_face", False),
        "alarm": result["risk"] == "danger",
    })


@app.errorhandler(413)
def too_large(e):
    flash("File too large. Maximum upload size is 200 MB.")
    return redirect(url_for("upload"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
