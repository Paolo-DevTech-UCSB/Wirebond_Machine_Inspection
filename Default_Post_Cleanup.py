



def is_sensor_color(r, g, b):
    return (
        100 <= r <= 185 and
        165 <= g <= 240 and
        215 <= b <= 255 and
        b > g > r
    )

def is_FR4_color(r, g, b):
    return (
        0 <= r <= 100 and
        0 <= g <= 100 and
        0 <= b <= 100 and
        r < 50 and g < 50 and b < 50
    )


def detect_sensor_with_fr4_ring(img):
    """
    1. Checks for a ~350px diameter SENSOR-colored circle in the center.
    2. Checks for an FR4 ring surrounding it.
    Returns True if both conditions are satisfied.
    """

    W, H = img.size
    cx, cy = W // 2, H // 2

    pixels = img.load()

    SENSOR_RADIUS = 175          # 350px diameter
    SENSOR_TOL    = 20           # tolerance for imperfect edges
    FR4_INNER     = SENSOR_RADIUS + 10
    FR4_OUTER     = SENSOR_RADIUS + 60

    sensor_count = 0
    sensor_total = 0

    fr4_count = 0
    fr4_total = 0

    for y in range(H):
        for x in range(W):
            r, g, b = pixels[x, y]

            # distance from center
            R = ((x - cx)**2 + (y - cy)**2)**0.5

            # --- SENSOR CIRCLE CHECK ---
            if SENSOR_RADIUS - SENSOR_TOL <= R <= SENSOR_RADIUS + SENSOR_TOL:
                sensor_total += 1
                if is_sensor_color(r, g, b):
                    sensor_count += 1

            # --- FR4 RING CHECK ---
            if FR4_INNER <= R <= FR4_OUTER:
                fr4_total += 1
                if is_FR4_color(r, g, b):
                    fr4_count += 1

    # Avoid division by zero
    if sensor_total == 0 or fr4_total == 0:
        return False

    sensor_ratio = sensor_count / sensor_total
    fr4_ratio = fr4_count / fr4_total

    # Thresholds can be tuned
    SENSOR_OK = sensor_ratio > 0.50
    FR4_OK    = fr4_ratio > 0.40

    return SENSOR_OK and FR4_OK
