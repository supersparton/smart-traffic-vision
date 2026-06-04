import os
import cv2
import json
import time
import queue
import threading
import base64
import numpy as np
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit
from vehicle_detector import VehicleDetector
from traffic_signal_controller import TrafficSignalController

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configuration
MODEL_PATH = "runs/detect/traffic_camera_models/vehicle_detector_v1/weights/best.pt"
detector = VehicleDetector(MODEL_PATH)
controller = TrafficSignalController()

# Global storage for live frames from mobile
live_frames = {} # {lane_name: base64_image}
pair_to_lane = {} # {pair_code: lane_name}

def process_video(lane_video_map, is_live=False):
    """
    SEQUENTIAL INFERENCE SYNC:
    Processes lanes one-by-one to prevent GPU overload.
    lane_video_map: dict like {"North": "path/to/video.mp4", "South": "path/to/video2.mp4"}
    """
    # Open video captures mapped to their specific lanes
    lane_caps = {}
    for lane, path in lane_video_map.items():
        lane_caps[lane] = cv2.VideoCapture(path)
    
    lane_names = ["North", "East", "South", "West"]
    frame_count = 0
    last_detections = {} # Store latest detections per lane
    
    while True:
        status = controller.tick()
        
        # Sequentially process each lane
        for lane in lane_names:
            frame = None
            
            # Read Frame - only from the correct video for this lane
            if lane in lane_caps or is_live:
                if is_live:
                    frame_base64 = live_frames.get(lane)
                    if frame_base64:
                        img_data = base64.b64decode(frame_base64.split(',')[1])
                        nparr = np.frombuffer(img_data, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                elif lane in lane_caps:
                    cap = lane_caps[lane]
                    ret, frame = cap.read()
                    if not ret:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
            
            # Inference & Update (SYNC)
            if frame is not None:
                detections, counts = detector.detect(frame)
                controller.update_lane_data(lane, counts)
                frame = detector.draw_annotations(frame, detections)
                last_detections[lane] = detections
                
                _, buffer = cv2.imencode('.jpg', frame)
                
                # Emit update for THIS lane immediately
                socketio.emit('lane_update', {
                    "lane": lane,
                    "frame": buffer.tobytes().hex(),
                    "counts": controller.lane_data[lane]["count"],
                    "breakdown": detections,
                    "controller": status
                })
                # No artificial delay - real-time processing
            else:
                # No video for this lane - skip entirely
                pass
        
        frame_count += 1
        socketio.sleep(0.01) 

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist("videos")
    lane_names = request.form.getlist("lanes") # e.g. ["North", "South"]
    is_live = request.form.get("is_live") == "true"
    
    # Build lane -> video path map
    lane_video_map = {}
    for i, file in enumerate(files):
        if file.filename != '':
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            if i < len(lane_names):
                lane_video_map[lane_names[i]] = path
    
    # Start processing in background
    thread = threading.Thread(target=process_video, args=(lane_video_map, is_live))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "success", "video_count": len(lane_video_map), "active_lanes": list(lane_video_map.keys())})

@app.route('/mobile/<pair_code>')
def mobile_capture(pair_code):
    return render_template('mobile_stream.html', pair_code=pair_code)

@app.route('/upload_live/<pair_code>', methods=['POST'])
def upload_live(pair_code):
    lane = pair_to_lane.get(pair_code)
    if not lane:
        return jsonify({"status": "error", "message": "Invalid code"}), 400
    
    data = request.json
    live_frames[lane] = data.get('image')
    return jsonify({"status": "ok"})

@app.route('/generate_codes')
def generate_codes():
    import random
    lanes = ["North", "East", "South", "West"]
    new_codes = {}
    for lane in lanes:
        code = "".join([str(random.randint(0, 9)) for _ in range(6)])
        new_codes[lane] = code
        pair_to_lane[code] = lane
    return jsonify(new_codes)

@app.route('/stream')
def stream():
    return "Use WebSocket instead", 400

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
