from ultralytics import YOLO

model = YOLO('yolov8l-pose.pt') #load a pretrained model (recommended for training)

# Train the model
results = model.train(data="config.yaml", epochs=1, imgsz=640)
