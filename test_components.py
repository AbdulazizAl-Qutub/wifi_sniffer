#!/usr/bin/env python3
"""
Test script to validate all components work correctly
"""
import sys
import os

def test_imports():
    """Test all imports work"""
    print("[*] Testing imports...")
    try:
        from capture_core import LightweightCapture
        from feature_engineer import FeatureEngineer
        from ai_model import LightweightDeviceClassifier
        from report_generator import ReportGenerator
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_feature_engineer():
    """Test feature extraction"""
    print("\n[*] Testing FeatureEngineer...")
    try:
        from feature_engineer import FeatureEngineer
        import numpy as np
        
        fe = FeatureEngineer()
        
        # Test with sample device data
        sample_device = {
            'mac': '00:11:22:33:44:55',
            'probe_ssids': ['Network1', 'Network2'],
            'rssi_values': [-50, -55, -52],
            'packet_count': 10,
            'first_seen': '2026-05-18T00:00:00',
            'last_seen': '2026-05-18T00:05:00',
            'oui_vendor': 'Apple'
        }
        
        features = fe.extract_features(sample_device)
        assert len(features) == 10, "Should have 10 features"
        print(f"✓ Feature extraction works (10 features extracted)")
        
        # Test batch extract with empty database
        vectors, macs = fe.batch_extract()
        assert isinstance(vectors, np.ndarray), "Should return numpy array"
        print(f"✓ Batch extraction works (empty database handled)")
        
        return True
    except Exception as e:
        print(f"✗ FeatureEngineer test failed: {e}")
        return False

def test_ai_model():
    """Test AI classifier"""
    print("\n[*] Testing AI Model...")
    try:
        from ai_model import LightweightDeviceClassifier
        import numpy as np
        
        classifier = LightweightDeviceClassifier()
        
        # Test with sample feature vector
        sample_features = np.array([0.3, 0.4, 0.5, 0.3, 0.2, 0.4, 0.6, 0.7, 0.5, 0.3])
        
        class_id, class_name, confidence = classifier.predict(sample_features)
        assert class_name in classifier.class_labels, "Should return valid class"
        assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
        print(f"✓ Classification works: {class_name} (confidence: {confidence:.2f})")
        
        # Test with invalid feature vector
        invalid_features = np.array([0.1, 0.2])
        probs = classifier.predict_proba(invalid_features)
        assert probs[-1] == 1.0, "Should return Unknown for invalid input"
        print(f"✓ Invalid input handling works")
        
        return True
    except Exception as e:
        print(f"✗ AI Model test failed: {e}")
        return False

def test_report_generator():
    """Test report generation"""
    print("\n[*] Testing ReportGenerator...")
    try:
        from report_generator import ReportGenerator
        import os
        import shutil
        
        # Create temp directory
        test_dir = "test_reports"
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        
        reporter = ReportGenerator(test_dir)
        
        # Test with sample analyses
        sample_analyses = {
            '00:11:22:33:44:55': {
                'classification': 'Smartphone',
                'confidence': 0.85,
                'vendor': 'Apple',
                'anomaly_score': 0.2,
                'behavioral_profile': 'Mobile device',
                'probed_networks': ['Network1'],
                'tracking_duration_sec': 300,
                'avg_signal_dbm': -50
            }
        }
        
        json_path = reporter.generate_json_report(sample_analyses, timestamp="test")
        assert json_path is not None, "Should generate JSON report"
        assert os.path.exists(json_path), "JSON report file should exist"
        print(f"✓ JSON report generation works")
        
        csv_path = reporter.generate_csv_report(sample_analyses, timestamp="test")
        assert csv_path is not None, "Should generate CSV report"
        assert os.path.exists(csv_path), "CSV report file should exist"
        print(f"✓ CSV report generation works")
        
        # Test with empty analyses
        result = reporter.generate_json_report({})
        assert result is None, "Should handle empty analyses"
        print(f"✓ Empty data handling works")
        
        # Cleanup
        shutil.rmtree(test_dir)
        
        return True
    except Exception as e:
        print(f"✗ ReportGenerator test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("WiFi-Sniffer-AI Component Test Suite")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("FeatureEngineer", test_feature_engineer()))
    results.append(("AI Model", test_ai_model()))
    results.append(("ReportGenerator", test_report_generator()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:<20} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
