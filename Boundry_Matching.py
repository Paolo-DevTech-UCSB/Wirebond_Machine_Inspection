# Boundry_matching.py

def boxes_overlap(boxA, boxB):
    """
    Returns True if two bounding boxes overlap.
    Boxes are in [x1, y1, x2, y2] format.
    """

    ax1, ay1, ax2, ay2 = boxA
    bx1, by1, bx2, by2 = boxB

    # Compute overlap
    overlap_x = max(0, min(ax2, bx2) - max(ax1, bx1))
    overlap_y = max(0, min(ay2, by2) - max(ay1, by1))

    return overlap_x > 0 and overlap_y > 0


def find_threebond_overlaps(detections):
    """
    detections = list of tuples:
        (cls_id, [x1, y1, x2, y2])

    Returns:
        overlaps = list of (threebond_box, other_box)
    """

    THREE_BONDS = 4

    threebond_boxes = []
    other_boxes = []

    for cls_id, box in detections:
        if cls_id == THREE_BONDS:
            threebond_boxes.append(box)
        else:
            other_boxes.append((cls_id, box))

    overlaps = []

    for tb in threebond_boxes:
        for cls_id, obox in other_boxes:
            if boxes_overlap(tb, obox):
                overlaps.append((tb, (cls_id, obox)))

    return overlaps


def main(detections_by_image):
    """
    detections_by_image = dict:
        {
            "IMG_001.png": [
                (cls_id, [x1, y1, x2, y2]),
                ...
            ],
            ...
        }

    Returns:
        overlap_report = dict:
            {
                "IMG_001.png": [ (threebond_box, (cls_id, other_box)), ... ],
                ...
            }
    """

    overlap_report = {}

    for img_name, dets in detections_by_image.items():
        overlaps = find_threebond_overlaps(dets)
        if overlaps:
            overlap_report[img_name] = overlaps

    return overlap_report
