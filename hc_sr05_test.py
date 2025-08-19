

import RPi.GPIO as GPIO
import time
from collections import deque

# הגדרות פינים
TRIG_PIN = 23
ECHO_PIN = 24

# כיבוי אזהרות
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# תור לשמירת מדידות אחרונות (לממוצע נע)
readings = deque(maxlen=5)

def measure_distance_debug():
    GPIO.output(TRIG_PIN, False)
    print("DEBUG: TRIG set to LOW")
    time.sleep(1)

    GPIO.output(TRIG_PIN, True)
    print("DEBUG: TRIG set to HIGH")
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)
    print("DEBUG: TRIG set to LOW again")

    timeout_start = time.time() + 1
    pulse_start = None
    while GPIO.input(ECHO_PIN) == 0:
        pulse_start = time.time()
        if pulse_start > timeout_start:
            print("DEBUG: Timeout waiting for ECHO to go HIGH")
            return None
    print(f"DEBUG: ECHO went HIGH at {pulse_start}")

    timeout_end = time.time() + 1
    pulse_end = None
    while GPIO.input(ECHO_PIN) == 1:
        pulse_end = time.time()
        if pulse_end > timeout_end:
            print("DEBUG: Timeout waiting for ECHO to go LOW")
            return None
    if pulse_end is None:
        print("DEBUG: ECHO did not go LOW, measurement failed")
        return None

    print(f"DEBUG: ECHO went LOW at {pulse_end}")

    pulse_duration = pulse_end - pulse_start
    print(f"DEBUG: Pulse duration = {pulse_duration:.6f} seconds")

    distance = pulse_duration * 34300 / 2
    print(f"DEBUG: Calculated distance = {distance:.2f} cm")

    return round(distance, 2)

try:
    while True:
        dist = measure_distance_debug()
        if dist is None:
            print("DEBUG: Measurement failed due to timeout.")
        elif 2 <= dist <= 400:
            readings.append(dist)
            avg = sum(readings) / len(readings)
            print(f"מרחק נמדד: {dist} ס\"מ | ממוצע נע ({len(readings)} קריאות): {avg:.2f} ס\"מ")
        else:
            print(f"DEBUG: מרחק חריג ({dist} ס\"מ), לא נוסף לממוצע")

        time.sleep(1)

except KeyboardInterrupt:
    print("ניקוי GPIO וסיום")
    GPIO.cleanup()

