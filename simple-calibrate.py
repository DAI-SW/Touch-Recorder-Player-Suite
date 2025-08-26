#!/usr/bin/env python3
"""
Einfache Touch-Kalibrierung - Standalone Tool
"""

import subprocess
import re
import time
import sys

# Farben
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
NC = '\033[0m'

def calibrate_touch(device_num):
    """Einfache Touch-Kalibrierung"""
    device_path = f"/dev/input/event{device_num}"
    
    print(f"\n{YELLOW}🎯 TOUCH-KALIBRIERUNG{NC}")
    print(f"Device: {device_path}")
    print(f"\n{GREEN}Anleitung:{NC}")
    print("1. Ich zeige dir die Touch-Werte")
    print("2. Berühre Oben Links → notiere X,Y")
    print("3. Berühre Unten Rechts → notiere X,Y")
    print("4. Drücke Strg+C zum Beenden")
    print(f"\n{RED}Enter zum Start...{NC}")
    input()
    
    cmd = ['sudo', 'evtest', device_path]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    
    last_x = 0
    last_y = 0
    
    print(f"\n{CYAN}Touch-Events (berühre den Screen):{NC}")
    print("-" * 40)
    
    try:
        for line in proc.stdout:
            # X-Koordinate
            if "ABS_MT_POSITION_X" in line or "ABS_X" in line:
                match = re.search(r'value (\d+)', line)
                if match:
                    last_x = int(match.group(1))
                    
            # Y-Koordinate
            elif "ABS_MT_POSITION_Y" in line or "ABS_Y" in line:
                match = re.search(r'value (\d+)', line)
                if match:
                    last_y = int(match.group(1))
                    # Zeige aktuelle Position
                    print(f"\rPosition: X={last_x:5d}, Y={last_y:5d}", end='', flush=True)
                    
    except KeyboardInterrupt:
        print(f"\n\n{GREEN}Kalibrierung beendet{NC}")
        
    finally:
        proc.terminate()
        
    # Manuelle Eingabe
    print(f"\n{YELLOW}Bitte gib die notierten Werte ein:{NC}")
    
    try:
        print("\nOben Links:")
        x_min = int(input("  X-Wert: "))
        y_min = int(input("  Y-Wert: "))
        
        print("\nUnten Rechts:")
        x_max = int(input("  X-Wert: "))
        y_max = int(input("  Y-Wert: "))
        
        # Berechne Bereich
        touch_max_x = x_max - x_min
        touch_max_y = y_max - y_min
        
        print(f"\n{GREEN}✅ ERGEBNIS:{NC}")
        print(f"Touch-Bereich: {touch_max_x} x {touch_max_y}")
        print(f"Touch-Offset: ({x_min}, {y_min})")
        
        print(f"\n{CYAN}Füge diese Werte in touchscreen-simple.py ein:{NC}")
        print(f"self.touch_max_x = {touch_max_x}")
        print(f"self.touch_max_y = {touch_max_y}")
        print(f"self.touch_offset_x = {x_min}")
        print(f"self.touch_offset_y = {y_min}")
        
    except ValueError:
        print(f"{RED}Ungültige Eingabe!{NC}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        device = input("Touch-Device Nummer (z.B. 15): ")
    else:
        device = sys.argv[1]
        
    try:
        calibrate_touch(int(device))
    except Exception as e:
        print(f"{RED}Fehler: {e}{NC}")
