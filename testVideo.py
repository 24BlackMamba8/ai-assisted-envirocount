

import cv2
import imutils
from sensors.dht_temp_humidity import read_temp_humidity
from sensors.light_bh1750 import read_light_intensity
from sensors.distance_sensor import read_distance_cm  # שים לב לשם הפונקציה

hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

def add_sensor_text(frame, temp, humidity, light, distance, people_count):
    text = f"אנשים: {people_count} | טמפ': {temp:.1f}C | לחות: {humidity:.1f}% | אור: {light:.0f}lx | מרחק: {distance:.1f}cm"
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    return frame

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("⚠️ לא ניתן לפתוח מצלמה")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ לא נקלט פריים מהמצלמה")
                break

            frame = imutils.resize(frame, width=500)
            (regions, _) = hog.detectMultiScale(frame, winStride=(4,4), padding=(4,4), scale=1.05)
            people_count = len(regions)

            temp, humidity = read_temp_humidity()
            light = read_light_intensity()
            distance = read_distance_cm()  # שימוש בפונקציה הנכונה

            frame = add_sensor_text(frame, temp, humidity, light, distance, people_count)

            for (x, y, w, h) in regions:
                cv2.rectangle(frame, (x,y), (x+w, y+h), (0,0,255), 2)

            cv2.imshow('EnviroCount - Test Video', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("🛑 עצירה ע\"י המשתמש")

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
