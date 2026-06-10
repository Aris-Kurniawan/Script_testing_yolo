# zone_manager.py
# Modul manajemen state setiap zona (multi-zona + hysteresis)
# Dipakai oleh: yolo_api.py

import time


class ZoneManager:
    """
    Menyimpan state setiap zona dan menghitung hysteresis counter.

    Parameter
    ---------
    K : int
        Minimum cycle High sebelum obstacle aktif (hysteresis naik)
    M : int
        Minimum cycle non-High sebelum obstacle nonaktif (hysteresis turun)
    """

    def __init__(self, K: int = 2, M: int = 3):
        self.K     = K
        self.M     = M
        self.zones: dict = {}
        # Simpan latency terakhir per zona untuk diekspos ke /density/<zone_id>
        self._latency: dict = {}

    # ── Registrasi ──────────────────────────────────────────
    def register_zone(self, zone_id: str) -> None:
        self.zones[zone_id] = {
            'level':          'Low',
            'count':          0,
            'h_count':        0,
            'l_count':        0,
            'obstacle_active': False,
            'last_updated':   time.time(),
        }
        self._latency[zone_id] = {'t_detect_ms': 0.0, 't_classify_ms': 0.0}

    # ── Update dari YOLO thread ──────────────────────────────
    def update(self, zone_id: str, level: str, count: int,
               t_detect_ms: float = 0.0, t_classify_ms: float = 0.0) -> None:
        """Dipanggil setiap siklus YOLO dengan hasil deteksi terbaru."""
        if zone_id not in self.zones:
            self.register_zone(zone_id)

        z = self.zones[zone_id]
        z['level']        = level
        z['count']        = count
        z['last_updated'] = time.time()

        # Hysteresis counter
        if level == 'High':
            z['h_count'] += 1
            z['l_count']  = 0
        else:
            z['l_count'] += 1
            z['h_count']  = 0

        # Simpan latency terakhir
        self._latency[zone_id]['t_detect_ms']   = t_detect_ms
        self._latency[zone_id]['t_classify_ms'] = t_classify_ms

    # ── Force inject (untuk testing: /set_density) ───────────
    def force_set(self, zone_id: str, level: str, count: int = None) -> None:
        """
        Inject langsung state zona — dipakai oleh test_rerouting.py
        dan test_latency.py melalui endpoint POST /set_density.
        """
        if zone_id not in self.zones:
            self.register_zone(zone_id)

        z = self.zones[zone_id]
        z['level']        = level
        z['last_updated'] = time.time()

        if count is not None:
            z['count'] = count

        # Set hysteresis agar langsung aktif
        if level == 'High':
            z['h_count'] = self.K
            z['l_count'] = 0
        else:
            z['l_count'] = self.M
            z['h_count'] = 0

    # ── Getter ───────────────────────────────────────────────
    def get_state(self, zone_id: str) -> dict:
        """Return state satu zona (dict), atau dict kosong jika belum ada."""
        if zone_id not in self.zones:
            self.register_zone(zone_id)
        z    = self.zones[zone_id]
        lat  = self._latency.get(zone_id, {})
        return {
            'level':         z['level'],
            'count':         z['count'],
            'h_count':       z['h_count'],
            'l_count':       z['l_count'],
            'last_updated':  z['last_updated'],
            't_detect_ms':   lat.get('t_detect_ms',   0.0),
            't_classify_ms': lat.get('t_classify_ms', 0.0),
        }

    def get_all_states(self) -> dict:
        """Return state semua zona yang terdaftar."""
        return {zid: self.get_state(zid) for zid in self.zones}
