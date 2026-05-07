from ultralytics import YOLO

def main():
    model = YOLO("runs/detect/train/weights/best.pt")

    results = model.val()
    print("Validation complete.")

if __name__ == "__main__":
    main()
