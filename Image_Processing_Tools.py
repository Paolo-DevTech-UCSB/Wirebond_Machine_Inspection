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

    #cropped_img.show()

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

                #mask_img.show()
                #cropped_img.show()

                Hole_Type = "Guard-ring"


    return Hole_Type

#------------------------- Mercedes Detection Code ------------------------


def Detect_Merc_Center(img, Details=False):
        def angle_diff(a, b):
            d = abs(a - b) % (2*np.pi)
            return min(d, 2*np.pi - d)

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
                if 55 < R < 85 and is_dark:
                    filtered_image_data.append((0, 255, 0))
                    green_list.append((x, y))

                # 4. Blue ring
                elif 105 < R < 135 and is_dark:
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

        #if Details:
        #    linear_Points_image.show()
        #    input("Check_Output... Press enter.... ")



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
        low_g, mid_g, high_g = sort_by_theta(Rad_Green)
        green_sizes = [len(low_g), len(mid_g), len(high_g)]

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

        g_lowTheta, g_lowR = list_avg(low_g)
        g_midTheta, g_midR = list_avg(mid_g)
        g_highTheta, g_highR = list_avg(high_g)

        def safe_polar_to_cart(center_x, center_y, R, Theta, label, img=None):
            if R is None or Theta is None:
                print(f"[WARN] Missing {label} point group — R or Theta is None")

                return None, None

            return (
                center_x + R * np.cos(Theta),
                center_y + R * np.sin(Theta)
            )


        G1_x, G1_y = safe_polar_to_cart(cx, cy, g_lowR,  g_lowTheta,  "Green Low",  img)
        G2_x, G2_y = safe_polar_to_cart(cx, cy, g_midR,  g_midTheta,  "Green Mid",  img)
        G3_x, G3_y = safe_polar_to_cart(cx, cy, g_highR, g_highTheta, "Green High", img)

        low_b, mid_b, high_b = sort_by_theta(Rad_Blue)
        blue_sizes = [len(low_b), len(mid_b), len(high_b)]

        b_lowTheta, b_lowR = list_avg(low_b)
        b_midTheta, b_midR = list_avg(mid_b)
        b_highTheta, b_highR = list_avg(high_b)

        B1_x, B1_y = safe_polar_to_cart(cx, cy, b_lowR,  b_lowTheta,  "Blue Low",  img)
        B2_x, B2_y = safe_polar_to_cart(cx, cy, b_midR,  b_midTheta,  "Blue Mid",  img)
        B3_x, B3_y = safe_polar_to_cart(cx, cy, b_highR, b_highTheta, "Blue High", img)

        def angle_of(x, y):
            return np.arctan2(y - cy, x - cx)


        def centroid_distance_ok(Gx, Gy, Bx, By, min_expected=65, max_expected=85):
            if None in (Gx, Gy, Bx, By):
                return False

            d = np.hypot(Bx - Gx, By - Gy)

            return (min_expected <= d <= max_expected)

        def centroid_size_ok(g_size, b_size, min_size=60):
            return g_size >= min_size and b_size >= min_size
            


        # First, validate all coordinates BEFORE calling angle_of()
        if None in (G1_x, G1_y, G2_x, G2_y, G3_x, G3_y,
                    B1_x, B1_y, B2_x, B2_y, B3_x, B3_y):
            return None, None, None   # or whatever your function normally returns





        validated_lines = []

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

        ANGLE_TOL = np.deg2rad(10)

        All_Lines = []

        for i, (Gx, Gy, Bx, By) in enumerate([
            (G1_x, G1_y, B1_x, B1_y),
            (G2_x, G2_y, B2_x, B2_y),
            (G3_x, G3_y, B3_x, B3_y)
        ]):
            if None in (Gx, Gy, Bx, By):
                continue

            

            # Compute centroid distance
            d = np.hypot(Bx - Gx, By - Gy)
            min_expected = 40
            max_expected = 90
            dist_ok = (min_expected <= d <= max_expected)
            size_ok = centroid_size_ok(green_sizes[i], blue_sizes[i])
            # Compute slope (m)
            m = (By - Gy) / (Bx - Gx + 1e-6)
            print("m =", (By - Gy) / (Bx - Gx))

            ALLOWED_SLOPE_RANGES = [
                (4, 40),      # vertical-ish
                (-40, -4), 
                (0.40, 0.65),  # down-left
                (-0.90, -0.40) # down-right
            ]
            slope_ok = any(low <= m <= high for (low, high) in ALLOWED_SLOPE_RANGES)


            #print(f"\n--- SPOKE {i+1} ---")
            #print(f"Green centroid: ({Gx:.2f}, {Gy:.2f})")
            #print(f"Blue  centroid: ({Bx:.2f}, {By:.2f})")
            #print(f"Green size:     {green_sizes[i]}")
            #print(f"Blue size:      {blue_sizes[i]}")
            #print(f"Distance:       {d:.2f} px")
            #print(f"Angle diff:     {ang_diff:.3f} rad")

            COLOR_LABELS = {
                0: "magenta",
                1: "yellow",
                2: "white"
            }

            # Final validation
            if dist_ok and slope_ok:
                validated_lines.append(("L" + str(i+1), (Gx, Gy, Bx, By)))
                All_Lines.append(("L" + str(i+1), (Gx, Gy, Bx, By)))
            else:
                print(f"[FILTER] Spoke {COLOR_LABELS.get(i, 'unknown')} rejected: "
                    f"{'distance' if not dist_ok else 'slope'}")
                All_Lines.append(("L" + str(i+1), (Gx, Gy, Bx, By)))
                print("d, greensize, bluesize:", d, green_sizes[i], blue_sizes[i])



        #show_lines_on_crop(img, All_Lines)

        return validated_lines



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



def find_other_spokes(X_1, X_2, Y_1, Y_2, img):
    width, height = img.size
    centerX = width / 2.0
    centerY = height / 2.0
    image_center = np.array([centerX, centerY], dtype=float)

    # ---------------------------------------------------------
    # 1. Base spoke direction (unit vector) + hub projection
    # ---------------------------------------------------------
    P1 = np.array([X_1, Y_1], dtype=float)
    P2 = np.array([X_2, Y_2], dtype=float)
    base_dir = P2 - P1
    base_dir /= np.linalg.norm(base_dir) + 1e-9

    # Project image center onto the original spoke to get hub
    v = image_center - P1
    t = np.dot(v, base_dir)
    center = P1 + t * base_dir   # hub point

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
    def normal(v):
        return np.array([-v[1], v[0]])

    n2 = normal(dir2)
    n3 = normal(dir3)
    n2 /= np.linalg.norm(n2) + 1e-9
    n3 /= np.linalg.norm(n3) + 1e-9

    # ---------------------------------------------------------
    # 2. Build 7 parallel lines for each spoke family
    #    offsets: -75, -50, -25, 0, +25, +50, +75 pixels
    # ---------------------------------------------------------
    offsets = np.array([-50, -25, 0, 25, 50], dtype=float)
    N = len(offsets)  # 7

    lines2 = []
    lines3 = []
    for off in offsets:
        p2 = center + off * n2
        p3 = center + off * n3
        lines2.append((p2, dir2))
        lines3.append((p3, dir3))

    # ---------------------------------------------------------
    # 3. Intersections: build NxN grid of crossing points
    #    Solve: p2 + t2*d2 = p3 + t3*d3
    # ---------------------------------------------------------
    def intersect(p2, d2, p3, d3):
        A = np.column_stack((d2, -d3))  # 2x2
        b = (p3 - p2)
        det = np.linalg.det(A)
        if abs(det) < 1e-9:
            return None
        t_s = np.linalg.solve(A, b)
        t = t_s[0]
        return p2 + t * d2

    grid_points = [[None for _ in range(N)] for _ in range(N)]
    for i, (p2, d2) in enumerate(lines2):
        for j, (p3, d3) in enumerate(lines3):
            pt = intersect(p2, d2, p3, d3)
            if pt is None:
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

    def sample_cell(c00, c10, c01, c11, img, Nsamples=20):
        samples = []
        c00 = np.array(c00)
        c10 = np.array(c10)
        c01 = np.array(c01)
        c11 = np.array(c11)

        for u in np.linspace(0.1, 0.9, Nsamples):
            for v in np.linspace(0.1, 0.9, Nsamples):
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
    # 5. Column and row brightness over (N-1)x(N-1) cells
    # ---------------------------------------------------------
    column_brightness = []
    for col in range(N - 1):
        cell_values = []
        for row in range(N - 1):
            c00 = grid_points[col][row]
            c10 = grid_points[col+1][row]
            c01 = grid_points[col][row+1]
            c11 = grid_points[col+1][row+1]
            cell_values.append(sample_cell(c00, c10, c01, c11, img))
        column_brightness.append(np.mean(cell_values))

    row_brightness = []
    for row in range(N - 1):
        cell_values = []
        for col in range(N - 1):
            c00 = grid_points[col][row]
            c10 = grid_points[col+1][row]
            c01 = grid_points[col][row+1]
            c11 = grid_points[col+1][row+1]
            cell_values.append(sample_cell(c00, c10, c01, c11, img))
        row_brightness.append(np.mean(cell_values))

    #print("\n=== DEBUG BRIGHTNESS ===")
    #print("Column darkness (higher = darker):")
    #for i, val in enumerate(column_brightness):
    #    print(f"  Column {i}: {val}")
    #print("\nRow darkness (higher = darker):")
    #for i, val in enumerate(row_brightness):
    #    print(f"  Row {i}: {val}")
    #print("========================\n")

    darkest_col = int(np.argmax(column_brightness))
    darkest_row = int(np.argmax(row_brightness))

    # center index in the grid
    mid = N // 2  # 3 for 7x7

    spoke2_x, spoke2_y = grid_points[darkest_col][mid]
    spoke3_x, spoke3_y = grid_points[mid][darkest_row]

    # ---------------------------------------------------------
    # Debug plot
    # ---------------------------------------------------------
    col_top = grid_points[darkest_col][0]
    col_bottom = grid_points[darkest_col][N-1]
    row_left = grid_points[0][darkest_row]
    row_right = grid_points[N-1][darkest_row]

    plt.figure(figsize=(7, 7))
    #plt.imshow(img)

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
    for col in range(N):
        for row in range(N):
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
    for col in range(N):
        x0, y0 = grid_points[col][0]
        x1, y1 = grid_points[col][N-1]
        plt.arrow(
            x0, y0,
            (x1 - x0) * 0.25,
            (y1 - y0) * 0.25,
            color='cyan',
            head_width=6,
            length_includes_head=True
        )

    # row direction arrows
    for row in range(N):
        x0, y0 = grid_points[0][row]
        x1, y1 = grid_points[N-1][row]
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
    plt.title("Labeled 7x7 Grid with Darkest Column/Row (Hub-Centered)")
    #plt.show()

    # Convert points into short line segments so get_center_from_spokes() works
    L = 40  # length of the fake line segment

    # after you compute dir2, dir3 and spoke2_x, spoke2_y, spoke3_x, spoke3_y

    L = 40

    # normalize directions just in case
    d2 = dir2 / (np.linalg.norm(dir2) + 1e-9)
    d3 = dir3 / (np.linalg.norm(dir3) + 1e-9)

    p2 = np.array([spoke2_x, spoke2_y], dtype=float)
    p3 = np.array([spoke3_x, spoke3_y], dtype=float)

    spoke2_line = (
        p2[0] - L * d2[0], p2[1] - L * d2[1],
        p2[0] + L * d2[0], p2[1] + L * d2[1]
    )

    spoke3_line = (
        p3[0] - L * d3[0], p3[1] - L * d3[1],
        p3[0] + L * d3[0], p3[1] + L * d3[1]
    )

    return [
        ('ORIGINAL', (X_1, Y_1, X_2, Y_2)),
        ('SPOKE2', spoke2_line),
        ('SPOKE3', spoke3_line)
    ]


def infer_missing_spoke_from_two(lines, img=None):
    """
    Given exactly 2 spokes, infer the 3rd spoke direction.
    Returns a list of 3 spokes in the same format as 'find_other_spokes'.
    """

    if len(lines) != 2:
        print("infer_missing_spoke_from_two: requires exactly 2 spokes")
        return lines

    # -------------------------------
    # Extract the two known spokes
    # -------------------------------
    (_, (x1, y1, x2, y2)) = lines[0]
    (_, (x3, y3, x4, y4)) = lines[1]

    # -------------------------------
    # Compute their intersection (hub)
    # -------------------------------
    hub = get_center_from_spokes(lines)
    if hub is None or hub == (None, None):
        print("infer_missing_spoke_from_two: could not compute hub")
        return lines

    hx, hy = hub

    # -------------------------------
    # Compute angles of the two spokes
    # -------------------------------
    ang1 = np.arctan2(y2 - y1, x2 - x1)
    ang2 = np.arctan2(y4 - y3, x4 - x3)

    # Normalize to [0, 2π)
    ang1 = ang1 % (2*np.pi)
    ang2 = ang2 % (2*np.pi)

    # -------------------------------
    # The three spokes should be 120° apart.
    # Find the missing angle.
    # -------------------------------
    angles = sorted([ang1, ang2])
    a, b = angles

    # Candidate missing angles
    cand1 = (a + 2*np.pi/3) % (2*np.pi)
    cand2 = (a + 4*np.pi/3) % (2*np.pi)

    # Choose the one that is NOT close to ang2
    if abs(((cand1 - b + np.pi) % (2*np.pi)) - np.pi) > np.deg2rad(20):
        missing_angle = cand1
    else:
        missing_angle = cand2

    # -------------------------------
    # Build a short line segment for the missing spoke
    # -------------------------------
    L = 60  # length of the segment
    dx = np.cos(missing_angle)
    dy = np.sin(missing_angle)

    xA = hx - L * dx
    yA = hy - L * dy
    xB = hx + L * dx
    yB = hy + L * dy

    missing_spoke = ('SPOKE_MISSING', (xA, yA, xB, yB))

    # -------------------------------
    # Return all three spokes
    # -------------------------------
    return [
        lines[0],
        lines[1],
        missing_spoke
    ]



def angle_diff(a, b):
    d = abs(a - b) % (2*np.pi)
    return min(d, 2*np.pi - d)
