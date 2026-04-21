import cv2
import time
import os
import numpy as np
from ultralytics import YOLO

# Paths for model and input/output
WEIGHTS_ONNX = 'weights/border_yolov8n.onnx'  # Path to ONNX model
WEIGHTS_PT = 'weights/best.pt'  # Backup path (not used if ONNX exists)
INPUT_VIDEO = 'data/raw/sample4.mp4'  # Path to input video (adjust if needed)
OUTPUT_VIDEO = "D:/Shihab_files/AI_Based_Threat_Detection_for_Border_Surveillance/final_demo12.mp4"  # Output annotated video

CONF = 0.35  # Confidence threshold

# Create output folder if it doesn't exist
os.makedirs('runs', exist_ok=True)

# Select model (ONNX if available, otherwise PT)
weights = WEIGHTS_ONNX if os.path.exists(WEIGHTS_ONNX) else WEIGHTS_PT
print('Using weights:', weights)
model = YOLO(weights)

# Open video input and output setup
cap = cv2.VideoCapture(INPUT_VIDEO)
assert cap.isOpened(), f'Cannot open {INPUT_VIDEO}'
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Get width of video frame
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # Get height of video frame
fps = cap.get(cv2.CAP_PROP_FPS) or 25  # FPS of video
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Video codec (mp4v)
out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, fps, (w, h))  # Output video writer

# Define virtual border line (e.g., the middle of the frame)
virtual_border = h // 2
print(f"Virtual border set at {virtual_border} (middle of the frame)")

prev = time.time()

while True:
    ok, frame = cap.read()
    if not ok: break  # Break if the frame is not read correctly

    # Draw the fixed virtual border line (red dashed line across the frame)
    cv2.line(frame, (0, virtual_border), (w, virtual_border), (0, 0, 255), 2)  # red line at virtual border

    # Run object detection on the frame
    res = model.predict(source=frame, conf=CONF, verbose=False)[0]

    # Annotate the frame with predictions
    annotated = res.plot()

    # Loop through all detected objects and handle near-border detection
    for det in res.boxes.data:  # `boxes.data` contains detected boxes
        x1, y1, x2, y2, conf, cls = det  # Unpack detection details
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)  # Center of the object

        # Draw bounding box and label
        label = f"{model.names[int(cls)]} {conf:.2f}"
        cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(annotated, label, (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Check if object is near the virtual border
        if abs(cy - virtual_border) < 40:  # 40px margin near the border
            cv2.putText(annotated, "Near Border", (cx, cy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            print(f"Object near border at ({cx},{cy})")

        # Correct the Bangladesh vs Push-in logic based on virtual border position
        if cy > virtual_border:
            # Bangladesh side (object is above virtual border)
            cv2.putText(annotated, "Bangladesh Side", (cx, cy + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            # Push-in side (object is below virtual border)
            cv2.putText(annotated, "Push-in Threat (India Side)", (cx, cy + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Calculate FPS
    now = time.time()
    cur_fps = 1.0 / (now - prev + 1e-6)  # FPS = 1 / (time difference between frames)
    prev = now

    # Display FPS on the frame
    cv2.putText(annotated, f'FPS: {cur_fps:.1f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Write the annotated frame to the output video
    out.write(annotated)

    # Optionally show the frame (remove the comment if you want to view it in real time)
    # cv2.imshow('Detection', annotated)

    # Exit loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and writer
cap.release()
out.release()

# Close any open OpenCV windows
cv2.destroyAllWindows()

print('Saved annotated demo video to:', OUTPUT_VIDEO)
