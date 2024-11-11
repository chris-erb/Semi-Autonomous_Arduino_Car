import cv2
import numpy as np
from flask import Flask, Response, render_template
import requests
import time
from flask_cors import CORS, cross_origin

ESP32_URL = "http://192.168.4.1"
STREAM_URL = "http://192.168.4.1:81/stream"

app = Flask(__name__)
CORS(app)

# Global variable to track autonomous mode
is_autonomous = False

def send_command(command):
    if not is_autonomous:  # Only send commands if NOT in autonomous mode
        try:
            requests.get(f"{ESP32_URL}?direction={command}")
            #print(f"Sent command: {command}")
        except Exception as e:
            print(f"Error sending command: {e}")
    else:
        print("Autonomous mode is on. Command not sent.")

def process_frame(frame):
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection
    edges = cv2.Canny(blurred, 50, 150)

    # Define a region of interest (ROI) for lane detection
    height, width = edges.shape
    roi = edges[int(height / 2):height, 0:width]

    # Hough Transform to detect lines
    lines = cv2.HoughLinesP(roi, 1, np.pi / 180, threshold=50, minLineLength=100, maxLineGap=50)

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(frame, (x1, y1 + int(height / 2)), (x2, y2 + int(height / 2)), (0, 255, 0), 2)

        # Determine lane position and send commands
        lane_center = (x1 + x2) / 2
        frame_center = width / 2

        # Simple logic for lane following
        if lane_center < frame_center - 50:  # Lane is to the left
            send_command("LEFT")
        elif lane_center > frame_center + 50:  # Lane is to the right
            send_command("RIGHT")
        else:  # Lane is centered
            send_command("FORWARD")

    return frame  # Return the processed frame for streaming

def generate_processed_stream():
    response = requests.get(STREAM_URL, stream=True)

    if response.status_code == 200:
        bytes_data = b''
        for chunk in response.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')  # JPEG start
            b = bytes_data.find(b'\xff\xd9')  # JPEG end
            if a != -1 and b != -1:
                jpg = bytes_data[a:b + 2]  # Extract the JPEG data
                bytes_data = bytes_data[b + 2:]  # Remove the processed bytes
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    processed_frame = process_frame(frame)  # Process the frame

                    # Encode the frame in JPEG format
                    ret, buffer = cv2.imencode('.jpg', processed_frame)
                    if not ret:
                        print("Failed to encode frame.")
                        break

                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    else:
        print(f"Failed to access stream. Status code: {response.status_code}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/processed_stream')
@cross_origin()
def processed_stream():
    return Response(generate_processed_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/toggle_autonomous', methods=['GET'])
def toggle_autonomous():
    global is_autonomous
    is_autonomous = not is_autonomous  # Toggle the autonomous mode
    status = "enabled" if is_autonomous else "disabled"
    print(f"Autonomous mode is now {status}.")
    return {"autonomous_mode": status}, 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port = 5000)