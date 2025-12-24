import cv2
import os
import numpy as np
import requests
import time
from Crypto.Cipher import AES
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.backends import default_backend
from key_manager import get_binary_keys

# IPFS Gateway URL - you can use a public gateway or your local node
IPFS_GATEWAY = "http://127.0.0.1:8080/ipfs/"
IPFS_API_URL = "http://127.0.0.1:5001/api/v0"
TEMP_DIR = "temp_downloads"

def download_from_ipfs(ipfs_hash):
    """Download a file from IPFS using its hash"""
    print(f"Downloading file with hash: {ipfs_hash}")
    
    # Create temp directory if it doesn't exist
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Construct the download path
    download_path = os.path.join(TEMP_DIR, f"{ipfs_hash}.bin")
    
    try:
        # Try using the IPFS API first (if local node is running)
        try:
            response = requests.post(
                f"{IPFS_API_URL}/cat", 
                params={"arg": ipfs_hash},
                timeout=10
            )
            if response.status_code == 200:
                with open(download_path, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded file using IPFS API to {download_path}")
                return download_path
        except requests.exceptions.RequestException:
            print("IPFS API not available, trying gateway...")
        
        # If API fails, try using the gateway
        response = requests.get(f"{IPFS_GATEWAY}{ipfs_hash}", timeout=30)
        if response.status_code == 200:
            with open(download_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded file using IPFS gateway to {download_path}")
            return download_path
        else:
            print(f"Failed to download: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error downloading from IPFS: {e}")
        return None

def aes_decrypt(encrypted_data, key):
    """Decrypt data that was encrypted with AES-EAX mode"""
    # Extract nonce (16 bytes), tag (16 bytes), and ciphertext
    nonce = encrypted_data[:16]
    tag = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]
    
    # Create cipher object
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    
    # Decrypt and verify
    try:
        data = cipher.decrypt_and_verify(ciphertext, tag)
        return data
    except ValueError as e:
        print(f"AES decryption error: {e}")
        return None

def chacha20_decrypt(encrypted_data, key):
    """Decrypt data that was encrypted with ChaCha20"""
    # Extract nonce (16 bytes) and ciphertext
    nonce = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    
    # Create cipher object
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
    decryptor = cipher.decryptor()
    
    # Decrypt
    try:
        return decryptor.update(ciphertext)
    except Exception as e:
        print(f"ChaCha20 decryption error: {e}")
        return None

def process_encrypted_chunk(file_path):
    """Process an encrypted chunk file and extract video frames"""
    print(f"Processing encrypted chunk: {file_path}")
    
    # Get encryption keys
    aes_key, chacha_key = get_binary_keys()
    
    # Read encrypted data
    with open(file_path, "rb") as f:
        encrypted_data = f.read()
    
    # Process the encrypted data to extract frames
    import struct
    frames = []
    position = 0
    frame_count = 0
    
    while position < len(encrypted_data):
        if position + 5 > len(encrypted_data):
            break  # Not enough data for header
        
        # Read header: 1 byte type + 4 bytes length
        enc_type, length = struct.unpack('>BI', encrypted_data[position:position+5])
        position += 5
        
        if position + length > len(encrypted_data):
            print(f"Warning: Incomplete frame at position {position}, skipping.")
            break
        
        frame_data = encrypted_data[position:position+length]
        position += length
        
        # Decrypt based on type
        if enc_type == 1:  # AES
            decrypted = aes_decrypt(frame_data, aes_key)
        elif enc_type == 0:  # ChaCha20
            decrypted = chacha20_decrypt(frame_data, chacha_key)
        else:
            print(f"Unknown encryption type {enc_type}, skipping frame.")
            continue
        
        if decrypted:
            # Try to decode as JPEG
            nparr = np.frombuffer(decrypted, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None and img.size > 0:
                frames.append(img)
                frame_count += 1
            else:
                print(f"Failed to decode frame {frame_count}")
        else:
            print(f"Decryption failed for frame {frame_count}")
    
    print(f"Extracted {frame_count} frames from the encrypted chunk")
    return frames

def display_video(frames, fps=30):
    """Display a sequence of frames as a video"""
    if not frames:
        print("No frames to display")
        return
    
    print(f"Displaying {len(frames)} frames at {fps} FPS")
    
    # Create a window
    window_name = "Decrypted Video"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # Display frames
    for i, frame in enumerate(frames):
        cv2.imshow(window_name, frame)
        key = cv2.waitKey(int(1000/fps))  # Wait for the specified FPS duration
        
        # Press 'q' or ESC to exit
        if key == ord('q') or key == 27:
            break
    
    cv2.destroyAllWindows()

def main():
    print("===== IPFS Video Decryption and Viewer =====")
    
    # Get IPFS hash from user
    ipfs_hash = input("Enter the IPFS hash of the encrypted video chunk: ")
    
    # Download the file from IPFS
    downloaded_file = download_from_ipfs(ipfs_hash)
    if not downloaded_file:
        print("Failed to download the file from IPFS. Exiting.")
        return
    
    # Process the encrypted chunk
    frames = process_encrypted_chunk(downloaded_file)
    
    # Display the video
    if frames:
        fps = int(input("Enter playback FPS (default: 30): ") or "30")
        display_video(frames, fps)
    else:
        print("No frames could be extracted from the encrypted chunk.")

if __name__ == "__main__":
    main()