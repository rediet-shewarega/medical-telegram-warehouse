from pathlib import Path
import pandas as pd
from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_DIR = BASE_DIR / "data" / "raw" / "images"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "yolo_detections.csv"


def classify_image(detected_classes):
    """
    Simple classification rule:
    - promotional: person + product-like object
    - product_display: product-like object but no person
    - lifestyle: person but no product-like object
    - other: neither
    """

    detected_classes = set(detected_classes)

    person_detected = "person" in detected_classes

    product_like_objects = {
        "bottle",
        "cup",
        "cell phone",
        "book",
        "box",
        "container",
        "vase",
        "scissors",
        "toothbrush",
    }

    product_detected = len(detected_classes.intersection(product_like_objects)) > 0

    if person_detected and product_detected:
        return "promotional"
    elif product_detected and not person_detected:
        return "product_display"
    elif person_detected and not product_detected:
        return "lifestyle"
    else:
        return "other"


def run_yolo_detection():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model = YOLO("yolov8n.pt")

    image_paths = list(IMAGE_DIR.glob("*/*.jpg"))

    print(f"Found {len(image_paths)} images")

    records = []

    for image_path in image_paths:
        channel_name = image_path.parent.name
        message_id = image_path.stem

        try:
            results = model(image_path, verbose=False)

            detected_classes = []
            max_confidence = 0.0

            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    confidence = float(box.conf[0])

                    detected_classes.append(class_name)
                    max_confidence = max(max_confidence, confidence)

                    records.append(
                        {
                            "message_id": message_id,
                            "channel_name": channel_name,
                            "image_path": str(image_path),
                            "detected_class": class_name,
                            "confidence_score": confidence,
                            "image_category": None,
                        }
                    )

            image_category = classify_image(detected_classes)

            if detected_classes:
                for record in records:
                    if (
                        record["message_id"] == message_id
                        and record["channel_name"] == channel_name
                    ):
                        record["image_category"] = image_category
            else:
                records.append(
                    {
                        "message_id": message_id,
                        "channel_name": channel_name,
                        "image_path": str(image_path),
                        "detected_class": "none",
                        "confidence_score": 0.0,
                        "image_category": "other",
                    }
                )

        except Exception as e:
            print(f"Error processing {image_path}: {e}")

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved detection results to {OUTPUT_FILE}")
    print(f"Total detection rows: {len(df)}")


if __name__ == "__main__":
    run_yolo_detection()