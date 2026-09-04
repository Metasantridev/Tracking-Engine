import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Kamera index {i} -> OK")
        cap.release()
    else:
        print(f"Kamera index {i} -> tidak ada")
