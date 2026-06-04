from ultralytics import YOLO

def train_custom_model(dataset_yaml_path):
    """
    Trains a custom YOLOv8 model for unique vehicle classes
    (e.g., auto-rickshaws, specific bikes, cars) from your annotated dataset.
    """
    # 1. Start with a pre-trained model to transfer learning (faster convergence)
    print("Loading base YOLOv8 model...")
    model = YOLO("yolov8n.pt") # 'n' stands for nano (fastest). Use 's' for small if you need more accuracy.
    
    # 2. Train the model on your custom dataset
    print(f"Starting training on {dataset_yaml_path}...")
    
    # Typical training parameters for a quick test run:
    # epochs=50: Train for 50 passes over the data.
    # imgsz=640: Resize input images to 640x640.
    # batch=16: Number of images processed at once (reduce if out of memory).
    results = model.train(
        data=dataset_yaml_path,
        epochs=50,
        imgsz=640,
        batch=8,           # Reduced from 16 to fit in Unified Memory
        workers=2,         # Added workers to feed the GPU faster
        project="traffic_camera_models",
        name="vehicle_detector_v1",
        device=0           # Targets the NVIDIA RTX 3050 GPU (CUDA)
    )
    
    print("\n--- Training Complete! ---")
    print("Best model weights saved in: traffic_camera_models/vehicle_detector_v1/weights/best.pt")

if __name__ == "__main__":
    print("Downloading dataset from Roboflow...")
    try:
        from roboflow import Roboflow
    except ImportError:
        print("Please install roboflow first: pip install roboflow")
        exit(1)
        
    rf = Roboflow(api_key="ODrvcE5jzj5aD9NwHqIR")
    project = rf.workspace("princes-workspace-jli8i").project("t5_smarttrafficlight_b1-4-nkphl")
    version = project.version(1) # We use version 1
    dataset = version.download("yolov8")
    
    # The 'dataset.location' contains the absolute path to the downloaded folder
    DATASET_YAML = f"{dataset.location}/data.yaml"
    
    import os
    if os.path.exists(DATASET_YAML):
        train_custom_model(DATASET_YAML)
    else:
        print(f"Dataset YAML not found at {DATASET_YAML}. Download may have failed.")
