import cv2
import csv
import os
import statistics
from ultralytics import YOLO

# ============================================================
# SETTINGS
# ============================================================

MODEL_PATH = r"D:\BB2\runs\detect\train4\weights\best.pt"

BASE_DIR = r"D:\2023 Videos\Event100"
VIDEO_PATH = os.path.join(BASE_DIR, "SC300TK83_48s.mov")

OUTPUT_CSV = os.path.join(BASE_DIR, "final_sponge_object_resultsBB.csv")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "final_sponge_outputBB.mp4")
OUTPUT_FRAMES_DIR = os.path.join(BASE_DIR, "validation_framesBB")
README_FILE = os.path.join(BASE_DIR, "README_BB.txt")

CONFIDENCE = 0.28
IOU_THRESHOLD = 0.5

VID_STRIDE = 8
TRACKER_FILE = "botsort.yaml"
MIN_BOX_AREA = 150
LARGE_BOX_FACTOR = 1.8

SHOW_VIDEO = True
STOP_AFTER_FRAME = None

# ============================================================
# README
# ============================================================

def create_readme_file():
    readme_text = f"""
README: Sponge Detection and Tracking Output

Video processed:
{VIDEO_PATH}

Main CSV file:
{OUTPUT_CSV}

This CSV records sponge detections per processed frame using YOLO detection and BoT-SORT tracking.

Settings used:

Confidence threshold:
{CONFIDENCE}

Video stride:
{VID_STRIDE}

Minimum box area:
{MIN_BOX_AREA}

Large box factor:
{LARGE_BOX_FACTOR}

CSV columns:

frame
Frame number from the original video.

track_id
Tracking ID assigned to the detected sponge.

detections_in_frame
Number of sponge detections found by the model in that frame.

status
new = tracking ID appeared for the first time.
existing = tracking ID was already seen before.

time_seconds
Time of the frame in seconds.

confidence
Model confidence score.

IoU threshold:
{IOU_THRESHOLD}

manual_review_needed
yes = the detection box is large compared with other boxes, so it should be checked manually.
no = no manual review flag from box size.

video_name
Name of the video file.
"""

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(readme_text)

    print("README saved to:", README_FILE)

# ============================================================
# SETUP
# ============================================================

print("STARTING SCRIPT")

os.makedirs(OUTPUT_FRAMES_DIR, exist_ok=True)
create_readme_file()

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

if not os.path.exists(VIDEO_PATH):
    raise FileNotFoundError(f"Video not found: {VIDEO_PATH}")

print("Loading model...")
model = YOLO(MODEL_PATH)
print("Model loaded")

print("Video:", VIDEO_PATH)
print("Saving CSV to:", OUTPUT_CSV)
print("Saving video to:", OUTPUT_VIDEO)
print("Saving frames to:", OUTPUT_FRAMES_DIR)
print("Starting processing...\n")

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    raise RuntimeError("Could not open video.")

fps = cap.get(cv2.CAP_PROP_FPS)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

writer = cv2.VideoWriter(
    OUTPUT_VIDEO,
    cv2.VideoWriter_fourcc(*"mp4v"),
    fps if fps > 0 else 25,
    (frame_width, frame_height)
)

rows = []
frame_index = 0
video_name = os.path.basename(VIDEO_PATH)

seen_track_ids = set()
reference_areas = []

# ============================================================
# PROCESS VIDEO
# ============================================================

while True:
    ret, frame = cap.read()

    if not ret:
        break

    if STOP_AFTER_FRAME is not None and frame_index > STOP_AFTER_FRAME:
        print("Stopping early for test.")
        break

    if frame_index % VID_STRIDE != 0:
        frame_index += 1
        continue

    print(f"Processing frame {frame_index}")

    annotated_frame = frame.copy()
    time_seconds = frame_index / fps if fps > 0 else 0

    results = model.track(
        frame,
        persist=True,
        conf=CONFIDENCE,
         iou=IOU_THRESHOLD,
        tracker=TRACKER_FILE,
        verbose=False
    )

    result = results[0]
    current_detections = []

    if result.boxes is not None and result.boxes.id is not None:
        boxes = result.boxes

        ids = boxes.id.int().cpu().tolist()
        confs = boxes.conf.cpu().tolist()
        xyxy = boxes.xyxy.cpu().tolist()

        for track_id, conf, box in zip(ids, confs, xyxy):
            x1, y1, x2, y2 = map(int, box)

            box_width = max(0, x2 - x1)
            box_height = max(0, y2 - y1)
            box_area = box_width * box_height

            if box_area < MIN_BOX_AREA:
                continue

            if track_id not in seen_track_ids:
                status = "new"
                seen_track_ids.add(track_id)
            else:
                status = "existing"

            reference_areas.append(box_area)

            current_detections.append({
                "track_id": track_id,
                "status": status,
                "confidence": float(conf),
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "box_area": box_area
            })

    detections_in_frame = len(current_detections)

    if len(reference_areas) > 0:
        median_area = statistics.median(reference_areas)
    else:
        median_area = 1

    frame_filename = os.path.join(
        OUTPUT_FRAMES_DIR,
        f"{os.path.splitext(video_name)[0]}_frame_{frame_index}.jpg"
    )

    print(f"Frame {frame_index} | Detections: {detections_in_frame}")

    if detections_in_frame == 0:
        rows.append([
            frame_index,
            "",
            0,
            "no_detection",
            time_seconds,
            "",
            "no",
            video_name
        ])

    for det in current_detections:
        if median_area > 0 and det["box_area"] >= LARGE_BOX_FACTOR * median_area:
            manual_review_needed = "yes"
        else:
            manual_review_needed = "no"

        label = f'ID:{det["track_id"]} | conf:{det["confidence"]:.2f}'

        cv2.rectangle(
            annotated_frame,
            (det["x1"], det["y1"]),
            (det["x2"], det["y2"]),
            (0, 255, 0),
            2
        )

        cv2.putText(
            annotated_frame,
            label,
            (det["x1"], max(25, det["y1"] - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )

        rows.append([
            frame_index,
            det["track_id"],
            detections_in_frame,
            det["status"],
            time_seconds,
            det["confidence"],
            manual_review_needed,
            video_name
        ])

    cv2.imwrite(frame_filename, annotated_frame)
    writer.write(annotated_frame)

    if SHOW_VIDEO:
        cv2.imshow("Sponge Tracking", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("Stopped by user.")
            break

    frame_index += 1

cap.release()
writer.release()
cv2.destroyAllWindows()

# ============================================================
# SAVE CSV
# ============================================================

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer_csv = csv.writer(f)

    writer_csv.writerow([
        "frame",
        "track_id",
        "detections_in_frame",
        "status",
        "time_seconds",
        "confidence",
        "manual_review_needed",
        "video_name"
    ])

    writer_csv.writerows(rows)

print("\nDONE")
print("CSV saved to:", OUTPUT_CSV)
print("Video saved to:", OUTPUT_VIDEO)
print("Frames saved to:", OUTPUT_FRAMES_DIR)