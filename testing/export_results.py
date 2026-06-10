import pandas as pd
import glob
import os

def export_all_results():
    os.makedirs('logs', exist_ok=True)
    excel_path = 'logs/ALL_RESULTS.xlsx'

    try:
        writer = pd.ExcelWriter(excel_path, engine='openpyxl')
    except ModuleNotFoundError:
        print("Error: 'pandas' or 'openpyxl' is not installed. Please install them using:\n"
              "pip install pandas openpyxl")
        return

    # TABLE II
    try:
        df2 = pd.read_csv('logs/table2_yolo_accuracy.csv')
        df2.to_excel(writer, sheet_name='TABLE_II_YOLO', index=False)
    except FileNotFoundError:
        print("Warning: logs/table2_yolo_accuracy.csv not found. Skipping Table II sheet.")

    # TABLE III
    try:
        df3 = pd.read_csv('logs/table3_classification.csv')
        df3.to_excel(writer, sheet_name='TABLE_III_Classification', index=False)
    except FileNotFoundError:
        print("Warning: logs/table3_classification.csv not found. Skipping Table III sheet.")

    # TABLE IV
    try:
        df4 = pd.read_csv('logs/table4_rerouting.csv')
        df4.to_excel(writer, sheet_name='TABLE_IV_Rerouting', index=False)
    except FileNotFoundError:
        print("Warning: logs/table4_rerouting.csv not found. Skipping Table IV sheet.")

    # TABLE V — gabung server + unity log
    try:
        df5s = pd.read_csv('logs/table5_latency.csv')
        unity_logs = glob.glob('logs/latency_unity*.csv')
        if unity_logs:
            df5u = pd.read_csv(unity_logs[-1])
            df5  = pd.concat([df5s, df5u], axis=1)
        else:
            df5 = df5s
        df5.to_excel(writer, sheet_name='TABLE_V_Latency', index=False)
    except FileNotFoundError:
        print("Warning: logs/table5_latency.csv not found. Skipping Table V sheet.")

    try:
        writer.close()
        print(f"✅ Semua hasil tersimpan di {excel_path}")
    except Exception as e:
        print(f"Error saving Excel file: {e}")

if __name__ == '__main__':
    export_all_results()
