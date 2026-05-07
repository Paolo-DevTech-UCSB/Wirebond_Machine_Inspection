from ultralytics import YOLO

def main():
    # Load a pretrained YOLOv8 model (choose s, m, l, x)
    model = YOLO("yolov8s.pt")

    # Train the model
    results = model.train(
        data="dataset.yaml",   # path to your dataset YAML
        epochs=100,
        imgsz=640,
        batch=16,
        workers=4,
        device=0               # GPU = 0, CPU = "cpu"
    )

    print("Training complete. Best model saved to:", results.save_dir)

if __name__ == "__main__":
    main()
