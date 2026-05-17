#!/usr/bin/env python3
"""
feature_engineer.py - Extract ML-ready features from raw captured data
Produces numerical feature vectors for classification
"""
import numpy as np
import json
import os
from datetime import datetime

class FeatureEngineer:
    """Convert raw device data to numerical feature vectors"""
    
    def __init__(self, db_path="data/captured_devices.json"):
        self.db_path = db_path
        self.feature_names = [
            'num_probe_ssids',           # How many networks they're looking for
            'probe_diversity_score',      # Ratio of unique probes to total probes
            'avg_rssi',                   # Average signal strength
            'rssi_std',                   # Signal strength variance
            'packet_rate',                # Packets per second during active window
            'active_window_seconds',      # How long we've tracked this device
            'transmission_regularity',    # How regular the transmissions are (entropy-based)
            'oui_fingerprint_encoded',    # Encoded OUI vendor category
            'is_mobile_like',             # Feature: RSSI variation indicates movement
            'hour_of_day_seen'            # When was device most active
        ]
    
    def extract_features(self, device_data):
        """Extract numerical feature vector from a single device record"""
        features = {}
        
        # 1. Probe SSID count
        probe_ssids = device_data.get('probe_ssids', [])
        features['num_probe_ssids'] = min(len(probe_ssids), 20) / 20.0
        
        # 2. Probe diversity (unique / total - higher = broadcasting to many)
        total_probes = device_data.get('packet_count', 1)
        unique_count = len(probe_ssids)
        features['probe_diversity_score'] = min(unique_count / max(total_probes, 1) * 10, 1.0)
        
        # 3. RSSI stats
        rssi_values = device_data.get('rssi_values', [])
        if rssi_values:
            features['avg_rssi'] = (np.mean(rssi_values) + 100) / 100.0  # Normalize -100 to 0 -> 0 to 1
            features['rssi_std'] = min(np.std(rssi_values) / 30.0, 1.0)  # Normalize std
        else:
            features['avg_rssi'] = 0.5
            features['rssi_std'] = 0.0
        
        # 4. Packet rate (packets per second during active period)
        last_seen = datetime.fromisoformat(device_data.get('last_seen', datetime.now().isoformat()))
        first_seen = datetime.fromisoformat(device_data.get('first_seen', datetime.now().isoformat()))
        window = max((last_seen - first_seen).total_seconds(), 1)
        features['active_window_seconds'] = min(window / 300.0, 1.0)
        features['packet_rate'] = min(device_data.get('packet_count', 1) / window, 1.0)
        
        # 5. Transmission regularity (low value = bursty, high = consistent)
        # Using packet count variance as proxy
        features['transmission_regularity'] = 1.0 - abs(0.5 - (device_data.get('packet_count', 1) % 10) / 10.0)
        
        # 6. OUI vendor encoding
        vendor = device_data.get('oui_vendor', 'Unknown')
        features['oui_fingerprint_encoded'] = self._encode_vendor(vendor)
        
        # 7. Mobility indicator (RSSI variance suggests movement)
        features['is_mobile_like'] = min(features['rssi_std'] * 2, 1.0)
        
        # 8. Time-based feature
        try:
            hour = datetime.fromisoformat(device_data['last_seen']).hour
        except:
            hour = 12
        features['hour_of_day_seen'] = hour / 24.0
        
        return features
    
    def _encode_vendor(self, vendor):
        """Encode vendor into categorical numerical value"""
        common_vendors = {
            'Apple': 0.8, 'Samsung': 0.7, 'Intel': 0.6, 'Qualcomm': 0.65,
            'Broadcom': 0.55, 'Realtek': 0.5, 'MediaTek': 0.45,
            'TP-Link': 0.4, 'Cisco': 0.35, 'Huawei': 0.3, 'Xiaomi': 0.25,
            'Unknown': 0.1
        }
        for key, val in common_vendors.items():
            if key.lower() in vendor.lower():
                return val
        return 0.2  # Other known vendors
    
    def batch_extract(self):
        """Extract features from all devices in database"""
        if not os.path.exists(self.db_path):
            return np.array([]), []
        
        try:
            with open(self.db_path, 'r') as f:
                devices = json.load(f)
        except (json.JSONDecodeError, IOError):
            return np.array([]), []
        
        if not devices:
            return np.array([]), []
        
        feature_vectors = []
        mac_addresses = []
        
        for mac, data in devices.items():
            try:
                feats = self.extract_features(data)
                vector = [feats[name] for name in self.feature_names]
                feature_vectors.append(vector)
                mac_addresses.append(mac)
            except Exception as e:
                print(f"[!] Error extracting features for {mac}: {e}")
                continue
        
        if not feature_vectors:
            return np.array([]), []
        
        return np.array(feature_vectors), mac_addresses
    
    def get_feature_summary(self, device_data):
        """Human-readable feature summary for a device"""
        feats = self.extract_features(device_data)
        summary = {
            "known_networks": device_data.get('probe_ssids', []),
            "signal_avg_dbm": round(np.mean(device_data.get('rssi_values', [-70])), 1),
            "vendor": device_data.get('oui_vendor', 'Unknown'),
            "tracked_seconds": round(feats['active_window_seconds'] * 300),
            "packet_count": device_data.get('packet_count', 0),
            "probe_diversity": round(feats['probe_diversity_score'], 3),
            "mobility_score": round(feats['is_mobile_like'], 3)
        }
        return summary

if __name__ == "__main__":
    import sys
    fe = FeatureEngineer()
    vectors, macs = fe.batch_extract()
    print(f"Extracted features for {len(macs)} devices")
    if vectors.any():
        print(f"Feature vector shape: {vectors.shape}")
