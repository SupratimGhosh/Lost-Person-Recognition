# Advanced Face Recognition Pipeline

This project implements a real-time, multi-threaded face recognition and crowd monitoring system designed for surveillance applications.

## Key Features

1.  **High-Performance Face Recognition**:
    *   **Detection**: Uses `FaceDetector` (YOLOv8-Face) on every 10th frame for efficiency.
    *   **Recognition**: Matches faces against a dynamic reference database using cosine similarity.
    *   **Smart Preprocessing**: Automatically detects and crops faces from reference images for accurate embedding.

2.  **Crowd Management**:
    *   **Real-time Monitoring**: Estimates crowd density using `CSRNet` (via `src/crowd`).
    *   **Efficient Architecture**: Reuses the capture thread's frames, running inference every 60 seconds (customizable).
    *   **Alerts**: Triggers a `CROWD_ALERT` if density exceeds the threshold (100).

3.  **Alert System**:
    *   **MongoDB Integration**: Logs recognized "Lost Persons" and crowd alerts to a MongoDB collection.
    *   **Geolocation**: Fetches the device's current location (City, Region, Lat/Lon) via IP and attaches it to every alert.
    *   **Cooldowns**: Prevents spam by enforcing a 5-minute cooldown per person.

4.  **Dynamic Database Updates**:
    *   **Periodic Refresh**: Fetches new "Lost Person" images from MongoDB every 10 minutes.
    *   **Auto-Cleanup**: Automatically clears old reference data before updating to ensure a clean state.

## Installation

Ensure you have the required dependencies installed:

```bash
pip install opencv-python torch torchvision pillow pymongo requests ultralytics scikit-learn
```

(Note: `src.crowd` and `src.recognition` modules are expected to be present in the project structure).

## Usage

The main entry point is `pipeline_advanced.py`.

### Basic Run
Run with default settings (Webcam 0):
```bash
python pipeline_advanced.py --source 0
```

### Custom Configuration
```bash
python pipeline_advanced.py --source "rtsp://user:pass@IP:554/stream" --conf 0.3 --threshold 0.38 --db-interval 600
```

See `PIPELINE_USAGE.md` for detailed configuration options.
