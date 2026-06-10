import requests, csv, time
from datetime import datetime

FLASK_URL  = 'http://localhost:5000'
OUTPUT_CSV = 'logs/table4_rerouting.csv'

def run_rerouting_test(test_cases):
    """
    test_cases = list of dict:
    [
      {'event_id': 1, 'zone': 'zone_B',
       'route': 'Lobby → Ruang Seminar',
       'has_alternative': True},
      ...
    ]
    """
    results = []

    for tc in test_cases:
        print(f"\nEvent {tc['event_id']}: Zona {tc['zone']}")
        print(f"Rute: {tc['route']}")
        input("Pastikan navigasi aktif di Unity, tekan Enter...")

        # Inject High density ke zona target
        t_trigger = time.time()
        requests.post(f'{FLASK_URL}/set_density',
                      json={'zone': tc['zone'], 'level': 'High'})
        print("  High density diinjeksi, menunggu respons Unity...")

        # Tunggu konfirmasi dari tester
        time.sleep(3)
        success = input("  Apakah rute baru tampil menghindari zona? (y/n): ")
        false_t = input("  Apakah ini false trigger (zona sebenarnya tidak padat)? (y/n): ")

        # Reset zona
        requests.post(f'{FLASK_URL}/set_density',
                      json={'zone': tc['zone'], 'level': 'Low'})
        time.sleep(2)
        restored = input("  Apakah rute kembali ke jalur semula? (y/n): ")

        results.append({
            'event_id':        tc['event_id'],
            'zone':            tc['zone'],
            'route':           tc['route'],
            'has_alternative': tc['has_alternative'],
            't_trigger':       t_trigger,
            'successful':      success.lower() == 'y',
            'false_trigger':   false_t.lower() == 'y',
            'route_restored':  restored.lower() == 'y',
            'timestamp':       datetime.now().isoformat()
        })

    # Hitung ringkasan
    total     = len(results)
    success_n = sum(1 for r in results if r['successful'])
    failed_n  = total - success_n
    false_n   = sum(1 for r in results if r['false_trigger'])
    restored_n= sum(1 for r in results if r['route_restored'])

    with open(OUTPUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)

    print("\n=== TABLE IV: REROUTING RESULTS ===")
    print(f"  Total trigger events    : {total}")
    print(f"  Successful reroute      : {success_n} ({success_n/total*100:.1f}%)")
    print(f"  Failed reroute          : {failed_n} ({failed_n/total*100:.1f}%)")
    print(f"  False trigger           : {false_n} ({false_n/total*100:.1f}%)")
    print(f"  Route restored          : {restored_n}/{total}")

    return results

if __name__ == '__main__':
    test_cases = [
        {'event_id': 1, 'zone': 'zone_A',
         'route': 'Lobby → Ruang Seminar', 'has_alternative': True},
        {'event_id': 2, 'zone': 'zone_B',
         'route': 'Lobby → Lab Komputer',  'has_alternative': True},
        {'event_id': 3, 'zone': 'zone_C',
         'route': 'Lobby → Ruang Dosen',   'has_alternative': True},
        # tambah sampai 10 event
    ]
    run_rerouting_test(test_cases)