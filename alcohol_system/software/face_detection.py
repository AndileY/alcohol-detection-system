import cv2
import serial
import time
import paho.mqtt.client as mqtt
import random
import re

# ==========================================
# CONFIGURATION
# ==========================================

ARDUINO_PORT = 'COM10'

# MQTT Settings - Using SAME broker as web server
MQTT_BROKER = "test.mosquitto.org"  # CHANGED to match web_server
MQTT_PORT = 1883
MQTT_CLIENT_ID = f"KS0397_{random.randint(1000, 9999)}"

# MQTT Topics
TOPIC_STATUS = "alcohol_system/status"
TOPIC_SENSOR = "alcohol_system/sensor"
TOPIC_FACE = "alcohol_system/face"
TOPIC_ALCOHOL = "alcohol_system/alcohol_result"
TOPIC_PERCENTAGE = "alcohol_system/percentage"

# ==========================================
# MQTT SETUP
# ==========================================

mqtt_client = None
mqtt_connected = False

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print(f"[MQTT] ✅ Connected to {MQTT_BROKER}")
        client.publish(TOPIC_STATUS, "KS0397 System Online")
    else:
        mqtt_connected = False
        print(f"[MQTT] ❌ Connection failed with code: {rc}")

def on_publish(client, userdata, mid):
    print(f"[MQTT] 📤 Published: {mid}")

def init_mqtt():
    global mqtt_client, mqtt_connected
    try:
        mqtt_client = mqtt.Client(
            client_id=MQTT_CLIENT_ID,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
        mqtt_client.on_connect = on_connect
        mqtt_client.on_publish = on_publish
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        time.sleep(2)
        return mqtt_connected
    except Exception as e:
        print(f"[MQTT] Error: {e}")
        return False

def publish_message(topic, message):
    if mqtt_client and mqtt_connected:
        result = mqtt_client.publish(topic, message)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[MQTT] 📤 {topic}: {message}")
        else:
            print(f"[MQTT] ❌ Failed to publish: {topic}")

# ==========================================
# FACE DETECTION
# ==========================================

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

def detect_face():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("ERROR: Cannot open webcam!")
        return False
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("Looking for face... (look at the camera!)")
    time.sleep(1)
    
    start_time = time.time()
    face_detected = False
    
    while time.time() - start_time < 5:
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(60, 60))
            if len(faces) > 0:
                print(f"✓ Face detected!")
                face_detected = True
                break
            else:
                print(".", end="", flush=True)
    
    cap.release()
    return face_detected

# ==========================================
# SERIAL SETUP
# ==========================================

try:
    arduino = serial.Serial(ARDUINO_PORT, 9600, timeout=1)
    time.sleep(2)
    print(f"[Serial] ✅ Connected to {ARDUINO_PORT}")
except Exception as e:
    print(f"[Serial] Error: {e}")
    arduino = None

# ==========================================
# MAIN LOOP
# ==========================================

print("=" * 50)
print("KS0397 Alcohol System with MQTT")
print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
print("=" * 50)

# Initialize MQTT
init_mqtt()

if mqtt_connected:
    print("[MQTT] ✅ Ready - Publishing to test.mosquitto.org")
else:
    print("[MQTT] ⚠️ Running without MQTT")

print("\nPress button on KS0397 to start")
print("=" * 50)

while True:
    if arduino and arduino.in_waiting:
        command = arduino.readline().decode().strip()
        print(f"\n[Arduino] {command}")
        
        if command == "FACE_SCAN_REQUEST":
            print("[System] Face scan requested!")
            publish_message(TOPIC_FACE, "scan_started")
            
            if detect_face():
                print("[System] Sending 'V' (VERIFIED)")
                arduino.write(b'V')
                arduino.flush()
                publish_message(TOPIC_FACE, "verified")
                
                print("\n" + "=" * 50)
                print("✅ FACE VERIFIED! NOW BLOW INTO SENSOR")
                print("=" * 50 + "\n")
                
            else:
                print("[System] Sending 'F' (FAILED)")
                arduino.write(b'F')
                arduino.flush()
                publish_message(TOPIC_FACE, "failed")
        
        # Send alcohol results to MQTT
        elif "NOT GRANTED" in command:
            publish_message(TOPIC_ALCOHOL, "NOT GRANTED - Alcohol Detected")
            publish_message(TOPIC_STATUS, "Access Denied")
            print(f"[System] 🚫 NOT GRANTED - Alcohol detected!")
            
        elif "GRANTED" in command:
            publish_message(TOPIC_ALCOHOL, "GRANTED - Sober")
            publish_message(TOPIC_STATUS, "Access Granted")
            print(f"[System] ✅ GRANTED - Sober")
        
        # Extract and publish percentage
        elif "Sensor:" in command or "Alcohol:" in command:
            publish_message(TOPIC_SENSOR, command)
            
            match = re.search(r'(\d+)\s*%', command)
            if match:
                percentage = match.group(1)
                publish_message(TOPIC_PERCENTAGE, percentage)
                print(f"[MQTT] 📊 Published percentage: {percentage}%")
    
    time.sleep(0.1)