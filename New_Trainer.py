from ultralytics import YOLO

def main():
    # Load a pretrained YOLOv8 model (choose s, m, l, x)
    model = YOLO("yolov8n.pt")

    # Train the model
    results = model.train(
        data=r"C:\TensorFlow_Datasets\Datasets\Dataset_3_YOLO\dataset.yaml",
        epochs=1,
        imgsz=340,
        batch=16,
        workers=4,
        device="cpu"
    )


    print("Training complete. Best model saved to:", results.save_dir)

if __name__ == "__main__":
    main()
