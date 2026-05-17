"""
report_generator.py - Output structured intelligence reports
"""
import json
import csv
import os
from datetime import datetime

class ReportGenerator:
    def _init_(self, output_dir="reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_json_report(self, analyses, timestamp=None):
        """Generate full JSON intelligence report"""
        timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Organize by threat level
        report = {
            "report_time": datetime.now().isoformat(),
            "total_devices_detected": len(analyses),
            "summary": {
                "smartphones": sum(1 for a in analyses.values() if a['classification'] == 'Smartphone'),
                "laptops": sum(1 for a in analyses.values() if a['classification'] == 'Laptop'),
                "iot_devices": sum(1 for a in analyses.values() if a['classification'] == 'IoT Device'),
                "beacons": sum(1 for a in analyses.values() if a['classification'] == 'Beacon/Tracker'),
                "unknown": sum(1 for a in analyses.values() if a['classification'] == 'Unknown'),
                "suspicious_devices": sum(1 for a in analyses.values() if a.get('anomaly_score', 0) > 0.5)
            },
            "devices": []
        }
        
        for mac, analysis in sorted(analyses.items()):
            device_entry = {"mac": mac, **analysis}
            report["devices"].append(device_entry)
        
        path = f"{self.output_dir}/intel_report_{timestamp}.json"
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"[+] Report saved: {path}")
        return path
    
    def generate_csv_report(self, analyses, timestamp=None):
        """Generate CSV for spreadsheet/external tool import"""
        timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"{self.output_dir}/intel_report_{timestamp}.csv"
        
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "MAC", "Classification", "Confidence", "Vendor", 
                "Anomaly Score", "Behavioral Profile", "Signal (dBm)",
                "Networks Probed", "Tracking Duration (s)"
            ])
            
            for mac, analysis in sorted(analyses.items()):
                writer.writerow([
                    mac,
                    analysis.get('classification', 'Unknown'),
                    analysis.get('confidence', 0),
                    analysis.get('vendor', 'Unknown'),
                    analysis.get('anomaly_score', 0),
                    analysis.get('behavioral_profile', ''),
                    analysis.get('avg_signal_dbm', ''),
                    ', '.join(analysis.get('probed_networks', [])[:5]),
                    analysis.get('tracking_duration_sec', 0)
                ])
        
        print(f"[+] CSV report saved: {path}")
        return path
