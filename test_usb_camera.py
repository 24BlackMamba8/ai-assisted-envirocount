

import cv2

# פתח את מצלמת USB (נסה גם 1 אם לא עובד)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ לא מצליח לפתוח מצלמה")
    exit()

print("✅ מצלמה נפתחה בהצלחה. ליציאה לחץ q")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ לא התקבלה תמונה")
        break

    cv2.imshow("USB Camera Feed", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
