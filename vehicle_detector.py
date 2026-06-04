import cv2
from ultralytics import YOLO

class VehicleDetector:
    def __init__(self, model_path):
        # Load the custom trained model
        # Load and move model to dedicated GPU (CUDA)
        self.model = YOLO(model_path).to('cuda')
        # Class names from your data.yaml
        self.classes = ['Rikshaw', 'bus', 'car', 'motorbike', 'truck']

    def detect(self, frame):
        """
        Runs inference and returns detections.
        """
        # Run inference with reduced image size for high speed (320px)
        results = self.model(frame, imgsz=320, verbose=False)[0]
        
        detections = []
        counts = {cls: 0 for cls in self.classes}
        
        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            if conf < 0.25: continue # Confidence threshold
            
            cls_name = self.model.names[cls_id]
            if cls_name in counts:
                counts[cls_name] += 1
                
            # Get coordinates
            x1, y1, x2, y2 = box.xyxy[0]
            detections.append({
                "class": cls_name,
                "confidence": conf,
                "bbox": [int(x1), int(y1), int(x2), int(y2)]
            })
            
        return detections, counts

    def draw_annotations(self, frame, detections):
        """ Draws bounding boxes on the frame. """
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = f"{det['class']} {det['confidence']:.2f}"
            
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Draw label
            cv2.putText(frame, label, (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame
