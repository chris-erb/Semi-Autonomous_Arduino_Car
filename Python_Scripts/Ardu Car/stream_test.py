import cv2
import requests
import numpy as np

url = "http://192.168.4.1:81/stream"

# Start a GET request to the stream
response = requests.get(url, stream=True)

if response.status_code == 200:
    bytes_data = b''
    for chunk in response.iter_content(chunk_size=1024):
        bytes_data += chunk
        a = bytes_data.find(b'\xff\xd8')  # JPEG start
        b = bytes_data.find(b'\xff\xd9')  # JPEG end
        if a != -1 and b != -1:
            jpg = bytes_data[a:b+2]  # Extract the JPEG data
            bytes_data = bytes_data[b+2:]  # Remove the processed bytes
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                cv2.imshow("MJPEG Stream", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
else:
    print(f"Failed to access stream. Status code: {response.status_code}")

cv2.destroyAllWindows()