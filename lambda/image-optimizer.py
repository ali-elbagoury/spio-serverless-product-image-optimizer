import os
import boto3
import cv2
import numpy as np
import tempfile
import time
import zipfile


MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds
s3 = boto3.client("s3")

UPLOAD_BUCKET = "spio-images-uploads"
OUTPUT_BUCKET = "spio-images-processing"

def find_reference_for_batch(batch_id):
    response = s3.list_objects_v2(
        Bucket=UPLOAD_BUCKET,
        Prefix=batch_id  # look for objects starting with batch_id
    )
    if "Contents" not in response:
        return None
    for obj in response["Contents"]:
        key = obj["Key"]
        if "reference" in key:
            return key
    return None

def download_from_s3(bucket, key, local_path):
    print(f"[DEBUG] Downloading s3://{bucket}/{key} → {local_path}")
    s3.download_file(bucket, key, local_path)
    return local_path

def upload_to_s3(local_path, bucket, key):
    print(f"[DEBUG] Uploading {local_path} → s3://{bucket}/{key}")
    s3.upload_file(local_path, bucket, key)

def detect_object(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))
    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise RuntimeError("No contour found.")
    c = max(contours, key=cv2.contourArea)
    rr = cv2.minAreaRect(c)
    (cx, cy), (w_rot, h_rot), angle = rr
    diag = (w_rot**2 + h_rot**2) ** 0.5

    M = cv2.moments(c)
    if M["m00"] != 0:
        cx = int(M["m10"]/M["m00"])
        cy = int(M["m01"]/M["m00"])
    else:
        cx, cy = 0, 0

    return diag, c, (cx, cy)

# 👇 Lambda entrypoint
def lambda_handler(event, context):
    print(f"[DEBUG] Event received: {event}")

    def find_reference_for_batch(batch_id):
        """Search uploads bucket for reference image of a batch."""
        try:
            response = s3.list_objects_v2(
                Bucket=UPLOAD_BUCKET,
                Prefix=batch_id
            )
            for obj in response.get("Contents", []):
                key = obj["Key"]
                if "reference" in key:
                    return key
        except Exception as e:
            print(f"[ERROR] Failed to list objects for batch {batch_id}: {e}")
        return None

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        print(f"[DEBUG] Processing file: s3://{bucket}/{key}")

        filename = os.path.basename(key)
        parts = filename.split("-")
        batch_id = parts[0] if parts else "unknown_batch"
        print(f"[DEBUG] Batch ID: {batch_id}")

        tmp_input = os.path.join(tempfile.gettempdir(), filename)
        try:
            download_from_s3(bucket, key, tmp_input)
        except Exception as e:
            print(f"[ERROR] Failed to download {key}: {e}")
            continue

        if "reference" in filename:
            try:
                upload_to_s3(tmp_input, OUTPUT_BUCKET, f"{batch_id}/reference.png")
                print(f"[DEBUG] Stored reference for batch {batch_id}")
            except Exception as e:
                print(f"[ERROR] Failed to upload reference for {batch_id}: {e}")

        elif "product" in filename:
            # Dynamically find reference file in uploads
            ref_key = find_reference_for_batch(batch_id)
            if not ref_key:
                print(f"[WARN] No reference found for batch {batch_id}, skipping batch.")
                continue
        
            ref_path = os.path.join(tempfile.gettempdir(), f"{batch_id}_ref.png")
            try:
                download_from_s3(UPLOAD_BUCKET, ref_key, ref_path)
                print(f"[DEBUG] Reference downloaded for batch {batch_id}")
            except Exception as e:
                print(f"[ERROR] Failed to download reference {ref_key}: {e}")
                continue
        
            try:
                ref = cv2.imread(ref_path)
                if ref is None:
                    raise RuntimeError("Reference image could not be read")
                ref_h, ref_w = ref.shape[:2]
                ref_diag, _, ref_centroid = detect_object(ref)
            except Exception as e:
                print(f"[ERROR] Failed to process reference for batch {batch_id}: {e}")
                continue
        
            # 🔹 Process all product images in this batch
            response = s3.list_objects_v2(Bucket=UPLOAD_BUCKET, Prefix=batch_id)
            product_keys = [
                obj["Key"] for obj in response.get("Contents", [])
                if "product" in obj["Key"]
            ]
        
            # Create a temporary zip file
            zip_path = os.path.join(tempfile.gettempdir(), f"{batch_id}_scaled.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for prod_key in product_keys:
                    prod_filename = os.path.basename(prod_key)
                    tmp_prod_path = os.path.join(tempfile.gettempdir(), prod_filename)
                    try:
                        download_from_s3(UPLOAD_BUCKET, prod_key, tmp_prod_path)
                        print(f"[DEBUG] Downloaded product {prod_filename} for batch {batch_id}")
                    except Exception as e:
                        print(f"[ERROR] Failed to download {prod_key}: {e}")
                        continue
        
                    try:
                        product = cv2.imread(tmp_prod_path)
                        if product is None:
                            raise RuntimeError("Product image could not be read")
        
                        prod_diag, _, prod_centroid = detect_object(product)
                        scale_factor = ref_diag / prod_diag
                        new_w = int(round(product.shape[1] * scale_factor))
                        new_h = int(round(product.shape[0] * scale_factor))
                        resized = cv2.resize(product, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        
                        scaled_centroid = (int(prod_centroid[0] * scale_factor),
                                           int(prod_centroid[1] * scale_factor))
        
                        canvas = np.full((ref_h, ref_w, 3), 255, np.uint8)
                        shift_x = ref_centroid[0] - scaled_centroid[0]
                        shift_y = ref_centroid[1] - scaled_centroid[1]
        
                        x0, y0 = shift_x, shift_y
                        x1, y1 = max(0, x0), max(0, y0)
                        x2, y2 = min(ref_w, x0 + resized.shape[1]), min(ref_h, y0 + resized.shape[0])
                        roi_x1, roi_y1 = max(0, -x0), max(0, -y0)
                        roi_x2, roi_y2 = roi_x1 + (x2 - x1), roi_y1 + (y2 - y1)
        
                        canvas[y1:y2, x1:x2] = resized[roi_y1:roi_y2, roi_x1:roi_x2]
        
                        # Save the scaled product temporarily
                        scaled_filename = f"scaled_{prod_filename}"
                        tmp_scaled_path = os.path.join(tempfile.gettempdir(), scaled_filename)
                        cv2.imwrite(tmp_scaled_path, canvas)
        
                        # Add to zip
                        zipf.write(tmp_scaled_path, arcname=scaled_filename)
                        print(f"[DEBUG] Added {scaled_filename} to batch zip {batch_id}")
        
                    except Exception as e:
                        print(f"[ERROR] Failed to process product {prod_filename}: {e}")
        
            # Upload the zip
            try:
                upload_to_s3(zip_path, OUTPUT_BUCKET, f"{batch_id}/scaled/{batch_id}_scaled.zip")
                print(f"[DEBUG] Uploaded zipped scaled products for batch {batch_id}")
            except Exception as e:
                print(f"[ERROR] Failed to upload zip for batch {batch_id}: {e}")
        