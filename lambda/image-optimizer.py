import cv2
import numpy as np
import matplotlib.pyplot as plt

# --- load images ---
ref = cv2.imread("reference.png")
product = cv2.imread("small.png")
ref_h, ref_w = ref.shape[:2]

def detect_object(img):
    """Return (diag, contour, centroid) for main object."""
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

    # centroid
    M = cv2.moments(c)
    if M["m00"] != 0:
        cx = int(M["m10"]/M["m00"])
        cy = int(M["m01"]/M["m00"])
    else:
        cx, cy = 0, 0

    return diag, c, (cx, cy)

# --- measure object sizes + positions ---
ref_diag, ref_contour, ref_centroid = detect_object(ref)
prod_diag, prod_contour, prod_centroid = detect_object(product)

print("Reference diag:", ref_diag, "px")
print("Product diag:", prod_diag, "px")

# --- compute scale factor ---
scale_factor = ref_diag / prod_diag
print("Scale factor:", scale_factor)

new_w = int(round(product.shape[1] * scale_factor))
new_h = int(round(product.shape[0] * scale_factor))
resized = cv2.resize(product, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

# --- recalc centroid of scaled product ---
# scale centroid coordinates as well
scaled_centroid = (int(prod_centroid[0] * scale_factor),
                   int(prod_centroid[1] * scale_factor))

# --- align product centroid to reference centroid ---
canvas = np.full((ref_h, ref_w, 3), 255, np.uint8)

# shift calculation
shift_x = ref_centroid[0] - scaled_centroid[0]
shift_y = ref_centroid[1] - scaled_centroid[1]

x0 = shift_x
y0 = shift_y

# paste product carefully with boundaries
x1 = max(0, x0)
y1 = max(0, y0)
x2 = min(ref_w, x0 + resized.shape[1])
y2 = min(ref_h, y0 + resized.shape[0])

roi_x1 = max(0, -x0)
roi_y1 = max(0, -y0)
roi_x2 = roi_x1 + (x2 - x1)
roi_y2 = roi_y1 + (y2 - y1)

canvas[y1:y2, x1:x2] = resized[roi_y1:roi_y2, roi_x1:roi_x2]

final_img = canvas

cv2.imwrite("scaled_product.jpg", final_img)

# --- visualize ---
vis_ref = ref.copy()
cv2.drawContours(vis_ref, [ref_contour], -1, (0, 255, 0), 3)
cv2.circle(vis_ref, ref_centroid, 6, (0, 0, 255), -1)

vis_prod = product.copy()
cv2.drawContours(vis_prod, [prod_contour], -1, (0, 255, 0), 3)
cv2.circle(vis_prod, prod_centroid, 6, (0, 0, 255), -1)

plt.figure(figsize=(15,5))
plt.subplot(1,3,1)
plt.imshow(cv2.cvtColor(vis_ref, cv2.COLOR_BGR2RGB))
plt.title("Reference with centroid")
plt.axis("off")

plt.subplot(1,3,2)
plt.imshow(cv2.cvtColor(vis_prod, cv2.COLOR_BGR2RGB))
plt.title("Original product with centroid")
plt.axis("off")

plt.subplot(1,3,3)
plt.imshow(cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB))
plt.title("Scaled + aligned product")
plt.axis("off")
plt.show()
