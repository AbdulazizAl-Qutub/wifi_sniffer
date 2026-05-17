#!/bin/bash
# install.sh - One-command setup for WiFi-Sniffer-AI
set -e

echo "[*] WiFi-Sniffer-AI - Installation"
echo "================================"

# 1. Update system
echo "[*] Updating system packages..."
sudo apt update -qq
sudo apt upgrade -y -qq

# 2. Install base dependencies (minimal)
echo "[*] Installing base dependencies..."
sudo apt install -y -qq \
    python3 python3-pip python3-numpy \
    wireless-tools net-tools \
    aircrack-ng \
    git

# 3. Create project structure
echo "[*] Creating project structure..."
mkdir -p wifi-sniffer-ai/{data,models,reports}
cd wifi-sniffer-ai

# 4. Download OUI database (compressed ~300KB)
echo "[*] Downloading OUI vendor database..."
if [ ! -f "data/oui.txt" ]; then
    wget -q -O data/oui.txt.gz \
        https://linuxnet.ca/ieee/oui.txt.gz 2>/dev/null || \
    wget -q -O data/oui.txt.gz \
        http://standards-oui.ieee.org/oui/oui.txt.gz 2>/dev/null || \
    echo "[!] OUI download failed, will use built-in fallbacks"
    if [ -f "data/oui.txt.gz" ]; then
        gunzip -f data/oui.txt.gz 2>/dev/null
    fi
fi

# Create placeholder model config
cat > models/device_classifier.json << 'EOF'
{"version": 1, "type": "decision_rules", "trained": "2025-01-01"}
EOF

# 5. Create project files
echo "[*] Setting up project files..."
# Note: The python files should already be in this directory
# If not, they need to be copied/written here

# 6. Verify Python dependencies
echo "[*] Verifying Python dependencies..."
python3 -c "import numpy; print('[+] NumPy OK')" 2>/dev/null || \
    pip3 install numpy -q

# 7. Setup network interface helper
echo "[*] Creating interface setup helper..."
cat > setup_monitor.sh << 'SHELL'
#!/bin/bash
# Enable monitor mode on wlan1
sudo airmon-ng check kill
sudo airmon-ng start wlan1
echo "[+] Monitor mode ready. Interface: wlan1mon"
SHELL
chmod +x setup_monitor.sh

echo ""
echo "[+] Installation complete!"
echo ""
echo "Quick start:"
echo "  1. Connect external WiFi adapter"
echo "  2. ./setup_monitor.sh"
echo "  3. sudo python3 main.py"
echo ""
echo "Report output: ./reports/"
echo "Device DB:     ./data/captured_devices.json"
