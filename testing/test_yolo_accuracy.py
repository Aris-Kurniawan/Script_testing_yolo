from ultralytics import YOLO
import time, csv

def run_yolo_evaluation(model_path, dataset_yaml, output_csv):
    model = YOLO(model_path)

    # Jalankan validasi — menghasilkan semua metrik sekaligus
    metrics = model.val(
        data=dataset_yaml,
        imgsz=640,
        conf=0.5,
        iou=0.5,
        verbose=True
    )

    # Ukur inference time dari 100 frame sample
    import cv2, glob
    image_files = glob.glob('dataset/images/test/*.jpg')[:100]
    infer_times = []

    for img_path in image_files:
        frame = cv2.imread(img_path)
        t_start = time.time()
        model(frame, classes=[0], conf=0.5, verbose=False)
        infer_times.append((time.time() - t_start) * 1000)

    avg_infer = sum(infer_times) / len(infer_times)
    min_infer = min(infer_times)
    max_infer = max(infer_times)

    # Simpan ke CSV untuk TABLE II
    results = {
        'mAP@0.5':          round(metrics.box.map50 * 100, 2),
        'mAP@0.5:0.95':     round(metrics.box.map * 100, 2),
        'Precision':        round(metrics.box.mp * 100, 2),
        'Recall':           round(metrics.box.mr * 100, 2),
        'F1':               round(2 * metrics.box.mp * metrics.box.mr /
                                  (metrics.box.mp + metrics.box.mr + 1e-6), 4),
        'Avg_Inference_ms': round(avg_infer, 2),
        'Min_Inference_ms': round(min_infer, 2),
        'Max_Inference_ms': round(max_infer, 2),
    }

    with open(output_csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=results.keys())
        w.writeheader()
        w.writerow(results)

    print("=== TABLE II RESULTS ===")
    for k, v in results.items():
        print(f"  {k}: {v}")

    return results

if __name__ == '__main__':
    run_yolo_evaluation(
        model_path='yolov8s.pt',
        dataset_yaml='dataset/dataset.yaml',
        output_csv='logs/table2_yolo_accuracy.csv'
    )