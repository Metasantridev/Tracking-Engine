# Tracking Engine

Hand and face tracking engine berbasis MediaPipe + OpenCV.

## Stack
- **MediaPipe** — hand & face landmark detection
- **OpenCV** — video capture & rendering
- **NumPy** — array processing

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Jalankan

```bash
# Hand tracking
python hand_tracking.py

# Face tracking
python face_tracking.py

# Keduanya sekaligus
python combined_tracking.py
```
