from ultralytics import YOLO
import cv2

model_path = "sizeEnginev4.0.pt"
image_path = "test7.jpg"

model = YOLO(model_path)

# 🔥 Set confidence threshold
result = model(image_path, conf=0.8)[0]

# Draw detections
annotated_img = result.plot()

cv2.imshow("Pose Detection", annotated_img)
cv2.waitKey(0)
cv2.destroyAllWindows()

cv2.imwrite("output.jpg", annotated_img)