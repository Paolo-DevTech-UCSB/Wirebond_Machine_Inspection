import cv2
import numpy as np

# Load image
img = cv2.imread(r"C:\Users\hep\Desktop\Basic Inspector\Input Module Folders\320MHF2TDSB0108\1_13_14.png")

# Crop off the top 350 pixels
# Remove top 350, left 150, right 150
crop = img[350:, 150:-150]


# Convert to HSV
hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

# ---------------------------------------------------------
# GREEN RANGE (expanded: dark → bright)
# ---------------------------------------------------------
# Dark green
green_lower1 = np.array([35, 40, 20])
green_upper1 = np.array([85, 255, 150])

# Bright green
green_lower2 = np.array([35, 80, 150])
green_upper2 = np.array([85, 255, 255])

green_mask1 = cv2.inRange(hsv, green_lower1, green_upper1)
green_mask2 = cv2.inRange(hsv, green_lower2, green_upper2)
green_mask = cv2.bitwise_or(green_mask1, green_mask2)

# ---------------------------------------------------------
# GOLD RANGE (expanded: bright → deep gold)
# ---------------------------------------------------------
# Bright gold (yellowish)
gold_lower1 = np.array([15, 120, 150])
gold_upper1 = np.array([35, 255, 255])

# Deeper gold (more orange)
gold_lower2 = np.array([10, 100, 120])
gold_upper2 = np.array([25, 255, 255])

gold_mask1 = cv2.inRange(hsv, gold_lower1, gold_upper1)
gold_mask2 = cv2.inRange(hsv, gold_lower2, gold_upper2)
gold_mask = cv2.bitwise_or(gold_mask1, gold_mask2)

# ---------------------------------------------------------
# Combine green + gold → invert → keep everything else
# ---------------------------------------------------------
excluded_mask = cv2.bitwise_or(green_mask, gold_mask)
keep_mask = cv2.bitwise_not(excluded_mask)

# Clean noise
keep_mask = cv2.medianBlur(keep_mask, 5)

# ---------------------------------------------------------
# Compute center of mass
# ---------------------------------------------------------
M = cv2.moments(keep_mask)

if M["m00"] != 0:
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    print("Center of Mass (NOT green/gold):", (cx, cy))

    cv2.circle(crop, (cx, cy), 6, (0, 0, 255), -1)
else:
    print("No valid pixels found")

cv2.imshow("Crop", crop)
cv2.imshow("Mask (NOT green/gold)", keep_mask)
cv2.waitKey(0)
cv2.destroyAllWindows()

