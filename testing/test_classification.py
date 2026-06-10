import requests, csv, time
from datetime import datetime

FLASK_URL  = 'http://localhost:5000'
ZONE_ID    = 'zone_A'
OUTPUT_CSV = 'logs/table3_classification.csv'

def run_classification_test(scenarios):
    """
    scenarios = list of dict:
    [
      {'people_count': 3,  'ground_truth': 'Low'},
      {'people_count': 8,  'ground_truth': 'Medium'},
      {'people_count': 15, 'ground_truth': 'High'},
      ...
    ]
    """
    results = []

    for i, s in enumerate(scenarios):
        print(f"\nSkenario {i+1}: {s['people_count']} orang "
              f"(GT: {s['ground_truth']})")
        input("Atur jumlah orang di zona, tekan Enter jika siap...")

        # Ambil klasifikasi dari sistem
        time.sleep(2)  # tunggu sistem mendeteksi
        resp  = requests.get(f'{FLASK_URL}/density/{ZONE_ID}')
        data  = resp.json()
        pred  = data.get('level', 'Unknown')

        results.append({
            'scenario':     i + 1,
            'people_count': s['people_count'],
            'ground_truth': s['ground_truth'],
            'prediction':   pred,
            'correct':      pred == s['ground_truth'],
            'timestamp':    datetime.now().isoformat()
        })
        print(f"  Prediksi: {pred} → {'✅' if pred == s['ground_truth'] else '❌'}")

    # Hitung confusion matrix
    labels   = ['Low', 'Medium', 'High']
    matrix   = {gt: {pr: 0 for pr in labels} for gt in labels}
    correct  = 0

    for r in results:
        matrix[r['ground_truth']][r['prediction']] += 1
        if r['correct']:
            correct += 1

    accuracy = correct / len(results) * 100

    # Simpan ke CSV
    with open(OUTPUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)

    print("\n=== TABLE III: CONFUSION MATRIX ===")
    print(f"{'':12}", end='')
    for p in labels:
        print(f"{p:10}", end='')
    print()
    for gt in labels:
        print(f"{gt:12}", end='')
        for pr in labels:
            print(f"{matrix[gt][pr]:<10}", end='')
        print()
    print(f"\nOverall Accuracy: {accuracy:.2f}%")

    return matrix, accuracy

if __name__ == '__main__':
    # Definisikan 30 skenario: 10 Low, 10 Medium, 10 High
    scenarios = (
        [{'people_count': i, 'ground_truth': 'Low'}
         for i in [0,1,2,3,4,1,2,3,4,5]] +
        [{'people_count': i, 'ground_truth': 'Medium'}
         for i in [6,7,8,9,10,6,7,8,9,10]] +
        [{'people_count': i, 'ground_truth': 'High'}
         for i in [11,13,15,17,20,12,14,16,18,21]]
    )
    run_classification_test(scenarios)