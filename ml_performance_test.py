import joblib
import pandas as pd
import numpy as np
import os

def run_red_team_test():
    # 1. Load Artifacts
    base_path = os.path.abspath(os.path.join(os.getcwd()))
    try:
        model = joblib.load(os.path.join(base_path, "behavior_anomaly_model.pkl"))
        feature_cols = joblib.load(os.path.join(base_path, "feature_cols.pkl"))
        print("--- ThreatSense Red Team Testing Tool ---")
        print("Successfully loaded ML engine.\n")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # 2. Create Synthetic "Red Team" Actions (Known Ground Truth)
    # We create 50 normal actions and 50 hacker actions
    data = []
    labels = [] # 0 = Normal, 1 = Hacker

    # Generate 50 Normal Actions (Middle of day, low volume, common files)
    for _ in range(50):
        data.append({
            'hour': 14, 'day_of_week': 1, 'is_weekend': 0, 
            'temporal_zscore': 0.1, 'temporal_anomaly': 0, 
            'volume_zscore': 0.1, 'volume_anomaly': 0, 
            'files_per_hour': 2, 'transition_prob': 0.5, 
            'sequential_anomaly': 0, 'anomaly_score': 1.0,
            'user_encoded': 1, 'log_type_encoded': 1, 'department_encoded': 1, 
            'file_accessed_encoded': 1, 'location_encoded': 1, 'device_type_encoded': 1
        })
        labels.append(0)

    # Generate 50 Hacker Actions (3 AM, extreme volume, suspicious transitions)
    for _ in range(50):
        data.append({
            'hour': 3, 'day_of_week': 6, 'is_weekend': 1, 
            'temporal_zscore': 5.0, 'temporal_anomaly': 1, 
            'volume_zscore': 6.0, 'volume_anomaly': 1, 
            'files_per_hour': 100, 'transition_prob': 0.01, 
            'sequential_anomaly': 1, 'anomaly_score': 90.0,
            'user_encoded': 5, 'log_type_encoded': 2, 'department_encoded': 3, 
            'file_accessed_encoded': 90, 'location_encoded': 4, 'device_type_encoded': 2
        })
        labels.append(1)

    # 3. Process data
    test_df = pd.DataFrame(data)
    
    # Ensure any missing columns from feature_cols are present (set to 0)
    for col in feature_cols:
        if col not in test_df.columns:
            test_df[col] = 0
            
    test_df = test_df[feature_cols]

    # 4. Run Predictions
    predictions = model.predict(test_df)

    # 5. Calculate Metrics
    correct_normal = sum((predictions[:50] == 0))
    correct_attacks = sum((predictions[50:] == 1))

    total_accuracy = (correct_normal + correct_attacks) / 100
    detection_rate = (correct_attacks / 50) * 100
    false_alarm_rate = ((50 - correct_normal) / 50) * 100

    print(f"RESULT: Security Detection Rate: {detection_rate}%")
    print(f"RESULT: False Alarm Rate: {false_alarm_rate}%")
    print(f"RESULT: Overall Model Reliability: {total_accuracy * 100}%\n")
    
    if detection_rate > 90:
        print("STATUS: PASSED - This model is ready for Proactive Attack Detection.")
    else:
        print("STATUS: NEEDS TUNING - The model is missing too many attacks.")

if __name__ == "__main__":
    run_red_team_test()
