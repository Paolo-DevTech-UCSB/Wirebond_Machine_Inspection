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

#--------------------Loader-----------------------------

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

        # First, validate all coordinates BEFORE calling angle_of()
        if None in (G1_x, G1_y, G2_x, G2_y, G3_x, G3_y,
                    B1_x, B1_y, B2_x, B2_y, B3_x, B3_y):
            return None, None, None   # or whatever your function normally returns

        # Now it's safe to compute angles
        G_thetas = [angle_of(G1_x, G1_y),
                    angle_of(G2_x, G2_y),
                    angle_of(G3_x, G3_y)]

        B_thetas = [angle_of(B1_x, B1_y),
                    angle_of(B2_x, B2_y),
                    angle_of(B3_x, B3_y)]

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

        #Lines Expected in this format:
        #(name, (Gx, Gy, Bx, By))
        unvalidated_lines = []
        unvalidated_lines.append(("L1", (G1_x, G1_y, B1_x, B1_y)))
        unvalidated_lines.append(("L2", (G2_x, G2_y, B2_x, B2_y)))
        unvalidated_lines.append(("L3", (G3_x, G3_y, B3_x, B3_y)))

        show_lines_on_crop(linear_Points_image, unvalidated_lines)

        ANGLE_TOL = np.deg2rad(20)  # 20 degrees tolerance

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

        # correct:
        lines = validated_lines
        dx = Bx - Gx
        dy = By - Gy
        angle = np.degrees(np.arctan2(dy, dx)) % 360
        #line_angles[name] = angle

        # -----------------------------------------
        # Require exactly 3 spokes and ~120° spacing
        # -----------------------------------------
        

        #Quick Plot to Check the Spokes

        return lines



def show_lines_on_crop(img, lines):
            w, h = img.size
            plt.imshow(img)
            
            def draw_line(m, b, color):
                xs = np.array([0, w])
                ys = m * xs + b
                plt.plot(xs, ys, color=color, linewidth=2)

            for name, (Gx, Gy, Bx, By) in lines:
                if Bx == Gx:
                    plt.plot([Gx, Gx], [0, h], color='cyan', linewidth=2)
                    continue

                m = (By - Gy) / (Bx - Gx)
                b = Gy - m * Gx

                color = {'L1': 'magenta', 'L2': 'yellow', 'L3': 'white'}.get(name, 'red')
                draw_line(m, b, color)

            plt.axis('off')
            plt.show()


def get_center_from_spokes(lines):
    """
    lines: list of tuples in the form:
           (name, (Gx, Gy, Bx, By))
    Returns: (center_x, center_y)
    """

    # Must have at least 2 spokes
    if len(lines) < 2:
        print("Not enough spokes to compute intersection")
        return None, None

    # Extract first two spokes
    (_, (x1, y1, x2, y2)) = lines[0]
    (_, (x3, y3, x4, y4)) = lines[1]

    # Convert to slope-intercept form
    def to_mb(x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0:
            return None, x1  # vertical line: x = b
        m = dy / dx
        b = y1 - m * x1
        return m, b

    m1, b1 = to_mb(x1, y1, x2, y2)
    m2, b2 = to_mb(x3, y3, x4, y4)

    # Handle vertical + vertical (parallel)
    # Handle vertical + vertical (parallel)
    if m1 is None and m2 is None:
        print("Both spokes are vertical — no intersection")
        return None


    # Line 1 vertical
    if m1 is None:
        x = b1
        y = m2 * x + b2
        return x, y

    # Line 2 vertical
    if m2 is None:
        x = b2
        y = m1 * x + b1
        return x, y

    # Parallel non-vertical
    if m1 == m2:
        print("Spokes are parallel — no intersection")
        return None


    # Standard intersection
    x = (b2 - b1) / (m1 - m2)
    y = m1 * x + b1
    return x, y


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

"""def Detect_Merc_Center(img, Details=False):
        validated_lines = []
        width, height = img.size
        w, h = img.size
        centerX = w / 2
        centerY = h / 2

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

        # First, validate all coordinates BEFORE calling angle_of()
        if None in (G1_x, G1_y, G2_x, G2_y, G3_x, G3_y,
                    B1_x, B1_y, B2_x, B2_y, B3_x, B3_y):
            return None, None, None   # or whatever your function normally returns

        # Now it's safe to compute angles
        G_thetas = [angle_of(G1_x, G1_y),
                    angle_of(G2_x, G2_y),
                    angle_of(G3_x, G3_y)]

        B_thetas = [angle_of(B1_x, B1_y),
                    angle_of(B2_x, B2_y),
                    angle_of(B3_x, B3_y)]

        ANGLE_TOL = np.deg2rad(10)


        valid_lines = []
        line_angles = {}

        line_angles = {}

        for name, (Gx, Gy, Bx, By) in validated_lines:
            dx = Bx - Gx
            dy = By - Gy
            angle = np.degrees(np.arctan2(dy, dx)) % 360
            line_angles[name] = angle




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

        # correct:
        lines = validated_lines
        dx = Bx - Gx
        dy = By - Gy
        angle = np.degrees(np.arctan2(dy, dx)) % 360
        #line_angles[name] = angle

        # -----------------------------------------
        # Require exactly 3 spokes and ~120° spacing
        # -----------------------------------------
        
        # Normalize all spokes into point form (use the G point)
        normalized_lines = []

        for entry in lines:
            if isinstance(entry, tuple) and len(entry) == 2:
                # Already a point (recovered spoke)
                normalized_lines.append(entry)

            else:
                # Old format: ("L1", (Gx, Gy, Bx, By))
                name, (Gx, Gy, Bx, By) = entry
                normalized_lines.append((Gx, Gy))


        # Add recovered spokes
        try:
            if new_spokes is not None:
                ...
        except UnboundLocalError:
            new_spokes = None


        # Replace original lines with normalized version
        lines = normalized_lines



        def make_line(name, p1, p2):
            Gx, Gy = p1
            Bx, By = p2
            return (name, (Gx, Gy, Bx, By))

        lines.append(make_line("REC1", spokeA, spokeB))
        lines.append(make_line("REC2", spokeB, spokeA))



        #Quick Plot to Check the Spokes
        
        def show_lines_on_crop(img, lines):
            w, h = img.size
            plt.imshow(img)
            
            def draw_line(m, b, color):
                xs = np.array([0, w])
                ys = m * xs + b
                plt.plot(xs, ys, color=color, linewidth=2)

            for name, (Gx, Gy, Bx, By) in lines:
                if Bx == Gx:
                    plt.plot([Gx, Gx], [0, h], color='cyan', linewidth=2)
                    continue

                m = (By - Gy) / (Bx - Gx)
                b = Gy - m * Gx

                color = {'L1': 'magenta', 'L2': 'yellow', 'L3': 'white'}.get(name, 'red')
                draw_line(m, b, color)

            plt.axis('off')
            plt.show()
        
        #show_lines_on_crop(img, lines)
        
        if len(lines) == 0:
            print("[FILTER] Need exactly 3 spokes; got", len(lines))
            print("Mercedes Tracking FAILED !!!!!!!!!")
            return 0, 0, 0

        elif len(lines) < 3:

            new_spokes = None

            # Try to recover using any valid spoke pair
            if None not in (G1_x, G1_y, B1_x, B1_y):
                new_spokes = find_other_spokes(G1_x, B1_x, G1_y, B1_y, img)

            elif None not in (G2_x, G2_y, B2_x, B2_y):
                new_spokes = find_other_spokes(G2_x, B2_x, G2_y, B2_y, img)

            elif None not in (G3_x, G3_y, B3_x, B3_y):
                new_spokes = find_other_spokes(G3_x, B3_x, G3_y, B3_y, img)

            print(f"[FILTER] Only {len(lines)} spokes found; need 3.")

            # If find_other_spokes succeeded, add the two new spokes
            if new_spokes is not None:
                spokeA, spokeB = new_spokes
                lines.append(make_line("REC1", spokeA, spokeB))
                lines.append(make_line("REC2", spokeB, spokeA))
                print("[FILTER] Added recovered spokes:", spokeA, spokeB)
            else:
                print("[FILTER] Could not recover spokes — new_spokes is None")

            if len(lines) < 3:
                print("[FILTER] Still fewer than 3 spokes after recovery.")
                return 0, 0, 0


                # Recompute angles now that we have 3 spokes
                line_angles = {}
                for (x, y) in lines:
                    angle = np.degrees(np.arctan2(y - centerY, x - centerX)) % 360
                    line_angles[(x, y)] = angle

                angles_sorted = sorted(line_angles.items(), key=lambda x: x[1])
                vals_sorted  = [a for _, a in angles_sorted]


                print("[FILTER] Added recovered spokes:", spokeA, spokeB)

            # If still fewer than 3, fail
            if len(lines) < 3:
                print("[FILTER] Still fewer than 3 spokes after recovery.")
                return 0, 0, 0


        d1 = vals_sorted[1] - vals_sorted[0]
        d2 = vals_sorted[2] - vals_sorted[1]
        d3 = (vals_sorted[0] + 360) - vals_sorted[2]

        diffs = [d1, d2, d3]
        TOL = 8  # degrees tolerance

        valid_pattern = all(abs(d - 120) < TOL for d in diffs)

        if not valid_pattern:
            print("[FILTER] 3 spokes found but not 120° apart:", diffs)
            print("Mercedes Tracking FAILED !!!!!!!!!")
            return 0, 0, 0


        # At this point we KNOW we have 3 spokes ~120° apart.
        # You can still choose any 2 to compute the intersection.
        # For example, use the first two in `lines`:
        entry = lines[1]

        if not (isinstance(entry, tuple) and len(entry) == 2):
            print("Invalid line entry:", entry)
            return None  # or handle gracefully

        (_, (Gx2, Gy2, Bx2, By2)) = entry

        # ... keep your existing intersection logic here ...


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

        


        # ❗ CALL IT HERE, not inside the function
        #show_lines_on_crop(img, lines)

        return X, Y, more_above


        #return 0, 0, 0 """


"""
def find_other_spokes(X_1, X_2, Y_1, Y_2, img):
    width, height = img.size
    centerX = width / 2
    centerY = height / 2

    first_angle = np.arctan2(Y_1 - Y_2, X_1 - X_2)
    second_angle = first_angle + np.deg2rad(60)
    third_angle  = first_angle + np.deg2rad(120)



    VERTICAL_THRESHOLD = 20
    m = np.tan(first_angle)
    b = Y_1 - m * X_1
    print("slope m =", m, "intercept b =", b)

    if abs(m) <= VERTICAL_THRESHOLD:
        x1 = centerX
        y1 = m * centerX + b
    else:
        x1 = X_1
        y1 = centerY

    theta2 = first_angle + np.deg2rad(60)
    theta3 = first_angle + np.deg2rad(120)


    m2 = np.tan(theta2)
    m3 = np.tan(theta3)

    print("m =", m)
    print("m2 =", m2)
    print("m3 =", m3)



    # --- FIXED: use x1 instead of centerX ---
    B2_A = y1 - m2 * x1
    B2_B = (m*(x1 + 25) + b) - m2*(x1 + 25)
    B2_C = (m*(x1 + 50) + b) - m2*(x1 + 50)
    B2_D = (m*(x1 - 25) + b) - m2*(x1 - 25)
    B2_E = (m*(x1 - 50) + b) - m2*(x1 - 50)

    B3_A = y1 - m3 * x1
    B3_B = (m*(x1 + 25) + b) - m3*(x1 + 25)
    B3_C = (m*(x1 + 50) + b) - m3*(x1 + 50)
    B3_D = (m*(x1 - 25) + b) - m3*(x1 - 25)
    B3_E = (m*(x1 - 50) + b) - m3*(x1 - 50)

    parallel2 = [(m2, B2_C), (m2, B2_B), (m2, B2_A), (m2, B2_D), (m2, B2_E)]
    parallel3 = [(m3, B3_C), (m3, B3_B), (m3, B3_A), (m3, B3_D), (m3, B3_E)]



    grid_points = []

    for (m2_line, B2_line) in parallel2:
        column_points = []
        for (m3_line, B3_line) in parallel3:
            x_int = (B3_line - B2_line) / (m2_line - m3_line)
            y_int = m2_line * x_int + B2_line
            column_points.append((x_int, y_int))
        grid_points.append(column_points)


    def safe_getpixel(img, x, y):
        width, height = img.size
        if 0 <= x < width and 0 <= y < height:
            return img.getpixel((x, y))
        return None


    # ============================================================
    # NEW: Robust brightness sampling using FULL BORDER SAMPLING
    # ============================================================

    def sample_cell(c00, c10, c01, c11, img, N=20):
        samples = []
        for u in np.linspace(0.1, 0.9, N):
            for v in np.linspace(0.1, 0.9, N):
                # bilinear interpolation
                x = (1-u)*(1-v)*c00[0] + u*(1-v)*c10[0] + (1-u)*v*c01[0] + u*v*c11[0]
                y = (1-u)*(1-v)*c00[1] + u*(1-v)*c10[1] + (1-u)*v*c01[1] + u*v*c11[1]

                px = safe_getpixel(img, int(x), int(y))
                if px is None:
                    continue
                r, g, b = px

                lum = 0.2126*r + 0.7152*g + 0.0722*b
                darkness = 255 - lum
                samples.append(darkness)

        return np.mean(samples)



    # ============================
    # COLUMN BRIGHTNESS (cells)
    # ============================
    column_brightness = []
    for col in range(4):  # only 0–3 have cells
        cell_values = []
        for row in range(4):
            c00 = grid_points[col][row]
            c10 = grid_points[col+1][row]
            c01 = grid_points[col][row+1]
            c11 = grid_points[col+1][row+1]
            cell_values.append(sample_cell(c00, c10, c01, c11, img))
        column_brightness.append(np.mean(cell_values))

    # ============================
    # ROW BRIGHTNESS (cells)
    # ============================
    row_brightness = []
    for row in range(4):  # only 0–3 have cells
        cell_values = []
        for col in range(4):
            c00 = grid_points[col][row]
            c10 = grid_points[col+1][row]
            c01 = grid_points[col][row+1]
            c11 = grid_points[col+1][row+1]
            cell_values.append(sample_cell(c00, c10, c01, c11, img))
        row_brightness.append(np.mean(cell_values))"""

    # pick darkest (max darkness)
    #darkest_col = int(np.argmax(column_brightness))  # 0–3
    #darkest_row = int(np.argmax(row_brightness))     # 0–3

    
    """# --- FIXED: use the correct variable names ---
    spoke2_x, spoke2_y = grid_points[darkest_col][2]
    spoke3_x, spoke3_y = grid_points[2][darkest_row]

    ####VERIFY SPOKE POSITIONS 

        # ---------------------------------------------------------
    # Convert darkest column and row back into actual lines
    # ---------------------------------------------------------

    # Column line: use top and bottom intersections
    col_top = grid_points[darkest_col][0]
    col_bottom = grid_points[darkest_col][4]

    # Row line: use leftmost and rightmost intersections
    row_left = grid_points[0][darkest_row]
    row_right = grid_points[4][darkest_row]

    # ---------------------------------------------------------
    # Plot original spoke + inferred darkest column/row lines
    # ---------------------------------------------------------

    plt.figure(figsize=(7,7))
    plt.imshow(img)

    # ---------------------------------------------------------
    # Original spoke (yellow)
    # ---------------------------------------------------------
    plt.plot([X_1, X_2], [Y_1, Y_2], 'y-', linewidth=2, label='Original Spoke')


    # ---------------------------------------------------------
    # Darkest column line (cyan)
    # ---------------------------------------------------------
    plt.plot(
        [col_top[0], col_bottom[0]],
        [col_top[1], col_bottom[1]],
        'c-', linewidth=2, label=f'Darkest Column = {darkest_col}'
    )


    # ---------------------------------------------------------
    # Darkest row line (magenta)
    # ---------------------------------------------------------
    plt.plot(
        [row_left[0], row_right[0]],
        [row_left[1], row_right[1]],
        'm-', linewidth=2, label=f'Darkest Row = {darkest_row}'
    )


    # ---------------------------------------------------------
    # Plot grid intersections + labels
    # ---------------------------------------------------------
    for col in range(5):
        for row in range(5):
            x, y = grid_points[col][row]
            plt.scatter(x, y, c='white', s=40)
            plt.text(
                x + 3, y - 3,
                f"({col},{row})",
                color='white',
                fontsize=8,
                ha='left', va='bottom'
            )


    # ---------------------------------------------------------
    # Draw arrows showing column direction (cyan)
    # ---------------------------------------------------------
    for col in range(5):
        x0, y0 = grid_points[col][0]
        x1, y1 = grid_points[col][4]
        plt.arrow(
            x0, y0,
            (x1 - x0) * 0.25,
            (y1 - y0) * 0.25,
            color='cyan',
            head_width=6,
            length_includes_head=True
        )


    # ---------------------------------------------------------
    # Draw arrows showing row direction (magenta)
    # ---------------------------------------------------------
    for row in range(5):
        x0, y0 = grid_points[0][row]
        x1, y1 = grid_points[4][row]
        plt.arrow(
            x0, y0,
            (x1 - x0) * 0.25,
            (y1 - y0) * 0.25,
            color='magenta',
            head_width=6,
            length_includes_head=True
        )


    # ---------------------------------------------------------
    # Mark the two detected spokes
    # ---------------------------------------------------------
    plt.scatter(spoke2_x, spoke2_y, c='cyan', s=120, marker='x')
    plt.scatter(spoke3_x, spoke3_y, c='magenta', s=120, marker='x')


    plt.legend()
    plt.gca().invert_yaxis()
    plt.title("Labeled Grid with Darkest Column/Row")
    plt.show()




    #########################


    #return (spoke2_x, spoke2_y), (spoke3_x, spoke3_y)
    return [
        ('SPOKE2', (spoke2_x, spoke2_y, spoke2_x, spoke2_y)),
        ('SPOKE3', (spoke3_x, spoke3_y, spoke3_x, spoke3_y))
    ]




    #see how this creates a grid of 16 rombuses? assuming the spokes are in those cells, one collum will
    #allways be darker than the other three, thats where the spoke is 
    #the same situation works with the the rows
    #finding the darkest collumn & row, essentialy gives us the best estimate for the location of the spoke.
    #which will be returned by this greater fucntion and used to correct the location of the center point.


    """


    
def find_other_spokes(X_1, X_2, Y_1, Y_2, img):
    width, height = img.size
    centerX = width / 2.0
    centerY = height / 2.0
    center = np.array([centerX, centerY], dtype=float)

    # ---------------------------------------------------------
    # 1. Base spoke direction (unit vector)
    # ---------------------------------------------------------
    dx = X_2 - X_1
    dy = Y_2 - Y_1
    base_dir = np.array([dx, dy], dtype=float)
    base_dir /= np.linalg.norm(base_dir) + 1e-9  # avoid div0

    # 2 other spoke directions, 60° and 120° away (as lines)
    def rotate(v, angle_rad):
        c = np.cos(angle_rad)
        s = np.sin(angle_rad)
        R = np.array([[c, -s],
                      [s,  c]])
        return R @ v

    dir2 = rotate(base_dir, np.deg2rad(60))
    dir3 = rotate(base_dir, np.deg2rad(120))

    # Perpendicular normals (for parallel offsets)
    # Normal is 90° rotation of direction
    def normal(v):
        return np.array([-v[1], v[0]])

    n2 = normal(dir2)
    n3 = normal(dir3)

    # Normalize normals so "offset" is in pixels
    n2 /= np.linalg.norm(n2) + 1e-9
    n3 /= np.linalg.norm(n3) + 1e-9

    # ---------------------------------------------------------
    # 2. Build 5 parallel lines for each spoke family
    #    offsets: -50, -25, 0, +25, +50 pixels
    # ---------------------------------------------------------
    offsets = np.array([-50, -25, 0, 25, 50], dtype=float)

    # Each line is represented as (point, direction)
    lines2 = []  # family for dir2
    lines3 = []  # family for dir3

    for off in offsets:
        p2 = center + off * n2
        p3 = center + off * n3
        lines2.append((p2, dir2))
        lines3.append((p3, dir3))

    # ---------------------------------------------------------
    # 3. Intersections: build 5x5 grid of crossing points
    #    Solve: p2 + t2*d2 = p3 + t3*d3
    # ---------------------------------------------------------
    def intersect(p2, d2, p3, d3):
        # Solve p2 + t*d2 = p3 + s*d3
        # => t*d2 - s*d3 = (p3 - p2)
        A = np.column_stack((d2, -d3))  # 2x2
        b = (p3 - p2)
        det = np.linalg.det(A)
        if abs(det) < 1e-9:
            return None  # parallel or nearly so
        t_s = np.linalg.solve(A, b)
        t = t_s[0]
        return p2 + t * d2

    grid_points = [[None for _ in range(5)] for _ in range(5)]
    for i, (p2, d2) in enumerate(lines2):
        for j, (p3, d3) in enumerate(lines3):
            pt = intersect(p2, d2, p3, d3)
            if pt is None:
                # fallback: just put something off-image but finite
                pt = np.array([-1e6, -1e6])
            grid_points[i][j] = pt

    # ---------------------------------------------------------
    # 4. Safe pixel access + cell sampling
    # ---------------------------------------------------------
    def safe_getpixel(img, x, y):
        w, h = img.size
        if 0 <= x < w and 0 <= y < h:
            return img.getpixel((x, y))
        return None

    def sample_cell(c00, c10, c01, c11, img, N=20):
        samples = []
        c00 = np.array(c00)
        c10 = np.array(c10)
        c01 = np.array(c01)
        c11 = np.array(c11)

        for u in np.linspace(0.1, 0.9, N):
            for v in np.linspace(0.1, 0.9, N):
                # bilinear interpolation in param space
                x = (1-u)*(1-v)*c00[0] + u*(1-v)*c10[0] + (1-u)*v*c01[0] + u*v*c11[0]
                y = (1-u)*(1-v)*c00[1] + u*(1-v)*c10[1] + (1-u)*v*c01[1] + u*v*c11[1]

                px = safe_getpixel(img, int(x), int(y))
                if px is None:
                    continue
                r, g, b = px
                lum = 0.2126*r + 0.7152*g + 0.0722*b
                darkness = 255 - lum
                samples.append(darkness)

        if not samples:
            return 0.0
        return float(np.mean(samples))

    # ---------------------------------------------------------
    # 5. Column and row brightness over 4x4 cells
    # ---------------------------------------------------------
    column_brightness = []
    for col in range(4):
        cell_values = []
        for row in range(4):
            c00 = grid_points[col][row]
            c10 = grid_points[col+1][row]
            c01 = grid_points[col][row+1]
            c11 = grid_points[col+1][row+1]
            cell_values.append(sample_cell(c00, c10, c01, c11, img))
        column_brightness.append(np.mean(cell_values))

    row_brightness = []
    for row in range(4):
        cell_values = []
        for col in range(4):
            c00 = grid_points[col][row]
            c10 = grid_points[col+1][row]
            c01 = grid_points[col][row+1]
            c11 = grid_points[col+1][row+1]
            cell_values.append(sample_cell(c00, c10, c01, c11, img))
        row_brightness.append(np.mean(cell_values))

    print("\n=== DEBUG BRIGHTNESS ===")
    print("Column darkness (higher = darker):")
    for i, val in enumerate(column_brightness):
        print(f"  Column {i}: {val}")
    print("\nRow darkness (higher = darker):")
    for i, val in enumerate(row_brightness):
        print(f"  Row {i}: {val}")
    print("========================\n")

    darkest_col = int(np.argmax(column_brightness))
    darkest_row = int(np.argmax(row_brightness))

    # spokes as points on those lines near the center of the grid
    spoke2_x, spoke2_y = grid_points[darkest_col][2]
    spoke3_x, spoke3_y = grid_points[2][darkest_row]

    # ---------------------------------------------------------
    # Optional debug plot (kept from your version)
    # ---------------------------------------------------------
    col_top = grid_points[darkest_col][0]
    col_bottom = grid_points[darkest_col][4]
    row_left = grid_points[0][darkest_row]
    row_right = grid_points[4][darkest_row]

    plt.figure(figsize=(7, 7))
    plt.imshow(img)

    # original spoke
    plt.plot([X_1, X_2], [Y_1, Y_2], 'y-', linewidth=2, label='Original Spoke')

    # darkest column line
    plt.plot(
        [col_top[0], col_bottom[0]],
        [col_top[1], col_bottom[1]],
        'c-', linewidth=2, label=f'Darkest Column = {darkest_col}'
    )

    # darkest row line
    plt.plot(
        [row_left[0], row_right[0]],
        [row_left[1], row_right[1]],
        'm-', linewidth=2, label=f'Darkest Row = {darkest_row}'
    )

    # grid points
    for col in range(5):
        for row in range(5):
            x, y = grid_points[col][row]
            plt.scatter(x, y, c='white', s=40)
            plt.text(
                x + 3, y - 3,
                f"({col},{row})",
                color='white',
                fontsize=8,
                ha='left', va='bottom'
            )

    # column direction arrows
    for col in range(5):
        x0, y0 = grid_points[col][0]
        x1, y1 = grid_points[col][4]
        plt.arrow(
            x0, y0,
            (x1 - x0) * 0.25,
            (y1 - y0) * 0.25,
            color='cyan',
            head_width=6,
            length_includes_head=True
        )

    # row direction arrows
    for row in range(5):
        x0, y0 = grid_points[0][row]
        x1, y1 = grid_points[4][row]
        plt.arrow(
            x0, y0,
            (x1 - x0) * 0.25,
            (y1 - y0) * 0.25,
            color='magenta',
            head_width=6,
            length_includes_head=True
        )

    # mark detected spokes
    plt.scatter(spoke2_x, spoke2_y, c='cyan', s=120, marker='x')
    plt.scatter(spoke3_x, spoke3_y, c='magenta', s=120, marker='x')

    plt.legend()
    plt.gca().invert_yaxis()
    plt.title("Labeled Grid with Darkest Column/Row (Parametric Version)")
    plt.show()

    return [
        ('SPOKE2', (spoke2_x, spoke2_y, spoke2_x, spoke2_y)),
        ('SPOKE3', (spoke3_x, spoke3_y, spoke3_x, spoke3_y))
    ]



    #see how this creates a grid of 16 rombuses? assuming the spokes are in those cells, one collum will
    #allways be darker than the other three, thats where the spoke is 
    #the same situation works with the the rows
    #finding the darkest collumn & row, essentialy gives us the best estimate for the location of the spoke.
    #which will be returned by this greater fucntion and used to correct the location of the center point.
