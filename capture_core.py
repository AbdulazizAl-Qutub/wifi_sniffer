#!/usr/bin/env python3
"""
capture_core.py
Lightweight WiFi passive capture using raw AF_PACKET sockets
"""

import socket
import struct
import threading
import time
import json
import os

from collections import defaultdict
from datetime import datetime


class LightweightCapture:

    def __init__(
        self,
        interface="wlan0mon",
        db_path="data/captured_devices.json"
    ):

        self.interface = interface
        self.db_path = db_path
        self.running = False

        self.devices = defaultdict(lambda: {
            "mac": None,
            "first_seen": None,
            "last_seen": None,
            "probe_ssids": [],
            "rssi_values": [],
            "packet_count": 0,
            "oui_vendor": "Unknown"
        })

        self.packet_count = 0
        self.lock = threading.Lock()

        os.makedirs("data", exist_ok=True)

        self.oui_db = self.load_oui_db()

    def load_oui_db(self):

        oui = {}

        oui_path = "data/oui.txt"

        if os.path.exists(oui_path):

            with open(
                oui_path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:

                for line in f:

                    if "(hex)" in line:

                        parts = line.split()

                        if len(parts) >= 3:

                            prefix = parts[0].replace("-", ":").upper()

                            vendor = " ".join(parts[2:]).strip()

                            oui[prefix] = vendor

        return oui

    def lookup_oui(self, mac):

        prefix = mac.upper()[:8]

        return self.oui_db.get(prefix, "Unknown")

    def parse_radiotap_header(self, packet):

        try:

            if len(packet) < 8:
                return 24, None

            rt_len = struct.unpack("<H", packet[2:4])[0]

            rssi = None

            if len(packet) > 14:

                try:
                    rssi = struct.unpack("<b", packet[14:15])[0]
                except Exception:
                    pass

            return rt_len, rssi

        except Exception:

            return 24, None

    def parse_80211_packet(self, packet, rt_len):

        try:

            frame = packet[rt_len:]

            if len(frame) < 26:
                return None

            fc = struct.unpack("<H", frame[0:2])[0]

            frame_type = (fc >> 2) & 0x3
            frame_subtype = (fc >> 4) & 0xF

            # Probe Request
            if frame_type == 0 and frame_subtype == 4:

                addr2 = frame[10:16]

                mac = ":".join(f"{b:02x}" for b in addr2)

                if mac == "ff:ff:ff:ff:ff:ff":
                    return None

                result = {
                    "mac": mac.lower(),
                    "ssids": []
                }

                tag_offset = 24

                while tag_offset + 2 <= len(frame):

                    try:

                        tag_num = frame[tag_offset]
                        tag_len = frame[tag_offset + 1]

                        if tag_offset + 2 + tag_len > len(frame):
                            break

                        # SSID tag
                        if tag_num == 0 and tag_len > 0:

                            ssid_bytes = frame[
                                tag_offset + 2:
                                tag_offset + 2 + tag_len
                            ]

                            try:

                                ssid = ssid_bytes.decode(
                                    "utf-8",
                                    errors="ignore"
                                ).strip()

                                if ssid:
                                    result["ssids"].append(ssid)

                            except Exception:
                                pass

                        tag_offset += 2 + tag_len

                    except Exception:
                        break

                return result

        except Exception:
            return None

        return None

    def capture_loop(self):

        try:

            sock = socket.socket(
                socket.AF_PACKET,
                socket.SOCK_RAW,
                socket.ntohs(0x0003)
            )

            sock.bind((self.interface, 0))

            sock.settimeout(1.0)

        except PermissionError:

            print("[!] Root privileges required")
            print(f"    Run: sudo python3 {_file_}")

            return

        except OSError as e:

            print(f"[!] Interface error: {e}")
            print("[!] Make sure monitor mode is enabled")
            print("    Example:")
            print("    sudo airmon-ng start wlan0")

            return

        print(f"[+] Capture started on {self.interface}")

        while self.running:

            try:

                packet = sock.recv(65535)

                if len(packet) < 30:
                    continue

                rt_len, rssi = self.parse_radiotap_header(packet)

                if rt_len >= len(packet):
                    continue

                parsed = self.parse_80211_packet(packet, rt_len)

                if parsed and parsed.get("mac"):

                    with self.lock:

                        mac = parsed["mac"]

                        dev = self.devices[mac]

                        dev["mac"] = mac

                        dev["oui_vendor"] = self.lookup_oui(mac)

                        now = datetime.now().isoformat()

                        if dev["first_seen"] is None:
                            dev["first_seen"] = now

                        dev["last_seen"] = now

                        dev["packet_count"] += 1

                        if rssi is not None:

                            dev["rssi_values"].append(rssi)

                            if len(dev["rssi_values"]) > 50:
                                dev["rssi_values"] = \
                                    dev["rssi_values"][-50:]

                        for ssid in parsed.get("ssids", []):

                            if ssid not in dev["probe_ssids"]:
                                dev["probe_ssids"].append(ssid)

                        self.packet_count += 1

            except socket.timeout:
                continue

            except KeyboardInterrupt:
                break

            except Exception:
                continue

        sock.close()

        print("[+] Capture stopped")

    def start(self):

        self.running = True

        self.thread = threading.Thread(
            target=self.capture_loop,
            daemon=True
        )

        self.thread.start()

    def stop(self):

        self.running = False

        if hasattr(self, "thread"):
            self.thread.join(timeout=2)

        self.save()

    def save(self):

        with self.lock:

            data = dict(self.devices)

            active = {}

            now = datetime.now()

            for mac, dev in data.items():

                try:

                    last = datetime.fromisoformat(dev["last_seen"])

                    age = (now - last).total_seconds()

                    if age < 300 or len(dev["probe_ssids"]) > 0:
                        active[mac] = dev

                except Exception:
                    continue

            with open(self.db_path, "w") as f:
                json.dump(active, f, indent=2)

    def get_devices_snapshot(self):

        with self.lock:
            return dict(self.devices)


if __name__ == "__main__":

    import sys

    iface = sys.argv[1] if len(sys.argv) > 1 else "wlan0mon"

    cap = LightweightCapture(interface=iface)

    cap.start()

    try:

        while True:

            time.sleep(5)

            print(
                f"[{len(cap.devices)}] devices seen | "
                f"[{cap.packet_count}] packets captured"
            )

    except KeyboardInterrupt:

        print("\n[!] Stopping capture...")

    finally:

        cap.stop()

