#!/bin/bash
# Quick Start Guide for WiFi-Sniffer-AI

echo "=========================================="
echo "WiFi-Sniffer-AI - Quick Start Guide"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "✓ Running as root"
echo ""

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Install with:"
    echo "   sudo apt install python3"
    exit 1
fi
echo "✓ Python3 found"

# Check NumPy
if ! python3 -c "import numpy" 2>/dev/null; then
    echo "⚠ NumPy not found. Installing..."
    apt install -y python3-numpy
fi
echo "✓ NumPy available"

# Check airmon-ng
if ! command -v airmon-ng &> /dev/null; then
    echo "❌ airmon-ng not found. Install with:"
    echo "   sudo apt install aircrack-ng"
    exit 1
fi
echo "✓ airmon-ng found"

echo ""
echo "=========================================="
echo "Available WiFi Interfaces:"
echo "=========================================="
ip link show | grep -E '^[0-9]+:' | awk '{print $2}' | sed 's/:$//' | grep -E '^wl'

echo ""
echo "=========================================="
echo "Setup Steps:"
echo "=========================================="
echo ""
echo "1. Enable monitor mode:"
echo "   sudo airmon-ng check kill"
echo "   sudo airmon-ng start wlan0"
echo ""
echo "2. Run the sniffer:"
echo "   sudo python3 main.py"
echo ""
echo "3. Or use the setup command:"
echo "   sudo python3 main.py --setup"
echo "   sudo python3 main.py"
echo ""
echo "=========================================="
echo "Options:"
echo "=========================================="
echo "  -i INTERFACE    Specify interface (default: wlan0mon)"
echo "  -t SECONDS      Run for specific duration"
echo "  -r SECONDS      Report interval (default: 30)"
echo "  --setup         Enable monitor mode"
echo ""
echo "Examples:"
echo "  sudo python3 main.py -i wlan0mon"
echo "  sudo python3 main.py -t 300 -r 60"
echo ""
echo "=========================================="
echo "Output:"
echo "=========================================="
echo "  Reports:  ./reports/"
echo "  Database: ./data/captured_devices.json"
echo ""
echo "Press Ctrl+C to stop and generate final report"
echo ""
