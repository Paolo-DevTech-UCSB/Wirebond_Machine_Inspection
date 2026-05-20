from ultralytics import YOLO

def main():
    model = YOLO("runs/detect/train/weights/best.pt")

    results = model("test_image.jpg")

    for r in results:
        print(r.boxes)
        r.show()  # display window
        # r.save("output.jpg")  # save annotated image

if __name__ == "__main__":
    main()
