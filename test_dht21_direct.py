

import pigpio
import time

class DHT21:
    def __init__(self, pi, gpio):
        self.pi = pi
        self.gpio = gpio
        self.MAX_TIMINGS = 85
        self.data = [0]*5

    def read(self):
        pi = self.pi
        gpio = self.gpio
        data = self.data
        data[:] = [0]*5

        pi.set_mode(gpio, pigpio.OUTPUT)
        pi.write(gpio, pigpio.HIGH)
        time.sleep(0.05)

        pi.write(gpio, pigpio.LOW)
        time.sleep(0.02)

        pi.set_mode(gpio, pigpio.INPUT)

        timings = []
        count = 0

        # לחכות לשינוי בכניסה
        for i in range(self.MAX_TIMINGS):
            count = 0
            while pi.read(gpio) == (i % 2):
                count += 1
                time.sleep(0.00001)
                if count > 1000:
                    break
            timings.append(count)

        bits = []
        for i in range(3, len(timings), 2):
            if timings[i] > timings[i+1]:
                bits.append(1)
            else:
                bits.append(0)

        if len(bits) < 40:
            return None, None  # קריאה לא תקינה

        # המרת ביטים ל-5 בתים
        for i in range(5):
            byte = 0
            for j in range(8):
                byte <<= 1
                byte |= bits[i*8 + j]
            data[i] = byte

        checksum = sum(data[0:4]) & 0xFF
        if checksum != data[4]:
            return None, None  # שגיאת בדיקת תקינות

        humidity = ((data[0] << 8) + data[1]) / 10.0
        temperature = (((data[2] & 0x7F) << 8) + data[3]) / 10.0
        if data[2] & 0x80:
            temperature = -temperature

        return temperature, humidity


if __name__ == "__main__":
    pi = pigpio.pi()
    if not pi.connected:
        print("❌ לא ניתן להתחבר ל-pigpio daemon")
        exit()

    sensor = DHT21(pi, 4)  # GPIO4 = פין 7 בלוח

    try:
        while True:
            temp, hum = sensor.read()
            if temp is None or hum is None:
                print("⚠️ קריאה לא תקינה, מנסה שוב...")
            else:
                print(f"🌡️ טמפרטורה: {temp:.1f}°C | 💧 לחות: {hum:.1f}%")
            time.sleep(2)
    except KeyboardInterrupt:
        print("🛑 עצירה על ידי המשתמש")
    finally:
        pi.stop()
