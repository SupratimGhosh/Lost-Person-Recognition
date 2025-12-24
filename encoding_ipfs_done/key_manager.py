import os
import base64
import json
from pathlib import Path

# File to store encryption keys
KEYS_FILE = "encryption_keys.json"

def generate_keys():
    """Generate random keys for AES and ChaCha20 encryption"""
    aes_key = os.urandom(32)  # 256-bit key for AES
    chacha_key = os.urandom(32)  # 256-bit key for ChaCha20
    
    # Convert binary keys to base64 for storage
    keys = {
        "AES_KEY": base64.b64encode(aes_key).decode('utf-8'),
        "CHACHA_KEY": base64.b64encode(chacha_key).decode('utf-8')
    }
    
    # Save keys to file
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f)
    
    print(f"Generated new encryption keys and saved to {KEYS_FILE}")
    return keys

def load_keys():
    """Load encryption keys from file or generate new ones if file doesn't exist"""
    if not Path(KEYS_FILE).exists():
        return generate_keys()
    
    try:
        with open(KEYS_FILE, 'r') as f:
            keys = json.load(f)
        print(f"Loaded encryption keys from {KEYS_FILE}")
        return keys
    except Exception as e:
        print(f"Error loading keys: {e}. Generating new keys.")
        return generate_keys()

def get_binary_keys():
    """Get binary keys for use in encryption/decryption"""
    keys = load_keys()
    aes_key = base64.b64decode(keys["AES_KEY"])
    chacha_key = base64.b64decode(keys["CHACHA_KEY"])
    return aes_key, chacha_key

if __name__ == "__main__":
    # Generate new keys when run directly
    keys = generate_keys()
    print("New encryption keys generated:")
    print(f"AES_KEY: {keys['AES_KEY'][:10]}... (truncated)")
    print(f"CHACHA_KEY: {keys['CHACHA_KEY'][:10]}... (truncated)")