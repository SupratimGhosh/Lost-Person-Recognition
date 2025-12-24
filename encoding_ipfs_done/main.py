import cv2
import os
import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from Crypto.Cipher import AES
from Crypto import Random
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.backends import default_backend
from key_manager import get_binary_keys

# ==============================
# CONFIGURATION
# ==============================
IPFS_API_URL = "http://127.0.0.1:5001/api/v0/add"
OUTPUT_DIR = "encrypted_chunks"
HASH_LOG = "ipfs_hashes.txt"
CHUNK_DURATION = 1 * 60  # 5 minutes

# ==============================
# UTILITY FUNCTIONS
# ==============================

def debug_log(message):
    """Prints timestamped debug messages to console and file."""
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {message}"
    print(line)
    with open("debug.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def aes_encrypt(data, key):
    nonce = Random.new().read(16)
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return nonce + tag + ciphertext

def chacha20_encrypt(data, key):
    nonce = os.urandom(16)  # ChaCha20 typically uses a 12-byte nonce, but cryptography library expects 16 bytes here
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
    encryptor = cipher.encryptor()
    return nonce + encryptor.update(data)

def _is_webcam_source(src):
    if isinstance(src, int):
        return True
    if isinstance(src, str) and src.isdigit():
        return True
    return False

def _open_capture(src):
    if _is_webcam_source(src):
        idx = int(src) if isinstance(src, str) else src
        if os.name == "nt":
            return cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        return cv2.VideoCapture(idx)
    return cv2.VideoCapture(src)

def upload_to_ipfs(filepath):
    """Uploads a file to IPFS and returns the CID."""
    try:
        with open(filepath, "rb") as f:
            files = {"file": f}
            res = requests.post(IPFS_API_URL, files=files)
            cid = res.json().get("Hash")
            debug_log(f"✅ Uploaded {os.path.basename(filepath)} → CID: {cid}")
            with open(HASH_LOG, "a") as log:
                log.write(f"{datetime.now()} | {filepath} | {cid}\n")
            return cid
    except Exception as e:
        debug_log(f"❌ IPFS upload failed for {filepath}: {e}")
        return None

def save_encrypted_chunk(frames, stream_id, chunk_idx):
    """Saves encrypted frames to a file and uploads it."""
    if not frames:
        return
    filename = f"{OUTPUT_DIR}/stream{stream_id}_chunk{chunk_idx}.bin"
    with open(filename, "wb") as f:
        for frame in frames:
            f.write(frame)
    debug_log(f"🧩 Saved encrypted chunk {chunk_idx} for stream {stream_id}, uploading to IPFS...")
    upload_to_ipfs(filename)

# ==============================
# MAIN PROCESSING FUNCTION
# ==============================

def process_stream(rtsp_url, stream_id, stop_event=None):
    debug_log(f"🎥 Starting stream {stream_id}: {rtsp_url}")
    cap = _open_capture(rtsp_url)
    if not cap.isOpened():
        debug_log(f"❌ Unable to open stream {rtsp_url}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get encryption keys from key manager
    key_aes, key_chacha = get_binary_keys()

    start_time = time.time()
    chunk_idx = 0
    frames_buffer = []
    frame_counter = 0

    try:
        while True:
            if stop_event and stop_event.is_set():
                debug_log(f"🛑 Stop requested. Ending stream {stream_id}...")
                break
            ret, frame = cap.read()
            if not ret:
                debug_log(f"⚠️ Stream {stream_id} ended or lost connection.")
                break

            ret, encoded = cv2.imencode(".jpg", frame)
            frame_bytes = encoded.tobytes()

            # Encrypt based on frame type (simulate I/P/B distinction)
            frame_counter += 1
            if frame_counter % 60 == 0:
                encrypted = aes_encrypt(frame_bytes, key_aes)  # I-frame
                enc_type = 1  # AES
            else:
                encrypted = chacha20_encrypt(frame_bytes, key_chacha)  # P/B-frames
                enc_type = 0  # ChaCha20

            # Add header: 1 byte type + 4 bytes length
            import struct
            header = struct.pack('>BI', enc_type, len(encrypted))
            frames_buffer.append(header + encrypted)

            # Chunk every 5 minutes
            if time.time() - start_time >= CHUNK_DURATION:
                save_encrypted_chunk(frames_buffer, stream_id, chunk_idx)
                frames_buffer = []
                start_time = time.time()
                chunk_idx += 1

    except KeyboardInterrupt:
        debug_log(f"🛑 KeyboardInterrupt received! Stopping stream {stream_id} gracefully...")
        save_encrypted_chunk(frames_buffer, stream_id, chunk_idx)
        cap.release()
        return
    except Exception as e:
        debug_log(f"❌ Error in stream {stream_id}: {e}")
    finally:
        save_encrypted_chunk(frames_buffer, stream_id, chunk_idx)
        cap.release()
        debug_log(f"✅ Stream {stream_id} finished.")

# ==============================
# MULTI-THREAD LAUNCHER
# ==============================

def main(rtsp_streams):
    debug_log("🚀 Starting RTSP multi-thread processor...")
    stop_event = threading.Event()
    try:
        with ThreadPoolExecutor(max_workers=len(rtsp_streams)) as executor:
            futures = [executor.submit(process_stream, stream, idx, stop_event) for idx, stream in enumerate(rtsp_streams)]
            while True:
                time.sleep(0.5)
                if all(f.done() for f in futures):
                    break
    except KeyboardInterrupt:
        debug_log("🛑 Interrupt signal received! Terminating all streams safely...")
        stop_event.set()
    finally:
        debug_log("🏁 All streams stopped. Exiting gracefully.")

# ==============================
# RUN EXAMPLE
# ==============================

if __name__ == "__main__":
    rtsp_links = [
        "0",
        # "rtsp://supratim:supratim@192.168.1.3:554/stream1",
        # "rtsp://your_second_rtsp_stream_here",
        # add more if needed
    ]
    main(rtsp_links)
