import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import os

class AnomalyDetector:
    def __init__(self):
        # Paths to artifacts (one level up from /backend/ml/)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        
        self.model = joblib.load(os.path.join(base_path, "behavior_anomaly_model.pkl"))
        self.encoders = joblib.load(os.path.join(base_path, "encoders.pkl"))
        self.feature_cols = joblib.load(os.path.join(base_path, "feature_cols.pkl"))
        self.user_hour_stats = joblib.load(os.path.join(base_path, "user_hour_stats.pkl"))
        self.user_volume_stats = joblib.load(os.path.join(base_path, "user_volume_stats.pkl"))
        
        print("Anomaly Detector initialized with all artifacts.")

    def predict(self, log_entry, user_history):
        """
        log_entry: dict containing current action (user, log_type, department, file_accessed, etc.)
        user_history: list of recent actions for this user (from Redis)
        """
        # 1. Basic Time Features
        try:
            dt = datetime.fromisoformat(log_entry['timestamp'])
        except (ValueError, TypeError, KeyError):
            dt = datetime.utcnow()
        hour = dt.hour
        day_of_week = dt.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # 2. Temporal Analysis
        stats = self.user_hour_stats[self.user_hour_stats['user'] == log_entry['user']]
        if not stats.empty:
            mean = stats.iloc[0]['hour_mean']
            std = stats.iloc[0]['hour_std']
        else:
            mean, std = 12, 4 # Fallback
            
        temporal_zscore = np.abs((hour - mean) / std)
        temporal_anomaly = 1 if temporal_zscore > 2 else 0
        
        # 3. Volume Analysis (Recent frequency)
        # Assuming user_history contains actions from the last hour
        files_per_hour = len(user_history) + 1
        vol_stats = self.user_volume_stats[self.user_volume_stats['user'] == log_entry['user']]
        if not vol_stats.empty:
            v_mean = vol_stats.iloc[0]['volume_mean']
            v_std = vol_stats.iloc[0]['volume_std']
        else:
            v_mean, v_std = 5, 2 # Fallback
            
        volume_zscore = np.abs((files_per_hour - v_mean) / v_std)
        volume_anomaly = 1 if volume_zscore > 2 else 0
        
        # 4. Sequential Analysis (Transition Prob)
        # Using the last accessed file from history
        if user_history:
            prev_file = user_history[-1].get('file_accessed', 'none')
        else:
            prev_file = 'none'
            
        # Simplified transition prob for real-time (ideally would use a transition matrix)
        # For now, if it's the same file or a common switch, give high prob
        transition_prob = 0.5 if prev_file == log_entry['file_accessed'] else 0.05
        sequential_anomaly = 1 if transition_prob < 0.1 else 0
        
        # 5. Combined Anomaly Score (matches training logic)
        anomaly_score = (
            0.4 * temporal_zscore + 
            0.3 * volume_zscore + 
            0.3 * (1 - transition_prob) * 10
        )
        
        # 6. Encode Categorical
        features_dict = {
            'hour': hour,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'temporal_zscore': temporal_zscore,
            'temporal_anomaly': temporal_anomaly,
            'volume_zscore': volume_zscore,
            'volume_anomaly': volume_anomaly,
            'files_per_hour': files_per_hour,
            'transition_prob': transition_prob,
            'sequential_anomaly': sequential_anomaly,
            'anomaly_score': anomaly_score
        }
        
        # Add encoded categorical columns
        for col, encoder in self.encoders.items():
            val = log_entry.get(col, 'Unknown')
            # Handle unseen labels
            if val not in encoder.classes_:
                features_dict[col + '_encoded'] = 0 
            else:
                features_dict[col + '_encoded'] = encoder.transform([val])[0]
        
        # Create DataFrame for model input
        input_df = pd.DataFrame([features_dict])
        
        # Ensure column order matches training
        input_df = input_df[self.feature_cols]
        
        # Predict
        prediction = self.model.predict(input_df)[0]
        confidence = self.model.predict_proba(input_df)[0][1]
        
        return {
            "is_anomaly": bool(prediction),
            "confidence": float(confidence),
            "anomaly_score": float(anomaly_score),
            "details": {
                "temporal": "flagged" if temporal_anomaly else "normal",
                "volume": "flagged" if volume_anomaly else "normal",
                "sequential": "flagged" if sequential_anomaly else "normal"
            }
        }
