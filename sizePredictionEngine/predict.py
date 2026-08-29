from ultralytics import YOLO
import cv2
import numpy as np  # mathematical calculations

model_path = "Y26sizeEnginev6.0.pt"
image_path = "img63.jpeg"

# User manually enters their actual height in centimeters
# This value will later come from your backend/frontend.
real_height = 182.88   # in centimeters


model = YOLO(model_path)

result = model(image_path, conf=0.8)[0]  # run pose detection

# Draw detections
annotated_img = result.plot()

# Extract keypoints and calculate measurements
if result.keypoints is not None:

    keypoints = result.keypoints.xy.cpu().numpy()

    for person in keypoints:

        def get_distance(p1, p2):
            return np.linalg.norm(p1 - p2)

        # Keypoints (COCO format)
        left_shoulder = person[5]
        right_shoulder = person[6]

        left_hip = person[11]
        right_hip = person[12]

        left_ankle = person[15]
        right_ankle = person[16]

        left_eye = person[1]
        right_eye = person[2]

        # --------------------------------------------------
        # PIXEL MEASUREMENTS
        # --------------------------------------------------

        shoulder_width = get_distance(left_shoulder, right_shoulder)
        hip_width = get_distance(left_hip, right_hip)

        eye_mid = (left_eye + right_eye) / 2
        foot_mid = (left_ankle + right_ankle) / 2

        height = get_distance(eye_mid, foot_mid)

        # --------------------------------------------------
        # NORMALIZED MEASUREMENTS
        # --------------------------------------------------

        shoulder_ratio = shoulder_width / height if height != 0 else 0
        hip_ratio = hip_width / height if height != 0 else 0

        # --------------------------------------------------
        # EXISTING PIXEL OUTPUT
        # --------------------------------------------------

        print("\n--- Measurements ---")
        print("Shoulder (px):", shoulder_width)
        print("Hip (px):", hip_width)
        print("Height (px):", height)
        print("Shoulder ratio:", shoulder_ratio)
        print("Hip ratio:", hip_ratio)

        # --------------------------------------------------
        # REAL MEASUREMENT CALCULATION
        # --------------------------------------------------

        if height != 0:

            # Scale:
            # real height in cm / detected height in pixels
            cm_per_pixel = real_height / height

            # Convert shoulder and hip pixel measurements
            # into real-world centimeters
            shoulder_cm = shoulder_width * cm_per_pixel
            hip_cm = hip_width * cm_per_pixel

            print("\n--- Real Measurements ---")
            print("User Real Height (cm):", real_height)
            print("Scale (cm per pixel):", cm_per_pixel)
            print("Shoulder (cm):", shoulder_cm)
            print("Hip (cm):", hip_cm)

        else:
            print("\nCannot calculate real measurements because pixel height is 0.")

        # --------------------------------------------------
        # DRAWING PART
        # --------------------------------------------------

        # Convert to int for OpenCV
        ls = tuple(left_shoulder.astype(int))
        rs = tuple(right_shoulder.astype(int))

        lh = tuple(left_hip.astype(int))
        rh = tuple(right_hip.astype(int))

        eye_pt = tuple(eye_mid.astype(int))
        foot_pt = tuple(foot_mid.astype(int))

        # Draw lines
        cv2.line(
            annotated_img,
            ls,
            rs,
            (0, 255, 0),
            2
        )  # shoulders

        cv2.line(
            annotated_img,
            lh,
            rh,
            (255, 0, 0),
            2
        )  # hips

        cv2.line(
            annotated_img,
            eye_pt,
            foot_pt,
            (0, 0, 255),
            2
        )  # height

        # Draw text
        cv2.putText(
            annotated_img,
            f"S:{shoulder_width:.1f}",
            (ls[0], ls[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

        cv2.putText(
            annotated_img,
            f"H:{hip_width:.1f}",
            (lh[0], lh[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 0),
            2
        )

        cv2.putText(
            annotated_img,
            f"HT:{height:.1f}",
            (eye_pt[0], eye_pt[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2
        )

else:
    print("No pose keypoints detected.")


# --------------------------------------------------
# SHOW RESULT
# --------------------------------------------------

cv2.imshow("Pose Detection", annotated_img)

cv2.waitKey(0)

cv2.destroyAllWindows()


# --------------------------------------------------
# SAVE OUTPUT IMAGE
# --------------------------------------------------

cv2.imwrite("output.jpg", annotated_img)