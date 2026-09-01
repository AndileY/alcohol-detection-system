from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import paho.mqtt.client as mqtt
import json
import threading
import time
import atexit
from datetime import datetime
from collections import deque

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# MQTT Settings - Using public test broker (no auth required)
MQTT_BROKER = "test.mosquitto.org"  # Changed from broker.emqx.io
MQTT_PORT = 1883

# Store latest data
latest_data = {
    "percentage": 0,
    "raw_value": 0,
    "face_status": "waiting",
    "alcohol_result": "WAITING",
    "system_status": "online"
}

# Store historical data (last 1000 records)
history_data = deque(maxlen=1000)
daily_stats = {}
hourly_stats = {}

# Global MQTT client
mqtt_client = None
mqtt_connected = False

# ==========================================
# DATA STORAGE FUNCTIONS
# ==========================================

def store_reading(percentage, raw_value, result):
    """Store reading in history with timestamp"""
    timestamp = datetime.now()
    reading = {
        "timestamp": timestamp.isoformat(),
        "time": timestamp.strftime("%H:%M:%S"),
        "date": timestamp.strftime("%Y-%m-%d"),
        "hour": timestamp.strftime("%H:00"),
        "percentage": percentage,
        "raw_value": raw_value,
        "result": result
    }
    history_data.append(reading)
    
    # Update daily stats
    date_key = timestamp.strftime("%Y-%m-%d")
    if date_key not in daily_stats:
        daily_stats[date_key] = {"granted": 0, "denied": 0, "total": 0, "avg_percentage": 0, "readings": []}
    
    daily_stats[date_key]["total"] += 1
    if result == "GRANTED":
        daily_stats[date_key]["granted"] += 1
    else:
        daily_stats[date_key]["denied"] += 1
    
    daily_stats[date_key]["readings"].append(percentage)
    daily_stats[date_key]["avg_percentage"] = sum(daily_stats[date_key]["readings"]) / len(daily_stats[date_key]["readings"])
    
    # Keep only last 30 days
    keys_to_remove = [k for k in daily_stats.keys() if k < timestamp.strftime("%Y-%m-%d")]
    for k in keys_to_remove:
        del daily_stats[k]
    
    # Update hourly stats
    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
    if hour_key not in hourly_stats:
        hourly_stats[hour_key] = {"count": 0, "avg_percentage": 0, "readings": []}
    
    hourly_stats[hour_key]["count"] += 1
    hourly_stats[hour_key]["readings"].append(percentage)
    hourly_stats[hour_key]["avg_percentage"] = sum(hourly_stats[hour_key]["readings"]) / len(hourly_stats[hour_key]["readings"])
    
    # Keep only last 168 hours (7 days)
    keys_to_remove = [k for k in hourly_stats.keys() if k < timestamp.strftime("%Y-%m-%d %H:00")]
    for k in keys_to_remove:
        del hourly_stats[k]
    
    return reading

def get_statistics():
    """Get overall statistics"""
    if not history_data:
        return {
            "total_tests": 0,
            "granted_count": 0,
            "denied_count": 0,
            "success_rate": 0,
            "avg_percentage": 0,
            "max_percentage": 0,
            "min_percentage": 0
        }
    
    granted = sum(1 for h in history_data if h["result"] == "GRANTED")
    denied = sum(1 for h in history_data if h["result"] == "DENIED")
    percentages = [h["percentage"] for h in history_data]
    
    return {
        "total_tests": len(history_data),
        "granted_count": granted,
        "denied_count": denied,
        "success_rate": round((granted / len(history_data)) * 100, 1) if history_data else 0,
        "avg_percentage": round(sum(percentages) / len(percentages), 1) if percentages else 0,
        "max_percentage": max(percentages) if percentages else 0,
        "min_percentage": min(percentages) if percentages else 0
    }

# ==========================================
# MQTT Callbacks
# ==========================================

def on_connect(client, userdata, flags, rc, properties=None):
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print(f"[Web MQTT] ✅ Connected to {MQTT_BROKER}")
        topics = [
            "alcohol_system/face",
            "alcohol_system/sensor",
            "alcohol_system/alcohol_result",
            "alcohol_system/status",
            "alcohol_system/percentage"
        ]
        for topic in topics:
            client.subscribe(topic)
            print(f"[Web MQTT] Subscribed to {topic}")
    else:
        mqtt_connected = False
        print(f"[Web MQTT] ❌ Connection failed with code: {rc} (trying to reconnect...)")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    
    print(f"[Web MQTT] 📨 {topic}: {payload}")
    
    if topic == "alcohol_system/face":
        latest_data["face_status"] = payload
        socketio.emit('face_status', {'status': payload})
        
    elif topic == "alcohol_system/percentage":
        try:
            percentage = int(payload)
            latest_data["percentage"] = percentage
            socketio.emit('alcohol_data', {
                'percentage': percentage,
                'raw_value': latest_data["raw_value"]
            })
        except Exception as e:
            print(f"[Web MQTT] Error parsing percentage: {e}")
            
    elif topic == "alcohol_system/sensor":
        if "Alcohol:" in payload:
            try:
                parts = payload.split("Alcohol:")
                if len(parts) > 1:
                    percentage_str = parts[1].replace("%", "").strip()
                    percentage = int(percentage_str)
                    latest_data["percentage"] = percentage
                    
                    raw_parts = payload.split("Sensor:")
                    if len(raw_parts) > 1:
                        raw_value = raw_parts[1].split("|")[0].strip()
                        latest_data["raw_value"] = raw_value
                        
                        socketio.emit('alcohol_data', {
                            'percentage': percentage,
                            'raw_value': raw_value
                        })
            except Exception as e:
                print(f"[Web MQTT] Error parsing sensor: {e}")
                    
    elif topic == "alcohol_system/alcohol_result":
        if "NOT GRANTED" in payload:
            latest_data["alcohol_result"] = "DENIED"
            store_reading(latest_data["percentage"], latest_data["raw_value"], "DENIED")
            socketio.emit('alcohol_result', {'result': 'DENIED'})
            socketio.emit('history_update', get_history_data())
            socketio.emit('stats_update', get_statistics())
            socketio.emit('daily_update', get_daily_data())
        elif "GRANTED" in payload:
            latest_data["alcohol_result"] = "GRANTED"
            store_reading(latest_data["percentage"], latest_data["raw_value"], "GRANTED")
            socketio.emit('alcohol_result', {'result': 'GRANTED'})
            socketio.emit('history_update', get_history_data())
            socketio.emit('stats_update', get_statistics())
            socketio.emit('daily_update', get_daily_data())
            
    elif topic == "alcohol_system/status":
        socketio.emit('system_status', {'status': 'online'})
        latest_data["system_status"] = "online"

# ==========================================
# DATA RETRIEVAL FUNCTIONS
# ==========================================

def get_history_data(limit=100):
    """Get history data for charts"""
    data = list(history_data)[-limit:]
    return {
        "timestamps": [d["time"] for d in data],
        "percentages": [d["percentage"] for d in data],
        "results": [d["result"] for d in data],
        "raw_values": [d["raw_value"] for d in data]
    }

def get_daily_data(days=7):
    """Get daily statistics for last N days"""
    result = []
    for date_key in sorted(daily_stats.keys(), reverse=True)[:days]:
        stats = daily_stats[date_key]
        result.append({
            "date": date_key,
            "granted": stats["granted"],
            "denied": stats["denied"],
            "total": stats["total"],
            "avg_percentage": round(stats["avg_percentage"], 1)
        })
    return result[::-1]

def get_hourly_data(hours=24):
    """Get hourly statistics for last N hours"""
    result = []
    for hour_key in sorted(hourly_stats.keys(), reverse=True)[:hours]:
        stats = hourly_stats[hour_key]
        result.append({
            "hour": hour_key,
            "count": stats["count"],
            "avg_percentage": round(stats["avg_percentage"], 1)
        })
    return result[::-1]

# ==========================================
# MQTT Setup
# ==========================================

def setup_mqtt():
    global mqtt_client
    try:
        mqtt_client = mqtt.Client(
            client_id="WebDashboard",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        return True
    except Exception as e:
        print(f"[Web MQTT] Error: {e}")
        return False

# ==========================================
# API ROUTES
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/stats')
def api_stats():
    return jsonify(get_statistics())

@app.route('/api/history')
def api_history():
    limit = request.args.get('limit', 100, type=int)
    return jsonify(get_history_data(limit))

@app.route('/api/daily')
def api_daily():
    days = request.args.get('days', 7, type=int)
    return jsonify(get_daily_data(days))

@app.route('/api/hourly')
def api_hourly():
    hours = request.args.get('hours', 24, type=int)
    return jsonify(get_hourly_data(hours))

@app.route('/health')
def health():
    return {"status": "online", "mqtt_connected": mqtt_connected, "records": len(history_data)}

# ==========================================
# SOCKET.IO EVENTS
# ==========================================

@socketio.on('connect')
def handle_connect():
    print('[Web] 🟢 Client connected')
    socketio.emit('alcohol_data', {
        'percentage': latest_data["percentage"],
        'raw_value': latest_data["raw_value"]
    })
    socketio.emit('face_status', {'status': latest_data["face_status"]})
    socketio.emit('alcohol_result', {'result': latest_data["alcohol_result"]})
    socketio.emit('system_status', {'status': latest_data["system_status"]})
    socketio.emit('history_update', get_history_data())
    socketio.emit('stats_update', get_statistics())
    socketio.emit('daily_update', get_daily_data())

@socketio.on('disconnect')
def handle_disconnect():
    print('[Web] 🔴 Client disconnected')

@socketio.on('request_history')
def handle_request_history():
    socketio.emit('history_update', get_history_data())

# ==========================================
# CLEANUP
# ==========================================

def cleanup():
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("[Web MQTT] Disconnected")

atexit.register(cleanup)

# ==========================================
# MAIN
# ==========================================

if __name__ == '__main__':
    print("=" * 50)
    print("AlcSecure Web Dashboard")
    print(f"Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
    
    if setup_mqtt():
        print("[Web MQTT] ✅ Started successfully")
    else:
        print("[Web MQTT] ❌ Failed to start")
    
    print("")
    print("🌐 Dashboard: http://localhost:5000")
    print("📊 Analytics: http://localhost:5000/analytics")
    print("📜 History: http://localhost:5000/history")
    print("⚙️ Settings: http://localhost:5000/settings")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)