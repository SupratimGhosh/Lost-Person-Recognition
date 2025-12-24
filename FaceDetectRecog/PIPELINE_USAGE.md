# Pipeline Usage Guide

This guide details the configuration and usage of the `pipeline_advanced.py` script.

## CLI Arguments

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--source` | `0` | Video source. Use `0` for webcam or an RTSP URL string for IP cameras. |
| `--conf` | `0.3` | Face detection confidence threshold (0.0 - 1.0). Lower values detect more faces but may increase false positives. |
| `--threshold` | `0.38` | Recognition cosine similarity threshold. Higher values require stricter matches. |
| `--db-interval` | `600` | Seconds between Reference DB updates. Default is 10 minutes. |

### Example

```bash
python pipeline_advanced.py --source 0 --conf 0.4 --threshold 0.45 --db-interval 300
```

## Features Deep Dive

### 1. Face Recognition Loop
-   **Capture**: Reads frames continuously.
-   **Detection**: Runs detection on every 10th frame.
-   **Embedding**: Crops detected faces and computes embeddings.
-   **Matching**: Compares embeddings against `reference_embeddings` loaded from `exported_images`.
-   **Alerts**: If a match is found (score > threshold):
    -   Logs the match.
    -   Sends an alert to MongoDB with `person_id` extracted from the filename.
    -   Attaches current location (e.g., "Ujjain, MP (23.17, 75.78)").

### 2. Crowd Monitoring
-   **Mechanism**: A dedicated thread wakes up every 60 seconds (or configured sleep time).
-   **Input**: Uses the *latest available frame* from the capture thread (no new camera connection needed).
-   **Inference**: Runs `CSRNet` to estimate crowd count.
-   **Alert**: If count > 100 (configurable in code), sends a `CROWD_ALERT` to MongoDB.

### 3. Reference Database Updates
-   **Process**:
    1.  Deletes all files in `exported_images/` and `reference_embeddings/`.
    2.  Runs `lost_images/fetch_image_db.py` to download fresh images from MongoDB.
    3.  Runs Face Detection on these new images to crop faces.
    4.  Computes embeddings for the crops and saves them.
-   **Timing**: Runs on startup and then every `--db-interval` seconds.

### 4. Alert System
-   **Destination**: MongoDB `alerts` collection.
-   **Schema**:
    ```json
    {
      "person_id": "string",
      "location": "City, Region (Lat, Lon)",
      "timestamp": "ISO Date",
      "confidence": float,
      "image_path": "string",
      "status": "new",
      "message": "Person ... detected at ..."
    }
    ```
-   **Cooldown**: 5 minutes per person.

## Troubleshooting

-   **"No face detected in reference image"**: Ensure uploaded "Lost Person" images have visible faces.
-   **"Crowd thread disabled"**: Check if `src/crowd/task_two_model_best.pth.tar` exists and `torchvision` is installed.
-   **Geolocation irrelevant**: The script uses IP-based location specific to the *machine running the pipeline*. Ensure internet access is available.
