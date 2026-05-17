"""
main.py - WiFi-Sniffer-AI Orchestrator
Complete lightweight wireless intelligence platform
"""
import sys
import time
import os
import signal
from datetime import datetime

from capture_core import LightweightCapture
from feature_engineer import FeatureEngineer
from ai_model import LightweightDeviceClassifier
from report_generator import ReportGenerator

class WiFiSnifferAI:
    """Main orchestrator - ties capture, AI, and reporting together"""
    
    def _init_(self, interface="wlan1mon"):
        self.interface = interface
        self.running = False
        
        # Init all modules
        self.capture = LightweightCapture(interface=interface)
        self.feature_engineer = FeatureEngineer(db_path="data/captured_devices.json")
        self.classifier = LightweightDeviceClassifier()
        self.reporter = ReportGenerator("reports")
        
        print(r"""
  _      _.____. _       _       ___       _      
 /  \    /  |           ||  |     /   \     |       \     /   \     
|   \  /   |  ---  |  | |    /  ^  \    |  .--.  |   /  ^  \    
|    \/    |      /  /  | |   /  /\  \   |  |  |  |  /  /\  \   
|  .  |    |     /  /   | |  /  __  \  |  '--'  | /  __  \  
|_|\|    |    /_/    || /_/     \\ |__/ /_/     \_\ 
        """)
        print("  Lightweight WiFi Intelligence Platform v1.0")
        print("=" * 55)
    
    def run(self, duration_seconds=None, report_interval=30):
        """Run the full pipeline"""
        self.running = True
        
        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start packet capture
        print(f"[+] Starting capture on {self.interface}")
        self.capture.start()
        
        start_time = time.time()
        last_report_time = start_time
        
        print("[+] AI analysis engine ready")
        print(f"[+] Auto-reporting every {report_interval}s")
        print(f"[+] Press Ctrl+C for final report\n")
        
        try:
            while self.running:
                time.sleep(5)
                
                # Show live stats
                dev_count = len(self.capture.devices)
                pkt_count = self.capture.packet_count
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] "
                      f"Devices: {dev_count} | Packets: {pkt_count}", end='')
                
                # Periodically run AI analysis and generate report
                elapsed = time.time() - start_time
                if (time.time() - last_report_time) >= report_interval:
                    print(" [Analyzing...]")
                    self._run_analysis()
                    last_report_time = time.time()
                else:
                    print()
                
                # Check if duration limit reached
                if duration_seconds and elapsed >= duration_seconds:
                    print(f"\n[+] Duration limit reached ({duration_seconds}s)")
                    break
                    
        except KeyboardInterrupt:
            print("\n[!] Interrupted by user")
        finally:
            self.shutdown()
    
    def _run_analysis(self):
        """Run AI analysis on all captured devices"""
        # Extract features from all devices
        feature_vectors, macs = self.feature_engineer.batch_extract()
        
        if len(macs) == 0:
            print("  No devices to analyze")
            return
        
        # Run AI classification on each device
        analyses = {}
        for i, mac in enumerate(macs):
            vector = feature_vectors[i]
            dev_data = self.capture.devices.get(mac, {})
            
            # Get AI analysis
            analysis = self.classifier.analyze_device(vector, dev_data)
            
            # Add vendor info
            analysis['vendor'] = dev_data.get('oui_vendor', 'Unknown')
            
            # Add feature summary for context
            summary = self.feature_engineer.get_feature_summary(dev_data)
            analysis.update(summary)
            
            analyses[mac] = analysis
        
        # Print top results
        self._print_results(analyses)
        
        # Save reports
        self.reporter.generate_json_report(analyses)
        self.reporter.generate_csv_report(analyses)
    
    def _print_results(self, analyses):
        """Print formatted analysis to console"""
        # Sort by anomaly score (most interesting first)
        sorted_devices = sorted(
            analyses.items(),
            key=lambda x: x[1].get('anomaly_score', 0),
            reverse=True
        )[:15]  # Top 15
        
        print(f"\n{'='*60}")
        print(f"  AI INTELLIGENCE REPORT - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        print(f"{'MAC':<18} {'Type':<14} {'Conf':<6} {'Anomaly':<8} {'Vendor':<15}")
        print(f"{'-'*60}")
        
        for mac, analysis in sorted_devices:
            print(f"{mac:<18} "
                  f"{analysis.get('classification', 'Unknown'):<14} "
                  f"{analysis.get('confidence', 0):.2f}{'':<4} "
                  f"{analysis.get('anomaly_score', 0):.3f}{'':<3} "
                  f"{analysis.get('vendor', '')[:14]:<15}")
        
        # Show suspicious devices
        suspicious = [(m, a) for m, a in analyses.items() 
                     if a.get('anomaly_score', 0) > 0.5]
        if suspicious:
            print(f"\n[!] Suspicious devices ({len(suspicious)} detected):")
            for mac, analysis in suspicious[:5]:
                print(f"  {mac} - Score: {analysis['anomaly_score']:.2f} "
                      f"({analysis.get('behavioral_profile', '')}")
        print(f"{'='*60}\n")
    
    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
    
    def shutdown(self):
        """Clean shutdown"""
        print("\n[+] Shutting down...")
        if hasattr(self, 'capture'):
            self.capture.stop()
        
        # Final analysis
        self._run_analysis()
        
        print("[+] Done. Reports saved to ./reports/")
        print("[+] Device database saved to ./data/captured_devices.json")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="WiFi-Sniffer-AI - Lightweight Wireless Intelligence Platform")
    parser.add_argument("-i", "--interface", default="wlan1mon",
                       help="Monitor mode interface (default: wlan1mon)")
    parser.add_argument("-t", "--time", type=int, default=None,
                       help="Capture duration in seconds (default: run until Ctrl+C)")
    parser.add_argument("-r", "--report-interval", type=int, default=30,
                       help="Report generation interval in seconds (default: 30)")
    parser.add_argument("--setup", action="store_true",
                       help="Run initial setup (enable monitor mode)")
    
    args = parser.parse_args()
    
    if args.setup:
        print("[+] Setting up monitor mode...")
        os.system(f"sudo airmon-ng check kill")
        os.system(f"sudo airmon-ng start wlan1")
        print("[+] Setup complete. Interface ready: wlan1mon")
        return
    
    # Check root
    if os.geteuid() != 0:
        print("[!] Must run as root. Use: sudo python3 main.py")
        sys.exit(1)
    
    app = WiFiSnifferAI(interface=args.interface)
    app.run(duration_seconds=args.time, report_interval=args.report_interval)

if _name_ == "_main_":
    main()
