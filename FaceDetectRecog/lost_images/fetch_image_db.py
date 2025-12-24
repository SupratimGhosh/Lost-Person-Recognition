import os
import sys
import mimetypes
from pathlib import Path
from bson.binary import Binary
from pymongo import MongoClient

# try to import python-magic (libmagic). It's optional.
try:
    import magic  # python-magic
    _HAS_MAGIC = True
except Exception:
    _HAS_MAGIC = False

# ============ CONFIG =============
MONGODB_URI = "YOUR URI"   # <-- replace with your URI (or set via env var)
DB_NAME     = "YOUR DB NAME"                   # change to your DB name
COLL_NAME   = "YOUR COLLECTION NAME"         # change to your collection name
OUTPUT_DIR  = "exported_images"
# Optional query filter to limit which docs to export
QUERY = {"status": "active"}  # e.g. {"personName": "Aman Verma"} or {} for all
# ==================================

def detect_image_ext_from_header(data_bytes):
    """
    Fast header-based detection for common image formats.
    Returns extension including dot (e.g. ".jpg") or None.
    """
    if not data_bytes or len(data_bytes) < 12:
        return None

    b = data_bytes
    # JPEG (starts with 0xFFD8)
    if b[0:2] == b'\xff\xd8':
        return ".jpg"
    # PNG
    if b[0:8] == b'\x89PNG\r\n\x1a\n':
        return ".png"
    # GIF (GIF87a or GIF89a)
    if b[0:6] in (b'GIF87a', b'GIF89a'):
        return ".gif"
    # WEBP (RIFF....WEBP)
    if b[0:4] == b'RIFF' and b[8:12] == b'WEBP':
        return ".webp"
    # BMP (BM)
    if b[0:2] == b'BM':
        return ".bmp"
    # TIFF (II* or MM*)
    if b[0:4] in (b'II*\x00', b'MM\x00*'):
        return ".tiff"
    # HEIC/HEIF - often starts with 'ftyp' box containing 'heic', 'heix', 'hevc' etc
    if b[4:8] == b'ftyp' and any(x in b[8:16] for x in (b'heic', b'heix', b'hevc', b'mif1', b'msf1')):
        return ".heic"
    return None

def guess_extension(content_type, data_bytes=None):
    """
    Return a sensible file extension for the content_type or by inspecting bytes.
    Preference order:
      1. explicit content_type (if present)
      2. python-magic (if available)
      3. header-based detection
      4. mimetypes.guess_extension
      5. fallback to .bin
    """
    # 1) use content_type if provided
    if content_type:
        content_type_lower = content_type.lower()
        # common explicit mappings
        if "jpeg" in content_type_lower or "jpg" in content_type_lower:
            return ".jpg"
        if "png" in content_type_lower:
            return ".png"
        if "gif" in content_type_lower:
            return ".gif"
        if "webp" in content_type_lower:
            return ".webp"
        if "bmp" in content_type_lower:
            return ".bmp"
        if "tiff" in content_type_lower or "tif" in content_type_lower:
            return ".tiff"
        # try generic mimetypes
        ext = mimetypes.guess_extension(content_type_lower)
        if ext:
            return ext

    # 2) try python-magic (libmagic)
    if _HAS_MAGIC and data_bytes:
        try:
            mime = magic.from_buffer(data_bytes, mime=True)
            if mime:
                ext = mimetypes.guess_extension(mime)
                if ext:
                    return ext
        except Exception:
            # ignore and fallback
            pass

    # 3) header-based detection
    if data_bytes:
        ext = detect_image_ext_from_header(data_bytes)
        if ext:
            return ext

    # 4) try to guess from bytes heuristics (as an extra attempt)
    # (we already covered common ones in header-based detection)
    # 5) fallback
    return ".bin"

def extract_image_bytes(photo_field):
    """
    Given a photo_field (which may be a dict with 'data' and 'contentType', or a raw Binary),
    return tuple (bytes, content_type or None).
    """
    # If it's already a Binary object
    if isinstance(photo_field, Binary):
        return bytes(photo_field), None

    # If it's a dict-like object
    try:
        photo_dict = dict(photo_field)
    except Exception:
        photo_dict = None

    if photo_dict is not None:
        # Try common keys
        data = photo_dict.get("data") or photo_dict.get("binary") or photo_dict.get("image") or photo_dict.get("img")
        content_type = photo_dict.get("contentType") or photo_dict.get("content_type") or photo_dict.get("type")

        if isinstance(data, Binary):
            return bytes(data), content_type
        # sometimes 'data' may be raw bytes already or base64 string
        if isinstance(data, (bytes, bytearray)):
            return bytes(data), content_type
        if isinstance(data, str):
            # if it's a base64 string (rare if stored via pymongo Binary), try decode
            import base64
            try:
                return base64.b64decode(data), content_type
            except Exception:
                pass

    # As a last resort, if it's bytes-like
    if isinstance(photo_field, (bytes, bytearray)):
        return bytes(photo_field), None

    # unknown format
    return None, None

def main():
    uri = MONGODB_URI.strip()
    if not uri or uri == "YOUR_MONGODB_URI_HERE":
        print("ERROR: Please set MONGODB_URI at top of script (or supply via environment). Exiting.")
        sys.exit(1)

    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    client = MongoClient(uri)
    db = client[DB_NAME]
    coll = db[COLL_NAME]

    cursor = coll.find(QUERY)
    total_saved = 0
    total_docs = 0

    for doc in cursor:
        total_docs += 1
        doc_id_str = str(doc.get("_id", total_docs))
        # Many schemas use 'photos' array — adapt as needed.
        photos = None
        if "photos" in doc:
            photos = doc.get("photos")
        elif "photo" in doc:
            photos = doc.get("photo")
        elif "image" in doc:
            photos = doc.get("image")

        # If field is single Binary or dict, wrap into list
        if photos is None:
            # fallback: maybe the image is stored directly at doc['data'] or doc['file']
            if "data" in doc:
                photos = [ {"data": doc.get("data"), "contentType": doc.get("contentType", None)} ]
            else:
                photos = []

        # Ensure list-like
        if not isinstance(photos, list):
            photos = [photos]

        for idx, p in enumerate(photos, start=1):
            img_bytes, content_type = extract_image_bytes(p)
            if img_bytes is None:
                # try checking inner structure if p is dict-like and contains nested 'data'
                print(f"[WARN] doc {doc_id_str} photo index {idx}: could not extract bytes, skipping.")
                continue

            ext = guess_extension(content_type, img_bytes)
            filename = f"{doc_id_str}_{idx}{ext}"
            filepath = out_dir / filename

            try:
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                total_saved += 1
                print(f"[OK] Saved: {filepath} (contentType={content_type})")
            except Exception as e:
                print(f"[ERROR] Could not write file {filepath}: {e}")

    print("==== Summary ====")
    print(f"Docs scanned: {total_docs}")
    print(f"Images saved: {total_saved}")
    client.close()

if __name__ == "__main__":
    main()
