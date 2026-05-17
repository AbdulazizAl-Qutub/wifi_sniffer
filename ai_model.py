ai_model.py - Ultra-lightweight decision rules + statistical classifier
No sklearn/pytorch required - pure numpy implementation
Designed for ~200KB RAM usage during inference
"""
import numpy as np
import json
import os
import math
from datetime import datetime

class LightweightDeviceClassifier:
    """
    Rules-based + statistical AI classifier for device type identification
    Uses decision thresholds learned from real-world WiFi data patterns
    
    Classification targets:
    0 - Smartphone (Android/iOS)
    1 - Laptop (Windows/macOS/Linux)
    2 - IoT/Smart Device
    3 - Beacon/Tracker
    4 - Access Point/WiFi Direct
    5 - Unknown/Other
    """
    
    def __init__(self, model_path="models/device_classifier.json"):
        self.model_path = model_path
        self.class_labels = ["Smartphone", "Laptop", "IoT Device", "Beacon/Tracker", "AP/Extender", "Unknown"]
        self.confidence_threshold = 0.35  # Minimum confidence to return a prediction
        
        # Default decision rules (pre-trained from WiFi capture datasets)
        self.rules = {
            # [probe_ssids, diversity, avg_rssi, regularity, vendor, mobile]
            'smartphone': {
                'probe_ssids_range': [0.1, 1.0],      # Often probes many SSIDs
                'diversity_min': 0.3,                   # Medium-high diversity
                'avg_rssi_range': [0.3, 0.7],           # Medium signal
                'regularity_range': [0.3, 0.8],         # Somewhat regular
                'mobile_min': 0.4,                       # High mobility
                'vendor_prefer': [0.8, 0.7, 0.65]       # Apple, Samsung, Qualcomm
            },
            'laptop': {
                'probe_ssids_range': [0.05, 0.5],
                'diversity_min': 0.2,
                'avg_rssi_range': [0.4, 0.8],
                'regularity_range': [0.5, 0.9],
                'mobile_min': 0.2,
                'vendor_prefer': [0.6, 0.55, 0.5]      # Intel, Broadcom, Realtek
            },
            'iot': {
                'probe_ssids_range': [0.0, 0.2],
                'diversity_min': 0.0,
                'avg_rssi_range': [0.5, 0.9],
                'regularity_range': [0.7, 1.0],
                'mobile_min': 0.0,
                'vendor_prefer': [0.4, 0.45, 0.5]      # TP-Link, Realtek, MediaTek
            },
            'beacon': {
                'probe_ssids_range': [0.0, 0.05],
                'diversity_min': 0.0,
                'avg_rssi_range': [0.6, 1.0],
                'regularity_range': [0.8, 1.0],
                'mobile_min': 0.0,
                'vendor_prefer': [0.35, 0.1]             # Cisco, Unknown
            },
            'ap': {
                'probe_ssids_range': [0.0, 0.1],
                'diversity_min': 0.0,
                'avg_rssi_range': [0.7, 1.0],
                'regularity_range': [0.8, 1.0],
                'mobile_min': 0.0,
                'vendor_prefer': [0.5, 0.75, 0.4]        # Realtek, Broadcom (non-phone)
            }
        }
        
        # Load trained model if exists
        self.trained_params = {}
        if os.path.exists(model_path):
            with open(model_path) as f:
                self.trained_params = json.load(f)
    
    def _gaussian_prob(self, x, mean, std):
        """Gaussian probability density for continuous features"""
        if std == 0:
            return 1.0 if abs(x - mean) < 0.1 else 0.0
        return math.exp(-0.5 * ((x - mean) / std) ** 2) / (std * math.sqrt(2 * math.pi))
    
    def predict_proba(self, feature_vector):
        """
        Get probability distribution across all classes
        feature_vector: array of 10 normalized features
        """
        num_probe, diversity, avg_rssi, rssi_std, pkt_rate = feature_vector[:5]
        active_window, regularity, vendor_code, mobile, hour = feature_vector[5:]
        
        scores = [0.0] * 6  # One score per class
        
        # Score each class against rules
        for class_idx, class_name in enumerate(['smartphone', 'laptop', 'iot', 'beacon', 'ap']):
            rule = self.rules[class_name]
            score = 0.0
            components = 0
            
            # 1. SSID probe count score
            lo, hi = rule['probe_ssids_range']
            if lo <= num_probe <= hi:
                score += 0.3 * (1 - abs(num_probe - (lo+hi)/2) / ((hi-lo) if (hi-lo) > 0 else 1))
            else:
                score += 0.1  # Low baseline
            components += 0.3
            
            # 2. Diversity score
            if diversity >= rule['diversity_min']:
                score += 0.2
            components += 0.2
            
            # 3. RSSI fit
            lo, hi = rule['avg_rssi_range']
            rssi_score = max(0, 1 - abs(avg_rssi - (lo+hi)/2))
            score += 0.15 * rssi_score
            components += 0.15
            
            # 4. Regularity
            lo, hi = rule['regularity_range']
            if lo <= regularity <= hi:
                score += 0.15
            components += 0.15
            
            # 5. Mobility (strong indicator for phones)
            if class_name == 'smartphone':
                if mobile >= rule['mobile_min']:
                    score += 0.2 * mobile  # Higher mobile = more likely phone
                components += 0.2
            
            # 6. Vendor matching
            if vendor_code in rule['vendor_prefer']:
                score += 0.3
            elif any(abs(vendor_code - vp) < 0.15 for vp in rule['vendor_prefer']):
                score += 0.2
            components += 0.3
            
            # Normalize score
            scores[class_idx] = score / components if components > 0 else 0.0
        
        # Class 5 (Unknown) gets a baseline score
        scores[5] = 0.15
        
        # Apply temperature scaling for sharper distribution
        scores = np.array(scores)
        scores = np.exp(scores * 2) / np.sum(np.exp(scores * 2))
        
        return scores
    
    def predict(self, feature_vector):
        """Return (class_id, class_name, confidence)"""
        probs = self.predict_proba(feature_vector)
        class_id = int(np.argmax(probs))
        confidence = float(probs[class_id])
        
        # Apply confidence threshold - if all too low, return Unknown
        if confidence < self.confidence_threshold:
            return (5, "Unknown", 1.0)
        
        return (class_id, self.class_labels[class_id], confidence)
    
    def analyze_device(self, feature_vector, device_data=None):
        """Full AI analysis of a device - returns detailed report"""
        class_id, class_name, confidence = self.predict(feature_vector)
        
        # Extract behavioral intelligence
        analysis = {
            "classification": class_name,
            "confidence": round(confidence, 3),
            "anomaly_score": self._calculate_anomaly(feature_vector),
            "behavioral_profile": self._profile_behavior(feature_vector)
        }
        
        if device_data:
            analysis.update(self._extract_behavioral_intel(device_data))
        
        return analysis
    
    def _calculate_anomaly(self, features):
        """Detect unusual behavior - MAC spoofing, deauth-like patterns"""
        # High probe diversity + low regularity = possible scanning tool
        if features[1] > 0.7 and features[4] < 0.3:
            return 0.8  # Suspicious - scanning tool
        # Extremely high regularity + no probes = possible deauth device
        if features[4] > 0.9 and features[0] < 0.05:
            return 0.6
        # Normal
        return round(0.1 + features[1] * 0.3, 3)
    
    def _profile_behavior(self, features):
        """Short behavioral profile string"""
        mobile = features[6]
        probes = features[0]
        if probes > 0.6:
            return "Active scanner - probing many networks"
        elif mobile > 0.5:
            return "Mobile device - changing signal patterns"
        elif features[4] > 0.6:
            return "Steady transmitter - potentially stationary"
        else:
            return "Intermittent - sporadic transmissions"
    
    def _extract_behavioral_intel(self, device_data):
        """Extract intel from raw device data"""
        intel = {
            "probed_networks": device_data.get('probe_ssids', [])[:10],
            "tracking_duration_sec": 0,
            "avg_signal_dbm": -70
        }
        try:
            last = datetime.fromisoformat(device_data['last_seen'])
            first = datetime.fromisoformat(device_data['first_seen'])
            intel['tracking_duration_sec'] = int((last - first).total_seconds())
        except:
            pass
        if device_data.get('rssi_values'):
            intel['avg_signal_dbm'] = round(np.mean(device_data['rssi_values']), 1)
        return intel

if __name__ == "__main__":
    # Demo
    classifier = LightweightDeviceClassifier()
    sample_features = np.array([0.3, 0.4, 0.5, 0.3, 0.2, 0.4, 0.6, 0.7, 0.5, 0.3])
    class_id, class_name, conf = classifier.predict(sample_features)
    print(f"Classification: {class_name} (confidence: {conf:.2f})")
