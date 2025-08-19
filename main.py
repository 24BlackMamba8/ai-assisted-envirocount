

import time
import datetime
from firebase_admin import credentials, initialize_app, firestore, db

# ייבוא פונקציות פנימיות
from ai.people_counter import get_people_count
from sensors.light_bh1750 import read_light_intensity
from sensors.distance_sensor import setup_ultrasonic, read_distance, cleanup_ultrasonic

# ייבוא פונקציות לשליחת נתונים
from cloud.firebase_sender import send_people_to_realtime, send_environment_to_realtime

### אתחול Firebase פעם אחת
cred = credentials.Certificate("serviceAccountKey.json")
initialize_app(cred, {
    'databaseURL': 'https://ai-assisted-envirocount-default-rtdb.firebaseio.com/'
})

firestore_db = firestore.client()

### ספים להתראות
LIGHT_THRESHOLD_LOW = 100
PEOPLE_COUNT_THRESHOLD = 50

### פונקציות לשליחת נתונים
def send_people_count(count):
    firestore_db.collection('envirocount').document('people_count').set({
        'count': count,
        'timestamp': datetime.datetime.utcnow()
    })
    db.reference('peopleCount').push({
        'count': count,
        'timestamp': datetime.datetime.utcnow().isoformat()
    })

def send_environment_data(light, distance):
    firestore_db.collection('envirocount').document('environment').set({
        'light': light,
        'distance': distance,
        'timestamp': datetime.datetime.utcnow()
    })
    db.reference('envData').push({
        'light': light,
        'distance': distance,
        'timestamp': datetime.datetime.utcnow().isoformat()
    })

### זיהוי חריגות
def check_alerts(light, people_count, distance):
    alerts = []
    if light is not None and light < LIGHT_THRESHOLD_LOW:
        alerts.append(f"⚠️ רמת אור נמוכה: {light} lux")
    if people_count > PEOPLE_COUNT_THRESHOLD:
        alerts.append(f"⚠️ מספר אנשים גבוה בכניסה: {people_count}")
    if distance is not None and distance < 10:
        alerts.append(f"⚠️ מרחק נמוך מאוד: {distance} ס״מ")
    return alerts

def main_loop():
    setup_ultrasonic()  # הגדרת חיישן המרחק
    try:
        while True:
            try:
                # קריאה מהמצלמה
                people_count = get_people_count()
                print(f"🧍‍♂️ נמצאו {people_count} אנשים")

                # קריאת חיישנים
                light = read_light_intensity()
                distance = read_distance()
                print(f"💡 אור: {light} lux | 📏 מרחק: {distance} ס\"מ")

                # בדיקת חריגות
                alerts = check_alerts(light, people_count, distance)
                if alerts:
                    print("\n🔔 התראות:")
                    for alert in alerts:
                        print(alert)

                # שליחה ל-Firebase
                send_people_count(people_count)
                send_people_to_realtime(people_count)
                send_environment_data(light, distance)
                send_environment_to_realtime(light, distance)

                print("✅ הנתונים נשלחו ל־Firebase\n")

            except Exception as e:
                print(f"❌ שגיאה: {e}")

            time.sleep(10)

    except KeyboardInterrupt:
        print("🛑 עצירה ע״י המשתמש")
    finally:
        cleanup_ultrasonic()  # ניקוי הגדרות GPIO של המרחק

if __name__ == "__main__":
    main_loop()

