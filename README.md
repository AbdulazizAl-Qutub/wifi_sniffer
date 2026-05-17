# WiFi-Sniffer-AI

Lightweight WiFi Intelligence Platform - Passive wireless device monitoring and AI-powered classification.

## Features

✓ **Passive Monitoring** - Captures WiFi probe requests without active scanning  
✓ **AI Classification** - Identifies device types (Smartphone, Laptop, IoT, Beacon, AP)  
✓ **Anomaly Detection** - Detects suspicious scanning tools and unusual patterns  
✓ **Vendor Identification** - OUI database lookup for manufacturer info  
✓ **Behavioral Profiling** - Tracks mobility, network probing, signal characteristics  
✓ **Intelligence Reports** - JSON and CSV output for analysis  
✓ **Lightweight** - ~200KB RAM usage, pure NumPy implementation  

## Requirements

- Linux system (tested on Ubuntu/Debian/Kali)
- Python 3.7+
- External WiFi adapter with monitor mode support
- Root privileges

### Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-numpy aircrack-ng wireless-tools
```

## Installation

### Quick Install

```bash
chmod +x install.sh
./install.sh
```

### Manual Setup

1. **Enable monitor mode:**
```bash
sudo airmon-ng check kill
sudo airmon-ng start wlan0
```

2. **Create directories:**
```bash
mkdir -p data models reports
```

3. **Download OUI database (optional):**
```bash
wget -O data/oui.txt.gz https://linuxnet.ca/ieee/oui.txt.gz
gunzip data/oui.txt.gz
```

## Usage

### Basic Usage

```bash
sudo python3 main.py
```

### Advanced Options

```bash
# Specify interface
sudo python3 main.py -i wlan0mon

# Run for specific duration (seconds)
sudo python3 main.py -t 300

# Change report interval (default: 30s)
sudo python3 main.py -r 60

# Setup monitor mode
sudo python3 main.py --setup
```

### Full Example

```bash
# Enable monitor mode
sudo python3 main.py --setup

# Start capture with 60-second reports
sudo python3 main.py -r 60

# Press Ctrl+C to stop and generate final report
```

## Output

### Console Output

Real-time display showing:
- Device count and packet statistics
- Top devices sorted by anomaly score
- Device classification and confidence
- Suspicious device alerts

### Reports

**JSON Report** (`reports/intel_report_TIMESTAMP.json`):
- Complete device analysis
- Summary statistics
- Behavioral profiles
- Anomaly scores

**CSV Report** (`reports/intel_report_TIMESTAMP.csv`):
- Spreadsheet-compatible format
- Easy import to Excel/LibreOffice
- Quick filtering and sorting

**Device Database** (`data/captured_devices.json`):
- Persistent device tracking
- Historical probe data
- Signal strength history

## Architecture

```
main.py                 - Orchestrator and CLI interface
├── capture_core.py     - Raw packet capture (AF_PACKET sockets)
├── feature_engineer.py - Feature extraction (10 numerical features)
├── ai_model.py         - Device classification (rule-based + statistical)
└── report_generator.py - Intelligence report generation
```

## Device Classification

The AI model classifies devices into 6 categories:

1. **Smartphone** - Android/iOS devices with high mobility
2. **Laptop** - Windows/macOS/Linux with moderate mobility
3. **IoT Device** - Smart home devices, stationary
4. **Beacon/Tracker** - BLE beacons, tracking devices
5. **AP/Extender** - Access points, WiFi extenders
6. **Unknown** - Unclassified or low-confidence devices

### Classification Features

- Number of probed SSIDs
- Probe diversity score
- Average RSSI and variance
- Packet rate and regularity
- Transmission patterns
- OUI vendor fingerprint
- Mobility indicators
- Time-of-day patterns

## Anomaly Detection

Detects suspicious behavior:
- **Scanning tools** - High probe diversity + low regularity
- **Deauth devices** - Extremely regular + no probes
- **MAC spoofing** - Unusual vendor/behavior combinations
- **Rogue devices** - Anomaly score > 0.5

## Troubleshooting

### Interface not found
```bash
# List available interfaces
ip link show

# Enable monitor mode on correct interface
sudo airmon-ng start wlan0
```

### Permission denied
```bash
# Must run as root
sudo python3 main.py
```

### No packets captured
```bash
# Check monitor mode is enabled
iwconfig

# Should show "Mode:Monitor"
# If not, run:
sudo airmon-ng start wlan0
```

### NumPy not found
```bash
pip3 install numpy
# or
sudo apt install python3-numpy
```

## Testing

Run the component test suite:

```bash
python3 test_components.py
```

This validates:
- All imports work correctly
- Feature extraction functions
- AI classification accuracy
- Report generation

## Security & Ethics

⚠️ **Important Notes:**

- This tool is for **authorized security testing only**
- Passive monitoring only - no active attacks
- Respect privacy laws in your jurisdiction
- Do not use on networks without permission
- Educational and research purposes

## Performance

- **RAM Usage**: ~200KB during inference
- **CPU Usage**: Minimal (single-threaded capture)
- **Storage**: ~1KB per device in database
- **Packet Rate**: Handles 1000+ packets/sec

## Limitations

- Only captures probe requests (not all WiFi traffic)
- Requires external WiFi adapter with monitor mode
- Classification accuracy depends on captured data
- OUI database may be outdated (update periodically)

## Contributing

Contributions welcome! Areas for improvement:

- Additional device classification categories
- Machine learning model training
- Web-based dashboard
- Real-time alerting system
- Integration with SIEM tools

## License

This project is for educational and research purposes.

## Credits

Developed for wireless security research and network analysis.

## Changelog

### v1.1 (2026-05-18)
- Fixed Python syntax errors (__init__, __name__)
- Added comprehensive error handling
- Improved empty data handling
- Added interface validation
- Enhanced report generation with error checks
- Added component test suite
- Changed default interface to wlan0
- Added detailed documentation

### v1.0 (Initial Release)
- Basic packet capture
- AI device classification
- Report generation
- OUI vendor lookup
