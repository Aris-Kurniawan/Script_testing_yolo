# logger.py
# Modul logging latency ke CSV (TABLE V)
# Dipakai oleh: yolo_api.py

import csv, os
from datetime import datetime


class LatencyLogger:
    """
    Menulis dua file CSV:
      - server_latency_<ts>.csv   → stage detection + classification (TABLE V server-side)
      - rerouting_trigger_<ts>.csv → trigger event dari /set_density (TABLE IV supplement)
    """

    def __init__(self, log_dir: str = 'logs/'):
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')

        # ── Server latency log ────────────────────────────────
        self._server_file   = open(
            f'{log_dir}/server_latency_{ts}.csv', 'w', newline='', encoding='utf-8'
        )
        self._server_writer = csv.writer(self._server_file)
        self._server_writer.writerow([
            'timestamp', 'zone_id',
            't1', 't2', 't3',
            't_detect_ms', 't_classify_ms',
            'count', 'level'
        ])
        self._server_file.flush()

        # ── Rerouting trigger log ─────────────────────────────
        self._trigger_file   = open(
            f'{log_dir}/rerouting_trigger_{ts}.csv', 'w', newline='', encoding='utf-8'
        )
        self._trigger_writer = csv.writer(self._trigger_file)
        self._trigger_writer.writerow([
            'event_id', 'zone_id', 't_trigger',
            't_api_received', 'success', 'notes'
        ])
        self._trigger_file.flush()

    # ── Logging API ───────────────────────────────────────────
    def log_server(self, zone_id: str,
                   t1: float, t2: float, t3: float,
                   count: int, level: str) -> None:
        """Catat satu siklus YOLO ke CSV server latency."""
        self._server_writer.writerow([
            datetime.now().isoformat(), zone_id,
            round(t1, 4), round(t2, 4), round(t3, 4),
            round((t2 - t1) * 1000, 2),   # ms deteksi YOLO
            round((t3 - t2) * 1000, 2),   # ms klasifikasi
            count, level
        ])
        self._server_file.flush()

    def log_trigger(self, event_id, zone_id: str,
                    t_trigger: float, t_api_received: float,
                    success: bool, notes: str = '') -> None:
        """Catat satu event trigger rerouting ke CSV trigger log."""
        self._trigger_writer.writerow([
            event_id, zone_id,
            round(t_trigger, 4), round(t_api_received, 4),
            success, notes
        ])
        self._trigger_file.flush()

    def close(self) -> None:
        """Tutup semua file handle (panggil saat server shutdown)."""
        self._server_file.close()
        self._trigger_file.close()
