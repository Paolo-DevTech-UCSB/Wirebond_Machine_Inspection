from PIL import Image, ImageDraw
import os
import Image_Processing_Tools as IPT
import matplotlib.pyplot as plt
import numpy as np

from scipy.ndimage import median_filter, grey_opening

from scipy.signal import find_peaks

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def compute_new_center(img, shift=45, k=5):
    """
    Computes the NEW center using:
      - sensor mask
      - contiguity histograms
      - overlap-cube filter
      - peak detection
      - weighted peak center (recommended)
    """

    mask = sensor_mask(img)

    # Raw histograms
    row_hist_raw = row_contiguity_hist(mask)
    col_hist_raw = col_contiguity_hist(mask)

    # Overlap-cube filtering
    _, _, _, row_g_raw, _ = overlap_cube_filter(row_hist_raw, shift=shift)
    _, _, _, col_g_raw, _ = overlap_cube_filter(col_hist_raw, shift=shift)

    # Peak detection
    row_peaks, _, _ = find_filtered_peaks(row_g_raw)
    col_peaks, _, _ = find_filtered_peaks(col_g_raw)

    # Weighted peak center (best stability)
    cx = weighted_peak_center(col_g_raw, col_peaks, k=k)
    cy = weighted_peak_center(row_g_raw, row_peaks, k=k)

    return cx, cy



def debug_overlap_cube_filter(hist, shift=45, eps=0.0):
    print("\n==============================")
    print(" DEBUG: OVERLAP CUBE FILTER ")
    print("==============================")

    h = np.array(hist, dtype=float)
    print(f"Raw hist length: {len(h)}")
    print(f"Raw hist max: {h.max()}, min: {h.min()}")

    # Add epsilon if requested
    if eps != 0:
        print(f"Adding epsilon: {eps}")
        h = h + eps

    # Pad
    pad = np.zeros(shift)
    hpad = np.concatenate([pad, h, pad])
    print(f"Padded length: {len(hpad)}")

    # Extract shifted versions
    f0 = hpad[shift:-shift]
    f1 = hpad[2*shift:]
    f2 = hpad[:-2*shift]

    print(f"f0 length: {len(f0)}, f1 length: {len(f1)}, f2 length: {len(f2)}")
    print(f"f0 max/min: {f0.max()}/{f0.min()}")
    print(f"f1 max/min: {f1.max()}/{f1.min()}")
    print(f"f2 max/min: {f2.max()}/{f2.min()}")

    # Compute product BEFORE normalization
    g_raw = f0 * f1 * f2
    print(f"g_raw max/min: {g_raw.max()}/{g_raw.min()}")

    # Normalize for plotting
    if g_raw.max() > 0:
        g = g_raw / g_raw.max()
    else:
        g = g_raw.copy()

    print(f"g normalized max/min: {g.max()}/{g.min()}")

    print("==============================\n")

    return f0, f1, f2, g_raw, g



# ---------------------------------------------------------
# 1. SENSOR MASK
# ---------------------------------------------------------
def sensor_mask(img):
    arr = np.array(img)
    R, G, B = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    mask = (
        (100 <= R) & (R <= 185) &
        (165 <= G) & (G <= 240) &
        (215 <= B) & (B <= 255) &
        (B > G) & (G > R)
    )
    return mask


# ---------------------------------------------------------
# 2. CONTIGUITY HISTOGRAMS
# ---------------------------------------------------------
def row_contiguity_hist(mask):
    H, W = mask.shape
    runs = np.zeros(H, dtype=int)

    for y in range(H):
        row = mask[y]
        max_run = 0
        current = 0
        for v in row:
            if v:
                current += 1
                max_run = max(max_run, current)
            else:
                current = 0
        runs[y] = max_run

    return runs


def col_contiguity_hist(mask):
    H, W = mask.shape
    runs = np.zeros(W, dtype=int)

    for x in range(W):
        col = mask[:,x]
        max_run = 0
        current = 0
        for v in col:
            if v:
                current += 1
                max_run = max(max_run, current)
            else:
                current = 0
        runs[x] = max_run

    return runs


# ---------------------------------------------------------
# 3. OVERLAP-CUBE FILTER (your idea)
# ---------------------------------------------------------
def overlap_cube_filter(hist, shift=45, eps=0.1):
    """
    Wide-structure detector using shifted products.
    g_raw = f(x) * f(x+shift) * f(x-shift)
    g_vis = cbrt(g_raw) normalized for plotting
    """
    h = np.array(hist, dtype=float)

    # avoid zero-collapse
    h = h + eps

    # pad with eps
    pad = np.ones(shift) * eps
    hpad = np.concatenate([pad, h, pad])

    # shifted versions
    f0 = hpad[shift:-shift]
    f1 = hpad[2*shift:]
    f2 = hpad[:-2*shift]

    # raw product (for peak detection)
    g_raw = f0 * f1 * f2

    # cube-root compression for visibility
    g_vis = np.cbrt(g_raw)
    if g_vis.max() > 0:
        g_vis = g_vis / g_vis.max()

    return f0, f1, f2, g_raw, g_vis



# ---------------------------------------------------------
# 4. PEAK DETECTION (on amplified histogram)
# ---------------------------------------------------------
def find_filtered_peaks(hist, min_prominence=0.05, min_width=3):
    """
    Detect peaks using prominence + width filtering.
    Returns accepted peaks, rejected peaks, and peak properties.
    """
    peaks, props = find_peaks(hist, prominence=min_prominence, width=min_width)

    # raw peaks (no filtering)
    all_peaks, _ = find_peaks(hist)

    rejected = [p for p in all_peaks if p not in peaks]

    return peaks, rejected, props


# ---------------------------------------------------------
# 5. PEAK-BASED CENTER ESTIMATION
# ---------------------------------------------------------
def top_k_center(hist, peaks, k=5):
    if len(peaks) == 0:
        return None
    sorted_peaks = sorted(peaks, key=lambda p: hist[p], reverse=True)
    top = sorted_peaks[:k]
    return float(np.mean(top))


def weighted_peak_center(hist, peaks, k=5):
    if len(peaks) == 0:
        return None
    sorted_peaks = sorted(peaks, key=lambda p: hist[p], reverse=True)
    top = sorted_peaks[:k]
    weights = np.array([hist[p] for p in top], dtype=float)
    positions = np.array(top, dtype=float)
    return float(np.average(positions, weights=weights))


# ---------------------------------------------------------
# 6. MASS BAND (unchanged)
# ---------------------------------------------------------
def find_mass_band(hist, low_frac=0.10, high_frac=0.90):
    integral = np.cumsum(hist)
    total = integral[-1]

    if total == 0:
        return 0, len(hist)-1

    low_idx = np.searchsorted(integral, low_frac * total)
    high_idx = np.searchsorted(integral, high_frac * total)

    return low_idx, high_idx


# ---------------------------------------------------------
# 7. MAIN DEBUG VISUALIZATION
# ---------------------------------------------------------
def debug_integral_bands(img):
    arr = np.array(img)
    mask = sensor_mask(img)

        # Raw histograms
    row_hist_raw = row_contiguity_hist(mask)
    col_hist_raw = col_contiguity_hist(mask)

    # DEBUG: inspect overlap behavior
    #debug_overlap_cube_filter(row_hist_raw, shift=45)
    #debug_overlap_cube_filter(col_hist_raw, shift=45)


    # Overlap-cube filtering (returns f0, f+, f-, g)
    # Overlap-cube filtering (returns f0, f+, f-, g_raw, g_vis)
    r0, r_plus, r_minus, row_g_raw, row_g = overlap_cube_filter(row_hist_raw, shift=45)
    c0, c_plus, c_minus, col_g_raw, col_g = overlap_cube_filter(col_hist_raw, shift=45)


    # Peak detection on amplified histograms
    row_peaks, row_rejected, _ = find_filtered_peaks(row_g_raw)
    col_peaks, col_rejected, _ = find_filtered_peaks(col_g_raw)



    # Peak-based centers
    peak_center_y = top_k_center(row_g_raw, row_peaks, k=5)
    peak_center_x = top_k_center(col_g_raw, col_peaks, k=5)

    weighted_center_y = weighted_peak_center(row_g_raw, row_peaks, k=5)
    weighted_center_x = weighted_peak_center(col_g_raw, col_peaks, k=5)

    # Mass bands (still based on raw histogram)
    y_low, y_high = find_mass_band(row_hist_raw)
    x_low, x_high = find_mass_band(col_hist_raw)

    # COM inside band
    band_mask = mask.copy()
    band_mask[:y_low, :] = False
    band_mask[y_high:, :] = False
    band_mask[:, :x_low] = False
    band_mask[:, x_high:] = False

    ys, xs = np.where(band_mask)
    com_x = xs.mean() if len(xs) else None
    com_y = ys.mean() if len(ys) else None

        # -----------------------------------------------------
    # PLOTTING
    # -----------------------------------------------------
    fig, axs = plt.subplots(2, 3, figsize=(16, 10))

    # Original
    axs[0,0].imshow(arr)
    axs[0,0].set_title("Original Image")
    axs[0,0].axis("off")

    # Mask overlay + centers
    overlay = arr.copy()
    overlay[mask] = [255, 0, 255]
    axs[0,1].imshow(overlay)
    axs[0,1].set_title("Mask + Centers")
    axs[0,1].axis("off")

    # COM
    if com_x is not None:
        axs[0,1].plot(com_x, com_y, 'bo', markersize=10)
        axs[0,1].text(com_x, com_y, "COM", color='blue')

    # Peak center
    if peak_center_x is not None:
        axs[0,1].plot(peak_center_x, peak_center_y, 'go', markersize=10)
        axs[0,1].text(peak_center_x, peak_center_y, "PEAK CTR", color='green')

    # Weighted peak center
    if weighted_center_x is not None:
        axs[0,1].plot(weighted_center_x, weighted_center_y, 'yo', markersize=10)
        axs[0,1].text(weighted_center_x, weighted_center_y, "W-PEAK CTR", color='yellow')

    # -----------------------------------------------------
    # ROW HISTOGRAM + g(x)
    # -----------------------------------------------------
    axs[0,2].plot(r0, color='gray', label="f(x)")
    axs[0,2].plot(r_plus, color='blue', alpha=0.6, label="f(x+10)")
    axs[0,2].plot(r_minus, color='purple', alpha=0.6, label="f(x-10)")
    axs[0,2].plot(row_g, color='black', linewidth=2, label="g(x) cube-root")

    axs[0,2].plot(row_peaks, row_g[row_peaks], 'go', label="accepted peaks")
    axs[0,2].plot(row_rejected, row_g[row_rejected], 'ro', label="rejected peaks")

    axs[0,2].set_title("Row Histogram: f(x), f(x±10), g(x) compressed")
    axs[0,2].legend()

    # -----------------------------------------------------
    # COLUMN HISTOGRAM + g(x)
    # -----------------------------------------------------
    axs[1,0].plot(c0, color='gray', label="f(x)")
    axs[1,0].plot(c_plus, color='blue', alpha=0.6, label="f(x+10)")
    axs[1,0].plot(c_minus, color='purple', alpha=0.6, label="f(x-10)")
    axs[1,0].plot(col_g, color='black', linewidth=2, label="g(x) cube-root")

    axs[1,0].plot(col_peaks, col_g[col_peaks], 'go', label="accepted peaks")
    axs[1,0].plot(col_rejected, col_g[col_rejected], 'ro', label="rejected peaks")

    axs[1,0].set_title("Column Histogram: f(x), f(x±10), g(x) compressed")
    axs[1,0].legend()

    # -----------------------------------------------------
    # REPLACE INTEGRAL PLOTS WITH g(x)
    # -----------------------------------------------------
    axs[1,1].plot(row_g, color='black')
    axs[1,1].set_title("Row g(x) (cube-root compressed)")

    axs[1,2].plot(col_g, color='black')
    axs[1,2].set_title("Column g(x) (cube-root compressed)")

    plt.tight_layout()
    #plt.show()


    return {
        "row_band": (y_low, y_high),
        "col_band": (x_low, x_high),
        "com": (com_x, com_y),
        "peak_center": (peak_center_x, peak_center_y),
        "weighted_peak_center": (weighted_center_x, weighted_center_y),
        "new_center": (weighted_center_x, weighted_center_y),
        "row_peaks": row_peaks,
        "col_peaks": col_peaks,
        "row_rejected": row_rejected,
        "col_rejected": col_rejected
    }



###########################################

def is_sensor_color(r, g, b):
    return (
        70 <= r <= 190 and     # widened for new high-R samples
        140 <= g <= 240 and    # widened for new high-G samples
        180 <= b <= 255 and    # widened for new high-B samples
        b > g > r              # preserve the strong channel ordering
    )


    #This color threshold is not locating the sensorpixels correctly



def garbage_sensor_com(img, debug_mark=False):
    W, H = img.size
    pix = img.load()
    # --- ADD THESE THREE LINES ---
    sum_x = 0
    sum_y = 0
    count = 0
    # -----------------------------

    for y in range(H):
        for x in range(W):
            r, g, b = pix[x, y]
            if is_sensor_color(r, g, b):
                sum_x += x
                sum_y += y
                count += 1
                if debug_mark:
                    # Paint the pixel bright pink so it stands out
                    pix[x, y] = (255, 0, 255) 
    
    if count == 0:
        return None, None, 0

    return sum_x / count, sum_y / count, count

def garbage_filter(img, debug=True):
    """
    Uses the NEW noise-filtered, peak-based center instead of the old COM.
    """

    # 1. Compute new center
    COMX, COMY = compute_new_center(img)

    if COMX is None or COMY is None:
        print("New center could not be computed.")
        return True

    width, height = img.size

    # Expected bounds
    min_x = 185
    max_x = 1415
    min_y = 185 + 350
    max_y = 1200 - 185

    # 2. Debug visualization
    if debug:
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.imshow(img)
        ax.set_title(f"Garbage Filter Debug\nNEW CTR=({COMX:.1f}, {COMY:.1f})")

        # Plot new center
        ax.scatter([COMX], [COMY], c='red', s=40, label="NEW CENTER", edgecolors='white')

        # Bounding box
        rect_x = [min_x, max_x, max_x, min_x, min_x]
        rect_y = [min_y, min_y, max_y, max_y, min_y]
        ax.plot(rect_x, rect_y, 'g-', linewidth=2, label="Allowed COM Region")

        ax.legend()
        #plt.show()

    # 3. Size check
    if width != 1600 or height != 1200:
        print("Warning: Image size incorrect.")
        return True

    # 4. Bounds check
    if COMX < min_x or COMX > max_x or COMY < min_y or COMY > max_y:
        print(f"NEW CENTER OUT OF BOUNDS → X:{COMX:.1f}, Y:{COMY:.1f}")
        return True

    return False

