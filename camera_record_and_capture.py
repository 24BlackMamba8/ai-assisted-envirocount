

import cv2
import time
import os
from datetime import datetime

# הגדרת נתיב שמירה
capture_dir = "data/captures"
os.makedirs(capture_dir, exist_ok=True)  # צור את התיקייה אם לא קיימת

# פתח את מצלמת ה־USB
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ לא מצליח לפתוח מצלמה")
    exit()

# הגדרות וידאו
frame_width = int(cap.get(3))  # רוחב
frame_height = int(cap.get(4)) # גובה
fps = 20.0
video_filename = os.path.join(capture_dir, "output.avi")

# מקודד וידאו
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(video_filename, fourcc, fps, (frame_width, frame_height))

# צילום snapshot ראשוני
ret, snapshot = cap.read()
if ret:
    snapshot_path = os.path.join(capture_dir, "snapshot.jpg")
    cv2.imwrite(snapshot_path, snapshot)
    print(f"📸 Snapshot נשמר: {snapshot_path}")

# הגדרת טיימר לתמונה כל 5 שניות
start_time = time.time()

print("🎥 מקליט וידאו. לחץ על q ליציאה...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ שגיאה בקבלת פריים")
        break

    out.write(frame)  # כתיבה לקובץ הווידאו
    cv2.imshow("USB Camera Feed", frame)

    # שמור תמונה כל 5 שניות
    elapsed_time = time.time() - start_time
    if elapsed_time > 5:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(capture_dir, f"frame_{timestamp}.jpg")
        cv2.imwrite(image_path, frame)
        print(f"🖼️ תמונה נשמרה: {image_path}")
        start_time = time.time()

    # יציאה בלחיצת 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("🛑 יציאה מהתוכנית")
        break

# ניקוי משאבים
cap.release()
out.release()
cv2.destroyAllWindows()

