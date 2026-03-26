from PIL import Image, ImageDraw
import os
import numpy as np
import matplotlib.pyplot as plt
from wb_config import RAW_DIR

#--------------------Cropper---------------------------

def Img_Crop(Image, X_off, Y_off, Width, Height, Details = False):
    cropped_img = Image.crop((X_off + 0 , Y_off + 0, X_off + Width , Y_off + Height))
    if Details: cropped_img.show()
    cropped_img = cropped_img.convert("RGB")
    return cropped_img

#--------------------Loader------------------------------

def Load_Img(RAW_DIR, Current_Module, Image_Name):
    img_path = os.path.join(RAW_DIR, Current_Module, Image_Name)
    try:
        img = Image.open(img_path)
        img.load()  # Force loading the image to catch any issues early
        return img
    except Exception as e:
        print(f"[SKIP] Cannot open image {img_path}: {e}")
        return None
    
#--------------------Color Range Helpers----------------------
def is_sensor_color(r, g, b):
    return (60 <= r <= 170) and (110 <= g <= 220) and (140 <= b <= 255)


def is_gold_color(r, g, b):
    return (190 <= r <= 255) and (205 <= g <= 255) and (155 <= b <= 230)

#--------------------COM Helpers --------------------------------

def compute_sensor_com(img):
        
        W, H = img.size
        pix = img.load()

        sum_x = 0
        sum_y = 0
        count = 0

        for y in range(H):
            for x in range(W):
                r, g, b = pix[x, y]
                if is_sensor_color(r, g, b):
                    sum_x += x
                    sum_y += y
                    count += 1

        if count == 0:
            return None, None

        return sum_x / count, sum_y / count, count

def compute_darks_com(img):
    make_mask=True
    W, H = img.size
    pix = img.load()

    sum_x = 0
    sum_y = 0
    count = 0

    # Optional mask image
    mask_img = Image.new("RGB", (W, H), (0, 0, 0))
    mask_pix = mask_img.load() if make_mask else None
    

    for y in range(H):
        for x in range(W):
            r, g, b = pix[x, y]
            if r < 20 and g < 30 and b < 100:
                sum_x += x
                sum_y += y
                count += 1

                if make_mask:
                    mask_pix[x, y] = (255, 255, 255)   # white pixel

    if count == 0:
        return None, None, None

    x_center = sum_x / count
    y_center = sum_y / count

    #mask_img.show()

    return x_center, y_center, count

def compute_combined_com(img):
    W, H = img.size
    pix = img.load()

    sum_x = 0
    sum_y = 0
    count = 0

    for y in range(H):
        for x in range(W):
            r, g, b = pix[x, y]

            # Combined condition:
            #   - sensor color OR dark pixel
            if is_sensor_color(r, g, b) or (r < 20 and g < 30 and b < 100):
                sum_x += x
                sum_y += y
                count += 1

    if count == 0:
        return None, None, None

    return sum_x / count, sum_y / count, count

def compute_gold_com(img):
        
        W, H = img.size
        pix = img.load()

        sum_x = 0
        sum_y = 0
        count = 0

        for y in range(H):
            for x in range(W):
                r, g, b = pix[x, y]
                if is_gold_color(r, g, b):
                    sum_x += x
                    sum_y += y
                    count += 1

        if count == 0:
            return None, None

        return sum_x / count, sum_y / count, count
#-------------------------Color COM Analyzer-------------------

def Analyze_Img_Colors(img):
    def compute_com(pixels, width, height, condition_fn):
        width, height = img.size
        pixels = img.load()
        sum_x = 0
        sum_y = 0
        count = 0

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                if condition_fn(r, g, b):
                    sum_x += x
                    sum_y += y
                    count += 1

        if count == 0:
            return None  # no pixels matched

        return sum_x / count, sum_y / count

    com_conditions = {
        "strict_white": lambda r, g, b: r > 230 and g > 230 and b > 230,
        "loose_white":  lambda r, g, b: r > 150 and g > 150 and b > 150,
        "black":        lambda r, g, b: (r + g + b) < 100,
        "mid_gray":     lambda r, g, b: 100 < (r + g + b) < 300,
        "red_bias":     lambda r, g, b: r > g and r > b,
        "green_bias":   lambda r, g, b: g > r and g > b,
        "blue_bias":    lambda r, g, b: b > r and b > g,
    }

    for name, fn in com_conditions.items():
        result = compute_com(pixels, width, height, fn)
        if result is not None:
            com_results[name] = result
    
        width, height = img.size
        pixels = img.load()
        sum_x = 0
        sum_y = 0
        count = 0

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                if condition_fn(r, g, b):
                    sum_x += x
                    sum_y += y
                    count += 1

        if count == 0:
            return None  # no pixels matched

        return sum_x / count, sum_y / count

    com_conditions = {
        "strict_white": lambda r, g, b: r > 230 and g > 230 and b > 230,
        "loose_white":  lambda r, g, b: r > 150 and g > 150 and b > 150,
        "black":        lambda r, g, b: (r + g + b) < 100,
        "mid_gray":     lambda r, g, b: 100 < (r + g + b) < 300,
        "red_bias":     lambda r, g, b: r > g and r > b,
        "green_bias":   lambda r, g, b: g > r and g > b,
        "blue_bias":    lambda r, g, b: b > r and b > g,
    }

    pixels = cropped_img.load()
    width, height = cropped_img.size

    com_results = {}

    for name, fn in com_conditions.items():
        result = compute_com(pixels, width, height, fn)
        if result is not None:
            com_results[name] = result

    # Add true image center for reference
    com_results["image_center"] = (width / 2, height / 2)
    draw = ImageDraw.Draw(cropped_img)

    colors = {
        "image_center": (255, 255, 255),  # white dot
        "strict_white": (255, 0, 0),
        "loose_white":  (255, 128, 0),
        "black":        (0, 255, 0),
        "mid_gray":     (0, 255, 255),
        "red_bias":     (255, 0, 255),
        "green_bias":   (0, 200, 0),
        "blue_bias":    (0, 128, 255),
    }

    for name, (cx, cy) in com_results.items():
        color = colors.get(name, (255, 255, 255))
        r = 5

        # Draw dot
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=color)

        # Draw label with slight offset
        draw.text((cx + 8, cy - 8), name, fill=color)

    cropped_img.show()

#-------------------------Image Classification-------------------------

def Classify_Img(Img, X_off, Y_off):
    
    # ---------------------------------------------------------
    # 1. CAL-DOT FILTERING + DEBUG MASK
    # ---------------------------------------------------------
    black_count = 0
    caldot_mask = []
    Hole_Type = "Default"

    def compute_com_from_mask(mask, W, H):
        sum_x = 0
        sum_y = 0
        count = 0

        idx = 0
        for y in range(H):
            for x in range(W):
                r, g, b = mask[idx]
                if r > 200 and g > 200 and b > 200:   # white pixel
                    sum_x += x
                    sum_y += y
                    count += 1
                idx += 1

        if count == 0:
            return None, None

        return sum_x / count, sum_y / count

    W, H = Img.size

    d = Img.getdata()
    for (r, g, b) in d:


        is_black = (r < 40 and g < 40 and b < 40)
        is_sensor = is_sensor_color(r, g, b)

        # COM mask includes black OR sensor
        if is_black or is_sensor:
            caldot_mask.append((255, 255, 255))
        else:
            caldot_mask.append((0, 0, 0))

        # Detection only counts black
        if is_black:
            black_count += 1

    black_count_THRESHOLD = round(47040 * 0.5)

    if black_count > black_count_THRESHOLD:
        print("Cal-dot detected — showing mask and cropped image...")

        # Build mask image
        mask_img = Image.new("RGB", (W, H))
        mask_img.putdata(caldot_mask)

        # --- Compute COM of cal-dot mask ---
        com_x, com_y = compute_com_from_mask(caldot_mask, W, H)
        Hole_Type = "Cal-dot"




    gx = gy = None
    sx = sy = None

    # ---------------------------------------------------------
    # 2. GUARD-RING FILTERING + DEBUG MASK
    # ---------------------------------------------------------
    gold_count = 0
    guard_mask = []
    gold_mask = []
    silicon_mask = []

    for (r, g, b) in d:

        # Your gold definition (keep or tighten as needed)
        is_gold = (190 <= r <= 255 and 205 <= g <= 255 and 155 <= b <= 230)

        # Your existing silicon detection
        is_sensor = is_sensor_color(r, g, b)

        # Build masks
        if is_gold or is_sensor:
            guard_mask.append((255, 255, 255))
        else:
            guard_mask.append((0, 0, 0))

        # Separate masks for COM calculation
        gold_mask.append((255,255,255) if is_gold else (0,0,0))
        silicon_mask.append((255,255,255) if is_sensor else (0,0,0))

        if is_gold:
            gold_count += 1


    # --- Your existing threshold ---
    GUARD_RING_THRESHOLD = round(502650 * 0.4 * 0.1)

    if gold_count > GUARD_RING_THRESHOLD:

        # Compute COM of gold and silicon
        gold_com = compute_com_from_mask(gold_mask, W, H)
        silicon_com = compute_com_from_mask(silicon_mask, W, H)

        if gold_com and silicon_com:
            gx, gy = gold_com
            sx, sy = silicon_com

            # Distance between COMs
            dist = ((gx - sx)**2 + (gy - sy)**2)**0.5
            #print("Gold–Silicon COM distance:", dist)

            if 180 <= dist <= 320:
                print("Guard-ring confirmed by COM distance")

                mask_img = Image.new("RGB", (W, H))
                mask_img.putdata(guard_mask)
                draw = ImageDraw.Draw(mask_img)
                r = 8

                # Draw COM dots
                draw.ellipse((gx-r, gy-r, gx+r, gy+r), fill=(0,0,255))   # gold COM (blue)
                draw.ellipse((sx-r, sy-r, sx+r, sy+r), fill=(255,0,0))   # silicon COM (red)

                # 🔵 Draw the blue line between COMs
                draw.line((gx, gy, sx, sy), fill=(0, 0, 255), width=3)

                mask_img.show()
                #cropped_img.show()

                Hole_Type = "Guard-ring"


    return Hole_Type

#------------------------- Mercedes Detection Code ------------------------

"""def Detect_Merc_Center(Img, Details=False):
        width, height = Img.size()
        pixels = Img.load()
        loose_sum_x = 0
        loose_sum_y = 0
        loose_count = 0

        loose_mask = []

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]

                # LOOSE: include spokes + outer ring + bright areas
                if r > 150 and g > 150 and b > 150:
                    loose_mask.append((255, 255, 255))
                    loose_sum_x += x
                    loose_sum_y += y
                    loose_count += 1
                else:
                    loose_mask.append((0, 0, 0))

        # Compute loose COM
        if loose_count > 0:
            com_loose_x = loose_sum_x / loose_count
            com_loose_y = loose_sum_y / loose_count

        center_of_mass_x = com_loose_x
        center_of_mass_y = com_loose_y

        filtered_image_data = []
        green_list = []
        blue_list = []

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                R = ((x - com_loose_x)**2 + (y - com_loose_y)**2)**0.5

                if 45 < R < 60 and r == 255 and g == 255 and b == 255:
                    filtered_image_data.append((0, 255, 0))
                    green_list.append((x, y))
                elif 90 < R < 110 and r == 255 and g == 255 and b == 255:
                    filtered_image_data.append((0, 0, 255)) 
                    blue_list.append((x, y))
                elif r == 255 and g == 255 and b == 255:
                    filtered_image_data.append((255, 255, 255))
                else:
                    filtered_image_data.append((0, 0, 0))

        linear_Points_image = Image.new("RGB", Img.size)
        linear_Points_image.putdata(filtered_image_data)

        if Details: linear_Points_image.show()

        Rad_Green = []
        for point in green_list:
            x, y = point
            theta = np.arctan2(y - center_of_mass_y, x - center_of_mass_x)
            distance = ((x - center_of_mass_x)**2 + (y - center_of_mass_y)**2)**0.5
            Rad_Green.append((theta, distance))

        Rad_Blue = []
        for point in blue_list:
            x, y = point
            theta = np.arctan2(y - center_of_mass_y, x - center_of_mass_x)
            distance = ((x - center_of_mass_x)**2 + (y - center_of_mass_y)**2)**0.5
            Rad_Blue.append((theta, distance))  

        def sort_by_theta(points):
            list_low_pi = []
            list_mid_pi = []
            list_high_pi = []

            for theta, r in points:
                # normalize angle to [0, 2π)
                if theta < 0:
                    theta += 2*np.pi

                # Your old custom angular windows
                if 0 <= theta < np.pi*(1/3):
                    list_low_pi.append((theta, r))

                elif np.pi*(1/3) <= theta < np.pi*(2/3):
                    list_low_pi.append((theta, r))

                elif np.pi*(2/3) <= theta < np.pi:
                    list_mid_pi.append((theta, r))

                elif np.pi*(9/8) <= theta < np.pi*(4/3):
                    list_mid_pi.append((theta, r))

                elif np.pi*(4/3) <= theta < np.pi*(5/3):
                    list_high_pi.append((theta, r))

                elif np.pi*(5/3) <= theta < np.pi*(17/8):
                    list_high_pi.append((theta, r))

            return list_low_pi, list_mid_pi, list_high_pi
        low, mid, high = sort_by_theta(Rad_Blue)

        def list_avg(points):
            if len(points) == 0:
                return None, None

            sum_theta = 0
            sum_r = 0

            for theta, r in points:
                sum_theta += theta
                sum_r += r

            return sum_theta / len(points), sum_r / len(points)

        def list_to_point(points):
            if len(points) == 0:
                return None, None

            sx = 0
            sy = 0

            for theta, r in points:
                # Convert polar → Cartesian
                x = center_of_mass_x + r * np.cos(theta)
                y = center_of_mass_y + r * np.sin(theta)

                sx += x
                sy += y

            return sx / len(points), sy / len(points)

        lowTheta, lowR = list_avg(low)
        midTheta, midR = list_avg(mid) 
        highTheta, highR = list_avg(high)

        def safe_polar_to_cart(center_x, center_y, R, Theta, label, img=None):
            if R is None or Theta is None:
                print(f"[WARN] Missing {label} point group — R or Theta is None")

                return None, None

            return (
                center_x + R * np.cos(Theta),
                center_y + R * np.sin(Theta)
            )


        G1_x, G1_y = safe_polar_to_cart(center_of_mass_x, center_of_mass_y, lowR,  lowTheta,  "Green Low",  img)
        G2_x, G2_y = safe_polar_to_cart(center_of_mass_x, center_of_mass_y, midR,  midTheta,  "Green Mid",  img)
        G3_x, G3_y = safe_polar_to_cart(center_of_mass_x, center_of_mass_y, highR, highTheta, "Green High", img)

        low, mid, high = sort_by_theta(Rad_Green)
        lowTheta, lowR = list_avg(low)
        midTheta, midR = list_avg(mid) 
        highTheta, highR = list_avg(high)

        B1_x, B1_y = safe_polar_to_cart(center_of_mass_x, center_of_mass_y, lowR,  lowTheta,  "Blue Low",  img)
        B2_x, B2_y = safe_polar_to_cart(center_of_mass_x, center_of_mass_y, midR,  midTheta,  "Blue Mid",  img)
        B3_x, B3_y = safe_polar_to_cart(center_of_mass_x, center_of_mass_y, highR, highTheta, "Blue High", img)

        lines = []

        if None not in (G1_x, G1_y, B1_x, B1_y):
            lines.append(("L1", (G1_x, G1_y, B1_x, B1_y)))

        if None not in (G2_x, G2_y, B2_x, B2_y):
            lines.append(("L2", (G2_x, G2_y, B2_x, B2_y)))

        if None not in (G3_x, G3_y, B3_x, B3_y):
            lines.append(("L3", (G3_x, G3_y, B3_x, B3_y)))

        # -----------------------------------------
        # 1. Compute angles for each line
        # -----------------------------------------
        line_angles = {}   # name → angle

        for name, (Gx, Gy, Bx, By) in lines:
            dx = Bx - Gx
            dy = By - Gy
            angle = np.degrees(np.arctan2(dy, dx)) % 360
            line_angles[name] = angle

        # Only apply spacing check if we have 3 lines
        if len(lines) == 3:
            # -----------------------------------------
            # 2. Check 120° spacing
            # -----------------------------------------
            angles_sorted = sorted(line_angles.items(), key=lambda x: x[1])
            vals_sorted  = [a for _, a in angles_sorted]

            d1 = vals_sorted[1] - vals_sorted[0]
            d2 = vals_sorted[2] - vals_sorted[1]
            d3 = (vals_sorted[0] + 360) - vals_sorted[2]

            diffs = [d1, d2, d3]
            TOL = 8  # degrees tolerance

            valid_pattern = all(abs(d - 120) < TOL for d in diffs)

            # -----------------------------------------
            # 3. If invalid, remove the worst line
            # -----------------------------------------
            if not valid_pattern:
                errors = {}
                for name, angle in line_angles.items():
                    ideal_diffs = [
                        abs((angle - 0)   % 360),
                        abs((angle - 120) % 360),
                        abs((angle - 240) % 360)
                    ]
                    errors[name] = min(ideal_diffs)

                bad_line = max(errors, key=errors.get)
                print(f"[FILTER] Removing bad line: {bad_line}")
                lines = [item for item in lines if item[0] != bad_line]

        # Need at least two lines
        if len(lines) >= 2:
            # Use the first two valid lines
            (_, (Gx1, Gy1, Bx1, By1)) = lines[0]
            (_, (Gx2, Gy2, Bx2, By2)) = lines[1]

            # Helper to get (m, b) or vertical form
            def line_to_mb(x1, y1, x2, y2):
                dx = x2 - x1
                dy = y2 - y1
                if dx == 0:
                    return None, x1  # vertical: x = b
                m = dy / dx
                b = y1 - m * x1
                return m, b

            m1, b1 = line_to_mb(Gx1, Gy1, Bx1, By1)
            m2, b2 = line_to_mb(Gx2, Gy2, Bx2, By2)

            # Compute intersection robustly
            if m1 is None and m2 is None:
                # Both vertical → no intersection
                print("[WARN] Both lines vertical; cannot compute intersection.")
                X, Y = center_of_mass_x, center_of_mass_y

            elif m1 is None:
                # Line 1 vertical: x = b1
                X = b1
                Y = m2 * X + b2

            elif m2 is None:
                # Line 2 vertical: x = b2
                X = b2
                Y = m1 * X + b1

            else:
                # Non-vertical lines
                if abs(m1 - m2) < 1e-6:
                    print("[WARN] Lines nearly parallel; using COM as fallback.")
                    X, Y = center_of_mass_x, center_of_mass_y
                else:
                    X = (b2 - b1) / (m1 - m2)
                    Y = m1 * X + b1

            X_off = (X - center_of_mass_x)
            Y_off = (Y - center_of_mass_y)

            img = np.array(Img)

            ys = [y for y in [G1_y, G2_y, G3_y, B1_y, B2_y, B3_y] if y is not None]

            Cenroid_Count = len(ys)
            if Cenroid_Count >= 6:
                print("All 6 centroids found.")
            else:
                print(f"Only {Cenroid_Count} centroids found. Retrying with next brightness threshold...")

            if len(ys) == 0 or ys == [None, None, None, None, None, None]:
                print("[WARN] No valid centroids found.")

            middle = sum(ys) / len(ys)
            above_count = sum(1 for y in ys if y < middle)
            more_above = above_count > len(ys) / 2


            # True if more than half are above
            more_above = above_count > len(ys) / 2

            return X_off, Y_off, more_above"""

def Detect_Merc_Center(img, Details=False):
        width, height = img.size
        pixels = img.load()

        cx = width / 2
        cy = height / 2

        filtered_image_data = []
        green_list = []
        blue_list = []

        for y in range(height):
            for x in range(width):

                # 1. Threshold: dark → white, bright → black
                r, g, b = pixels[x, y]
                is_dark = (r < 150 and g < 150 and b < 150)

                # 2. Distance from center
                R = ((x - cx)**2 + (y - cy)**2)**0.5

                # 3. Green ring
                if 60 < R < 80 and is_dark:
                    filtered_image_data.append((0, 255, 0))
                    green_list.append((x, y))

                # 4. Blue ring
                elif 110 < R < 130 and is_dark:
                    filtered_image_data.append((0, 0, 255))
                    blue_list.append((x, y))

                # 5. White mask (dark pixels)
                elif is_dark:
                    filtered_image_data.append((255, 255, 255))

                # 6. Everything else black
                else:
                    filtered_image_data.append((0, 0, 0))

        # Build output image
        linear_Points_image = Image.new("RGB", img.size)
        linear_Points_image.putdata(filtered_image_data)

        if Details:
            linear_Points_image.show()
            input("Check_Output... Press enter.... ")



        Rad_Green = []
        for point in green_list:
            x, y = point
            theta = np.arctan2(y - cy, x - cx)
            distance = ((x - cx)**2 + (y - cy)**2)**0.5
            Rad_Green.append((theta, distance))

        Rad_Blue = []
        for point in blue_list:
            x, y = point
            theta = np.arctan2(y - cy, x - cx)
            distance = ((x - cx)**2 + (y - cy)**2)**0.5
            Rad_Blue.append((theta, distance))  

        def sort_by_theta(points):
            low = []
            mid = []
            high = []

            for theta, r in points:
                if theta < 0:
                    theta += 2*np.pi

                sector = int((theta / (2*np.pi)) * 3)  # 0, 1, or 2

                if sector == 0:
                    low.append((theta, r))
                elif sector == 1:
                    mid.append((theta, r))
                else:
                    high.append((theta, r))

            return low, mid, high
        low, mid, high = sort_by_theta(Rad_Blue)

        def list_avg(points):
            if len(points) == 0:
                return None, None

            sum_theta = 0
            sum_r = 0

            for theta, r in points:
                sum_theta += theta
                sum_r += r

            return sum_theta / len(points), sum_r / len(points)

        def list_to_point(points):
            if len(points) == 0:
                return None, None

            sx = 0
            sy = 0

            for theta, r in points:
                # Convert polar → Cartesian
                x = cx + r * np.cos(theta)
                y = cy + r * np.sin(theta)

                sx += x
                sy += y

            return sx / len(points), sy / len(points)

        lowTheta, lowR = list_avg(low)
        midTheta, midR = list_avg(mid) 
        highTheta, highR = list_avg(high)

        def safe_polar_to_cart(center_x, center_y, R, Theta, label, img=None):
            if R is None or Theta is None:
                print(f"[WARN] Missing {label} point group — R or Theta is None")

                return None, None

            return (
                center_x + R * np.cos(Theta),
                center_y + R * np.sin(Theta)
            )


        G1_x, G1_y = safe_polar_to_cart(cx, cy, lowR,  lowTheta,  "Green Low",  img)
        G2_x, G2_y = safe_polar_to_cart(cx, cy, midR,  midTheta,  "Green Mid",  img)
        G3_x, G3_y = safe_polar_to_cart(cx, cy, highR, highTheta, "Green High", img)

        low, mid, high = sort_by_theta(Rad_Green)
        lowTheta, lowR = list_avg(low)
        midTheta, midR = list_avg(mid) 
        highTheta, highR = list_avg(high)

        B1_x, B1_y = safe_polar_to_cart(cx, cy, lowR,  lowTheta,  "Blue Low",  img)
        B2_x, B2_y = safe_polar_to_cart(cx, cy, midR,  midTheta,  "Blue Mid",  img)
        B3_x, B3_y = safe_polar_to_cart(cx, cy, highR, highTheta, "Blue High", img)

        def angle_of(x, y):
            return np.arctan2(y - cy, x - cx)

        G_thetas = [angle_of(G1_x, G1_y), angle_of(G2_x, G2_y), angle_of(G3_x, G3_y)]
        B_thetas = [angle_of(B1_x, B1_y), angle_of(B2_x, B2_y), angle_of(B3_x, B3_y)]

        ANGLE_TOL = np.deg2rad(10)

        valid_lines = []
        for i, (Gx, Gy, Bx, By) in enumerate([(G1_x,G1_y,B1_x,B1_y),
                                            (G2_x,G2_y,B2_x,B2_y),
                                            (G3_x,G3_y,B3_x,B3_y)]):

            if None in (Gx, Gy, Bx, By):
                continue

            if abs(G_thetas[i] - B_thetas[i]) < ANGLE_TOL:
                valid_lines.append(("L"+str(i+1), (Gx, Gy, Bx, By)))
            else:
                print(f"[FILTER] Spoke {i+1} rejected: green/blue angle mismatch")

        def angle_of(x, y):
            return np.arctan2(y - cy, x - cx)

        # Compute angles for each centroid
        G_thetas = [
            angle_of(G1_x, G1_y),
            angle_of(G2_x, G2_y),
            angle_of(G3_x, G3_y)
        ]

        B_thetas = [
            angle_of(B1_x, B1_y),
            angle_of(B2_x, B2_y),
            angle_of(B3_x, B3_y)
        ]

        ANGLE_TOL = np.deg2rad(10)  # 10 degrees tolerance

        validated_lines = []

        # Loop through the 3 spokes
        for i, (Gx, Gy, Bx, By) in enumerate([
            (G1_x, G1_y, B1_x, B1_y),
            (G2_x, G2_y, B2_x, B2_y),
            (G3_x, G3_y, B3_x, B3_y)
        ]):
            if None in (Gx, Gy, Bx, By):
                continue

            if abs(G_thetas[i] - B_thetas[i]) < ANGLE_TOL:
                validated_lines.append(("L" + str(i+1), (Gx, Gy, Bx, By)))
            else:
                print(f"[FILTER] Spoke {i+1} rejected: green/blue angle mismatch")
        
        lines = []

        if None not in (G1_x, G1_y, B1_x, B1_y):
            lines.append(("L1", (G1_x, G1_y, B1_x, B1_y)))

        if None not in (G2_x, G2_y, B2_x, B2_y):
            lines.append(("L2", (G2_x, G2_y, B2_x, B2_y)))

        if None not in (G3_x, G3_y, B3_x, B3_y):
            lines.append(("L3", (G3_x, G3_y, B3_x, B3_y)))

        # -----------------------------------------
        # 1. Compute angles for each line
        # -----------------------------------------
        line_angles = {}   # name → angle

        for name, (Gx, Gy, Bx, By) in lines:
            dx = Bx - Gx
            dy = By - Gy
            angle = np.degrees(np.arctan2(dy, dx)) % 360
            line_angles[name] = angle

        # Only apply spacing check if we have 3 lines
        if len(lines) == 3:
            # -----------------------------------------
            # 2. Check 120° spacing
            # -----------------------------------------
            angles_sorted = sorted(line_angles.items(), key=lambda x: x[1])
            vals_sorted  = [a for _, a in angles_sorted]

            d1 = vals_sorted[1] - vals_sorted[0]
            d2 = vals_sorted[2] - vals_sorted[1]
            d3 = (vals_sorted[0] + 360) - vals_sorted[2]

            diffs = [d1, d2, d3]
            TOL = 8  # degrees tolerance

            valid_pattern = all(abs(d - 120) < TOL for d in diffs)

            # -----------------------------------------
            # 3. If invalid, remove the worst line
            # -----------------------------------------
            if not valid_pattern:
                errors = {}
                for name, angle in line_angles.items():
                    ideal_diffs = [
                        abs((angle - 0)   % 360),
                        abs((angle - 120) % 360),
                        abs((angle - 240) % 360)
                    ]
                    errors[name] = min(ideal_diffs)

                bad_line = max(errors, key=errors.get)
                print(f"[FILTER] Removing bad line: {bad_line}")
                lines = [item for item in lines if item[0] != bad_line]

        # Need at least two lines
        if len(lines) >= 2:
            # Use the first two valid lines
            (_, (Gx1, Gy1, Bx1, By1)) = lines[0]
            (_, (Gx2, Gy2, Bx2, By2)) = lines[1]

            # Helper to get (m, b) or vertical form
            def line_to_mb(x1, y1, x2, y2):
                dx = x2 - x1
                dy = y2 - y1
                if dx == 0:
                    return None, x1  # vertical: x = b
                m = dy / dx
                b = y1 - m * x1
                return m, b

            m1, b1 = line_to_mb(Gx1, Gy1, Bx1, By1)
            m2, b2 = line_to_mb(Gx2, Gy2, Bx2, By2)

            # Compute intersection robustly
            if m1 is None and m2 is None:
                # Both vertical → no intersection
                print("[WARN] Both lines vertical; cannot compute intersection.")
                X, Y = cx, cy

            elif m1 is None:
                # Line 1 vertical: x = b1
                X = b1
                Y = m2 * X + b2

            elif m2 is None:
                # Line 2 vertical: x = b2
                X = b2
                Y = m1 * X + b1

            else:
                # Non-vertical lines
                if abs(m1 - m2) < 1e-6:
                    print("[WARN] Lines nearly parallel; using COM as fallback.")
                    X, Y = cx, cy
                else:
                    X = (b2 - b1) / (m1 - m2)
                    Y = m1 * X + b1

            X_off = (X - cx)
            Y_off = (Y - cy)

            Img = np.array(img)

            ys = [y for y in [G1_y, G2_y, G3_y, B1_y, B2_y, B3_y] if y is not None]

            Cenroid_Count = len(ys)
            if Cenroid_Count >= 6:
                print("All 6 centroids found.")
            else:
                print(f"Only {Cenroid_Count} centroids found. Retrying with next brightness threshold...")

            if len(ys) == 0 or ys == [None, None, None, None, None, None]:
                print("[WARN] No valid centroids found.")

            middle = sum(ys) / len(ys)
            above_count = sum(1 for y in ys if y < middle)
            more_above = above_count > len(ys) / 2


            # True if more than half are above
            more_above = above_count > len(ys) / 2

            
            def show_lines_on_crop(img, lines):
                w, h = img.size
                plt.imshow(img)
                
                def draw_line(m, b, color):
                    xs = np.array([0, w])
                    ys = m * xs + b
                    plt.plot(xs, ys, color=color, linewidth=2)

                for name, (Gx, Gy, Bx, By) in lines:
                    if Bx == Gx:
                        # vertical line
                        plt.plot([Gx, Gx], [0, h], color='cyan', linewidth=2)
                        continue

                    m = (By - Gy) / (Bx - Gx)
                    b = Gy - m * Gx

                    color = {'L1': 'magenta', 'L2': 'yellow', 'L3': 'white'}.get(name, 'red')
                    draw_line(m, b, color)

                plt.axis('off')
                plt.show()


            show_lines_on_crop(img, lines)


            return X, Y, more_above
        else:
            print("Mercedes Tracking FAILED !!!!!!!!!")
            return 0, 0, 0






#--------------------------------------- Merc Debugger --------------------------

def Plot_Mercedes(Img):
    """print("[WARN] Only", len(ys), "centroid pixels found. Results may be unreliable.")

    green_x = [x for x in [G1_x, G2_x, G3_x] if x is not None]
    green_y = [y for y in [G1_y, G2_y, G3_y] if y is not None]

    blue_x  = [x for x in [B1_x, B2_x, B3_x] if x is not None]
    blue_y  = [y for y in [B1_y, B2_y, B3_y] if y is not None]



    # --- draw lines ---
    def draw_line(m, b, color):
        xs = np.array([0, img.shape[1]])
        ys = m * xs + b

    import matplotlib.pyplot as plt


    x_fb_plot = (W / 2) + x_feedback
    y_fb_plot = (H / 2) + y_feedback

    X_global = crop_x0 + X
    Y_global = crop_y0 + Y

    def draw_line_on_final(m, b, color):
        height, width = img.shape[:2]
        xs = np.array([0, width])
        ys = m * xs + b
        plt.plot(xs, ys, color=color, linewidth=2, alpha=0.7)

    for name, (Gx, Gy, Bx, By) in lines:
        m = (By - Gy) / (Bx - Gx)
        b = Gy - m * Gx

        if name == "L1":
            draw_line_on_final(m, b, 'magenta')
        elif name == "L2":
            draw_line_on_final(m, b, 'yellow')
        elif name == "L3":
            draw_line_on_final(m, b, 'white')

    plt.legend()
    plt.axis('off')
    plt.show()"""
    print("this debugs and plots")
        
















