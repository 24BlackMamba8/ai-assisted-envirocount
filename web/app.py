

import sys
import os
import time
import cv2
import zipfile
import io
import numpy as np
from flask import Flask, send_file, send_from_directory, render_template, Response, jsonify
import atexit
from datetime import datetime

# נתיב יחסי לפרויקט
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sensors.distance_sensor import read_distance, setup_ultrasonic, cleanup_ultrasonic

# אתחול חיישן
setup_ultrasonic()
atexit.register(cleanup_ultrasonic)

app = Flask(__name__)
VIDEO_SRC = 0
CONF_THRESHOLD = 0.4
FRAME = None

# משתני הקלטה
is_recording = False
video_writer = None
video_filename = None
no_person_frames = 0
NO_PERSON_THRESHOLD = 50  # כמות פריימים רצופים ללא אנשים (~2.5 שניות)
cap = cv2.VideoCapture(VIDEO_SRC)

if not cap.isOpened():
    raise RuntimeError("❌ Cannot open camera!")

# טעינת מודל MobileNetSSD
prototxt_path = os.path.join(os.path.dirname(__file__), '..', 'MobileNetSSD_deploy.prototxt')
model_path = os.path.join(os.path.dirname(__file__), '..', 'MobileNetSSD_deploy.caffemodel')

if not os.path.exists(prototxt_path) or not os.path.exists(model_path):
    raise FileNotFoundError("❌ חסרים קבצי המודל!")

net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)

CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant",
           "sheep", "sofa", "train", "tvmonitor"]

people_count = 0
last_distance = 0
last_read_time = time.time()

def estimate_distance_from_box(box_height, frame_height, base_distance):
    if box_height <= 0:
        return base_distance
    relative_height = box_height / frame_height
    estimated_distance = base_distance / relative_height
    return round(estimated_distance, 1)

def generate_frames():
    global people_count, last_distance, last_read_time, FRAME, is_recording, video_writer, video_filename
    global no_person_frames

    while True:
        success, frame = cap.read()
        if not success:
            continue

        FRAME = frame.copy()
        (h, w) = frame.shape[:2]

        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
                                     0.007843, (300, 300), 127.5)
        net.setInput(blob)
        detections = net.forward()
        people_count = 0

        # קריאת חיישן כל שנייה
        if time.time() - last_read_time > 1:
            dist = read_distance()
            if dist is not None:
                last_distance = dist
            last_read_time = time.time()

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > CONF_THRESHOLD:
                idx = int(detections[0, 0, i, 1])
                if CLASSES[idx] == "person":
                    people_count += 1
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")

                    cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                    cv2.putText(frame, f"Person {people_count}", (startX, startY - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    estimated_distance = estimate_distance_from_box(endY - startY, h, last_distance)
                    cv2.putText(frame, f"Dist: {estimated_distance} cm",
                                (startX + 5, startY + 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # טקסט למעלה עם ספירת אנשים
        cv2.putText(frame, f"Person_count : {people_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # --- לוגיקה להקלטה אוטומטית לפי זיהוי אנשים ---

        if people_count > 0:
            no_person_frames = 0
            if not is_recording:
                save_dir = os.path.join(os.path.dirname(__file__), '..', 'sensors', 'captures')
                os.makedirs(save_dir, exist_ok=True)
                video_filename = f"auto_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
                video_path = os.path.join(save_dir, video_filename)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, (width, height))
                is_recording = True
                print(f"הקלטה אוטומטית התחילה: {video_filename}")
        else:
            no_person_frames += 1
            if is_recording and no_person_frames >= NO_PERSON_THRESHOLD:
                is_recording = False
                no_person_frames = 0
                if video_writer:
                    video_writer.release()
                    video_writer = None
                print("הקלטה אוטומטית נעצרה בגלל חוסר אנשים")

        if is_recording and video_writer is not None:
            video_writer.write(frame)

        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/sensor_data')
def sensor_data():
    return jsonify({"distance": last_distance, "people_count": people_count})

@app.route('/toggle_recording', methods=['POST'])
def toggle_recording():
    global is_recording, video_writer, video_filename
    save_dir = os.path.join(os.path.dirname(__file__), '..', 'sensors', 'captures')
    os.makedirs(save_dir, exist_ok=True)

    if not is_recording:
        video_filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
        video_path = os.path.join(save_dir, video_filename)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, (width, height))
        is_recording = True
        return jsonify({"status": "started", "message": f"הקלטה התחילה ({video_filename})"})
    else:
        is_recording = False
        if video_writer:
            video_writer.release()
            video_writer = None
        return jsonify({"status": "stopped", "message": f"הקלטה הסתיימה ({video_filename})"})

@app.route('/save_frame', methods=['POST'])
def save_frame():
    global FRAME
    if FRAME is None:
        return jsonify({"status": "error", "message": "אין פריים לשמור"}), 400

    save_dir = os.path.join(os.path.dirname(__file__), '..', 'sensors', 'captures')
    os.makedirs(save_dir, exist_ok=True)
    filename = f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    save_path = os.path.join(save_dir, filename)
    cv2.imwrite(save_path, FRAME)
    return jsonify({"status": "success", "message": f"תמונה נשמרה ב-{save_path}"})

@app.route('/list_captures')
def list_captures():
    captures_dir = os.path.join(os.path.dirname(__file__), '..', 'sensors', 'captures')
    os.makedirs(captures_dir, exist_ok=True)
    files = [f for f in os.listdir(captures_dir) if f.endswith(('.jpg', '.avi'))]
    return jsonify({"files": files})

@app.route('/delete_capture/<filename>', methods=['DELETE'])
def delete_capture(filename):
    captures_dir = os.path.join(os.path.dirname(__file__), '..', 'sensors', 'captures')
    file_path = os.path.join(captures_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"status": "success", "message": f"{filename} נמחק"})
    return jsonify({"status": "error", "message": "קובץ לא נמצא"}), 404

@app.route('/download/<filename>')
def download_capture(filename):
    captures_dir = os.path.join(os.path.dirname(__file__), '..', 'sensors', 'captures')
    return send_from_directory(captures_dir, filename, as_attachment=True)

@app.route('/download_all')
def download_all():
    captures_dir = os.path.join(os.path.dirname(__file__), '..', 'sensors', 'captures')
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        for file_name in os.listdir(captures_dir):
            file_path = os.path.join(captures_dir, file_name)
            if os.path.isfile(file_path):
                zipf.write(file_path, file_name)
    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip',
                     as_attachment=True, download_name='captures.zip')

@atexit.register
def cleanup():
    global video_writer
    if cap:
        cap.release()
    if video_writer:
        video_writer.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
