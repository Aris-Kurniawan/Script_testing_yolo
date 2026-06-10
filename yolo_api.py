# yolo_api.py
# Main Flask server — Crowd Detection System (IEES)
#
# Modul yang dipakai:
#   classifier.py   → DensityClassifier
#   zone_manager.py → ZoneManager
#   logger.py       → LatencyLogger
#
# Endpoint:
#   GET  /api/human          → backward compat Unity lama
#   GET  /density/<zone_id>  → test_classification.py, test_latency.py, NavigationBridge.cs
#   POST /set_density        → test_rerouting.py, test_latency.py

from flask import Flask, jsonify, request
from ultralytics import YOLO
from datetime import datetime
import cv2, threading, time

# ── Import modul lokal ─────────────────────────────────────
from classifier  import DensityClassifier
from zone_manager import ZoneManager
from logger      import LatencyLogger

# ── Inisialisasi Flask ─────────────────────────────────────
app = Flask(__name__)

# ── Konfigurasi threshold density ─────────────────────────
#    N1 = batas atas Low    (0 .. N1  orang → Low)
#    N2 = batas atas Medium (N1+1 .. N2 orang → Medium)
#                           (> N2 orang → High)
N1 = 5
N2 = 10

# ── Inisialisasi modul ─────────────────────────────────────
classifier   = DensityClassifier(n1=N1, n2=N2)
zone_mgr     = ZoneManager(K=2, M=3)
logger       = LatencyLogger(log_dir='logs/')

# State global jumlah orang (dipertahankan untuk /api/human backward compat)
jumlah_orang_sekarang = 0


# ══════════════════════════════════════════════════════════
# YOLO THREAD — berjalan sebagai daemon thread
# ══════════════════════════════════════════════════════════
def jalankan_yolo(url_kamera, zone_id: str = 'zone_A'):
    """
    Thread utama untuk menjalankan inferensi YOLOv8 secara terus-menerus.
    Setiap siklus (1 dari 10 frame) akan:
      1. Mendeteksi manusia (class 0)
      2. Mengklasifikasi density
      3. Update ZoneManager
      4. Log ke CSV melalui LatencyLogger
    """
    global jumlah_orang_sekarang

    # Load model — ganti ke yolov8s.pt untuk akurasi lebih baik
    model = YOLO('yolov8n.pt')

    cap         = cv2.VideoCapture(url_kamera)
    frame_count = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue

        frame_count += 1

        # Ambil 1 frame dari 10 (hemat resource)
        if frame_count % 10 != 0:
            continue

        # ── t1: frame masuk YOLO ──────────────────────────
        t1 = time.time()

        # Deteksi — classes=0 hanya manusia
        results = model(frame, classes=[0], conf=0.5,
                        imgsz=320, verbose=False)

        # ── t2: deteksi selesai ───────────────────────────
        t2 = time.time()

        for r in results:
            jumlah_orang_sekarang = len(r.boxes)

        # Klasifikasi density
        level = classifier.classify(jumlah_orang_sekarang)

        # ── t3: klasifikasi selesai ───────────────────────
        t3 = time.time()

        t_detect_ms   = round((t2 - t1) * 1000, 2)
        t_classify_ms = round((t3 - t2) * 1000, 2)

        # Update state zona
        zone_mgr.update(
            zone_id, level, jumlah_orang_sekarang,
            t_detect_ms=t_detect_ms, t_classify_ms=t_classify_ms
        )

        # Log ke CSV (TABLE V)
        logger.log_server(zone_id, t1, t2, t3,
                          jumlah_orang_sekarang, level)

        print(f"[YOLO] {zone_id}: {jumlah_orang_sekarang} orang "
              f"| {level} | detect={t_detect_ms}ms classify={t_classify_ms}ms")


# ══════════════════════════════════════════════════════════
# ENDPOINT 1 — Backward compat Unity lama
# ══════════════════════════════════════════════════════════
@app.route('/api/human', methods=['GET'])
def get_crowd_data():
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    is_crowded     = jumlah_orang_sekarang > N2

    return jsonify({
        "status":       "success",
        "rute_1_human": jumlah_orang_sekarang,
        "crowded":      is_crowded,
        "timestamp":    waktu_sekarang
    })


# ══════════════════════════════════════════════════════════
# ENDPOINT 2 — Utama untuk testing & Unity baru
# Dipakai: test_classification.py, test_latency.py, NavigationBridge.cs
# ══════════════════════════════════════════════════════════
@app.route('/density/<zone_id>', methods=['GET'])
def get_zone_density(zone_id):
    """
    Response field yang DIBUTUHKAN testing script:
      - level          → test_classification.py, test_latency.py
      - count          → test_latency.py
      - last_updated   → test_latency.py (data.get('last_updated', ...))
      - t_classify_ms  → test_latency.py (data.get('t_classify_ms', 0))
      - t_detect_ms    → test_latency.py (data.get('t_detect_ms', 0))
      - t_server       → NavigationBridge.cs
    """
    state = zone_mgr.get_state(zone_id)

    return jsonify({
        "zone_id":       zone_id,
        "count":         state.get('count', jumlah_orang_sekarang),
        "level":         state.get('level', classifier.classify(jumlah_orang_sekarang)),
        "t_server":      time.time(),
        "last_updated":  state.get('last_updated', time.time()),
        "t_detect_ms":   state.get('t_detect_ms',   0.0),
        "t_classify_ms": state.get('t_classify_ms', 0.0),
        "timestamp":     datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


# ══════════════════════════════════════════════════════════
# ENDPOINT 3 — Inject density untuk testing
# Dipakai: test_rerouting.py (TABLE IV), test_latency.py (TABLE V)
# ══════════════════════════════════════════════════════════
@app.route('/set_density', methods=['POST'])
def set_density():
    """
    Body JSON: { "zone": "zone_A", "level": "High" }
    Level: 'Low' | 'Medium' | 'High'
    """
    global jumlah_orang_sekarang

    body  = request.json
    level = body.get('level', 'Low')
    zone  = body.get('zone',  'zone_A')

    # Tentukan jumlah orang sesuai level yang diinject
    if level == 'High':
        count = N2 + 5       # contoh: 15 orang
    elif level == 'Medium':
        count = N1 + 3       # contoh: 8 orang
    else:
        count = 0

    # Update state global & ZoneManager
    jumlah_orang_sekarang = count
    zone_mgr.force_set(zone, level, count=count)

    t_received = time.time()

    # Log trigger event
    logger.log_trigger(
        event_id=f"{zone}_{int(t_received)}",
        zone_id=zone,
        t_trigger=t_received,
        t_api_received=t_received,
        success=True,
        notes=f'inject {level}'
    )

    print(f"[INJECT] zone={zone} level={level} count={count}")

    return jsonify({
        "status": "ok",
        "level":  level,
        "count":  count,
        "zone":   zone
    })


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 50)
    print("       CROWD DETECTION SERVER  (IEES)")
    print("=" * 50)
    print("Format IP Webcam : http://xxx.xxx.x.xx:xxxx/video")
    print("Format Webcam    : 0")
    print()

    input_user = input("Input URL Kamera: ")

    if input_user.isdigit():
        input_user = int(input_user)

    # Daftarkan zona awal
    zone_mgr.register_zone('zone_A')

    yolo_thread = threading.Thread(
        target=jalankan_yolo,
        args=(input_user, 'zone_A')
    )
    yolo_thread.daemon = True
    yolo_thread.start()

    print()
    print("Endpoints tersedia:")
    print("  GET  /api/human          -> backward compat Unity lama")
    print("  GET  /density/<zone_id>  -> test_classification.py & NavigationBridge.cs")
    print("  POST /set_density        -> test_rerouting.py & test_latency.py")
    print()
    print("Buka di http://localhost:5000/api/human")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000)