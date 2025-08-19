

import cv2

cap = cv2.VideoCapture('/dev/video0')  # השתמש במצלמה הנכונה
if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

print("✅ Camera opened successfully")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Can't receive frame (stream end?). Exiting ...")
        break

    cv2.imshow('frame', frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
