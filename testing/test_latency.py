import requests, csv, time, statistics, os
from datetime import datetime

FLASK_URL  = 'http://localhost:5000'
OUTPUT_CSV = 'logs/table5_latency.csv'
N_TRIALS   = 30

def run_latency_test():
    os.makedirs('logs', exist_ok=True)
    records = []

    print("\n" + "="*50)
    print("RUNNING SYSTEM LATENCY BENCHMARK (TABLE V)")
    print("="*50)

    # Ping server
    try:
        requests.get(f'{FLASK_URL}/density')
    except requests.exceptions.ConnectionError:
        print(f"Error: Flask server is not running at {FLASK_URL}. Please start the server first.")
        return

    for trial in range(1, N_TRIALS + 1):
        print(f"Trial {trial}/{N_TRIALS}...")

        # Inject High density untuk memicu pipeline penuh
        t_inject = time.time()
        requests.post(f'{FLASK_URL}/set_density',
                      json={'zone': 'zone_A', 'level': 'High'})

        # Poll API — ukur waktu round-trip API
        t_poll_start = time.time()
        resp = requests.get(f'{FLASK_URL}/density/zone_A')
        t_poll_end   = time.time()
        data = resp.json()

        # Ambil timestamp server dari response
        t_server = data.get('last_updated', t_poll_start)

        # Hitung latency per stage (ms)
        t_api_roundtrip = (t_poll_end - t_poll_start) * 1000
        t_classify      = data.get('t_classify_ms', 0)
        t_detect        = data.get('t_detect_ms', 0)

        records.append({
            'trial':            trial,
            't_detect_ms':      round(t_detect, 2),
            't_classify_ms':    round(t_classify, 2),
            't_api_ms':         round(t_api_roundtrip, 2),
            # NavMesh & AR update diambil dari Unity LatencyLogger
            # dan digabung setelah pengujian selesai
            'timestamp':        datetime.now().isoformat()
        })

        # Reset zona
        requests.post(f'{FLASK_URL}/set_density',
                      json={'zone': 'zone_A', 'level': 'Low'})
        time.sleep(1.5)

    # Hitung Min/Avg/Max per stage
    def stats(key):
        vals = [r[key] for r in records]
        return min(vals), round(statistics.mean(vals), 2), max(vals)

    d_min, d_avg, d_max = stats('t_detect_ms')
    c_min, c_avg, c_max = stats('t_classify_ms')
    a_min, a_avg, a_max = stats('t_api_ms')

    with open(OUTPUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=records[0].keys())
        w.writeheader()
        w.writerows(records)

    print("\n=== TABLE V: LATENCY RESULTS (Server-side) ===")
    print(f"{'Stage':<35} {'Min':>8} {'Avg':>8} {'Max':>8}")
    print(f"{'Camera → YOLOv8 detection':<35} {d_min:>8} {d_avg:>8} {d_max:>8}")
    print(f"{'Detection → Classification':<35} {c_min:>8} {c_avg:>8} {c_max:>8}")
    print(f"{'Classification → API response':<35} {a_min:>8} {a_avg:>8} {a_max:>8}")
    print("(NavMesh carve & AR update: lihat Unity LatencyLogger log)")

if __name__ == '__main__':
    run_latency_test()
