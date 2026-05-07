from ultralytics import YOLO

def main():
    model = YOLO("runs/detect/train/weights/best.pt")

    # Export to multiple formats
    model.export(format="onnx")
    model.export(format="tflite")
    model.export(format="engine")  # TensorRT

    print("Export complete.")

if __name__ == "__main__":
    main()
