# Video Encryption & IPFS Distribution System

## Project Overview
This system captures RTSP video streams, encrypts frames (AES for I-frames, ChaCha20 for P/B-frames), uploads encrypted chunks to IPFS, and provides decryption capabilities to retrieve and view video chunks using IPFS hashes. It includes key management, encryption/decryption logic, and IPFS integration.

---

## File Structure & Descriptions
| File/Directory               | Purpose                                                                                     |
|------------------------------|---------------------------------------------------------------------------------------------|
| `main.py`                    | Core script for RTSP stream capture, frame encryption, chunking, and IPFS upload.           |
| `ipfs_decrypt_viewer.py`     | Decryption tool to download IPFS chunks, decrypt frames, and display video.                 |
| `key_manager.py`             | Generates and manages AES/ChaCha20 encryption keys (stored in `encryption_keys.json`).       |
| `encryption_keys.json`       | Secure storage for encryption keys (**never commit to version control**).                   |
| `ipfs_hashes.txt`            | Logs IPFS CIDs of uploaded chunks for reference.                                            |
| `debug.log`                  | Detailed logs of stream processing, encryption, and uploads.                               |
| `encrypted_chunks/`          | Local directory for temporary storage of encrypted chunks before IPFS upload.               |
| `requirements.txt`           | Python dependencies for easy installation.                                                  |
| `test.py` (optional)         | Placeholder for testing individual components (e.g., encryption/decryption logic).          |
| `venv/`                      | Virtual environment (auto-created; contains isolated dependencies).                         |

---

## Setup Instructions
### Prerequisites
- Python 3.10+ 
- IPFS Desktop or CLI (local node running on `http://127.0.0.1:5001`)
- RTSP camera stream (or test stream) 
- Windows PowerShell (or terminal)

### Step 1: Install Dependencies
```powershell
# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required packages
pip install -r requirements.txt
```

### Step 2: Configure IPFS
1. Download and install [IPFS Desktop](https://docs.ipfs.tech/install/ipfs-desktop/) 
2. Start the IPFS daemon (runs on `http://127.0.0.1:5001` by default)
3. Verify IPFS API access: 
   ```powershell
   curl http://127.0.0.1:5001/api/v0/id
   ```
   (Should return node identity if running)

### Step 3: Generate Encryption Keys
Run `key_manager.py` to create `encryption_keys.json`:
```powershell
python key_manager.py
```
- Keys are stored securely in `encryption_keys.json` (AES-256 and ChaCha20-256).
- **Critical**: Back up this file; losing it will prevent decryption.

---

## Upload Logic (Encryption Workflow)
### Step 1: Configure RTSP Streams
Edit `main.py` to add your RTSP stream URLs in the `rtsp_links` list:
```python
# In main.py (line ~150)
if __name__ == "__main__":
    rtsp_links = [
        "rtsp://your-camera-username:password@192.168.1.3:554/stream1",  # Replace with your stream
        # Add additional streams here
    ]
    main(rtsp_links)
```

### Step 2: Start Encryption & Upload
Run `main.py` to begin capturing, encrypting, and uploading:
```powershell
python main.py
```
#### What Happens:
- Frames are captured from RTSP streams.
- I-frames (every 60th frame) are encrypted with AES-EAX; P/B-frames with ChaCha20.
- Encrypted frames are chunked into 5-minute segments (configurable via `CHUNK_DURATION`).
- Chunks are saved locally to `encrypted_chunks/` and uploaded to IPFS.
- IPFS CIDs are logged to `ipfs_hashes.txt`.

### Step 3: Monitor Progress
- Check `debug.log` for real-time updates (e.g., `[2025-10-17 03:59:11] ✅ Uploaded stream0_chunk0.bin → CID: QmbMqCWhTE7DSdnRMmcggUf5Bp9gUeGLjPFWbiMxc5FrXw`).
- Verify chunks in IPFS: Use the CID in `ipfs_hashes.txt` to check via [IPFS Gateway](http://127.0.0.1:8080/ipfs/<CID>).

---

## Decryption Testing Workflow
### Step 1: Retrieve an IPFS CID
Use a CID from `ipfs_hashes.txt` (e.g., `QmbMqCWhTE7DSdnRMmcggUf5Bp9gUeGLjPFWbiMxc5FrXw`).

### Step 2: Decrypt and View the Chunk
Run `ipfs_decrypt_viewer.py` and follow the prompts:
```powershell
python ipfs_decrypt_viewer.py
```
#### What Happens:
1. The script downloads the encrypted chunk from IPFS using the CID.
2. It reads the encryption keys from `encryption_keys.json`.
3. Frames are decrypted using AES/ChaCha20 (based on header flags) and decoded as JPEG.
4. The video is displayed in a window (press `q` to exit).

### Troubleshooting Decryption
- **"MAC check failed"**: Ensure `encryption_keys.json` matches the one used for encryption.
- **"No frames extracted"**: Verify the IPFS CID is valid and the chunk was uploaded correctly.
- **IPFS download errors**: Confirm the IPFS daemon is running (`http://127.0.0.1:5001`).

---

## Key Notes
- **Security**: Never share `encryption_keys.json` or commit it to version control.
- **Scalability**: Adjust `CHUNK_DURATION` in `main.py` to change chunk size (default: 5 minutes).
- **Logging**: Use `debug.log` to diagnose stream capture or upload issues.
- **RTSP Issues**: Test RTSP streams with `ffplay` or VLC first to ensure connectivity.

---

## Maintenance
- **Update Dependencies**: Run `pip freeze > requirements.txt` after adding new packages.
- **Backup Keys**: Regularly back up `encryption_keys.json` to a secure location.
- **IPFS Peering**: For public access, ensure your IPFS node is peered with the network.