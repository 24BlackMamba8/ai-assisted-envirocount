

# test_dht21_pigpio.py
import pigpio
import dht11
import time

# יצירת אובייקט pigpio
pi = pigpio.pi()
if not pi.connected:
    exit()

# הגדרת הפין (GPIO4 = פין 7)
sensor = dht11.DHT11(pi, 4)

print("📡 קריאה מהחיישן DHT21 (AM2301)...")

while True:
    result = sensor.read()
    if result.is_valid():
        print(f"🌡️ Temp: {result.temperature}°C  💧 Humidity: {result.humidity}%")
    else:
        print("⚠️ קריאה לא תקינה...")

    time.sleep(2)
