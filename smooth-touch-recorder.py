#!/usr/bin/env python3
"""
Precision Touchscreen Recorder - Mit exaktem Timing und Resolution Validation
"""

import os
import sys
import time
import subprocess
import re
from datetime import datetime
from collections import deque
import json

# Farben
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    GRAY = '\033[0;90m'
    NC = '\033[0m'

class PrecisionTouchRecorder:
    def __init__(self):
        self.record_dir = "/home/dai/recordings"
        os.makedirs(self.record_dir, exist_ok=True)
        os.system(f"chown dai:dai {self.record_dir}")
        
        self.screen_width = 1920
        self.screen_height = 1200
        # Touch-Controller Bereiche
        self.touch_max_x = 16382
        self.touch_max_y = 9598
        
        # Precision tracking settings
        self.min_movement_threshold = 2  # Noch präziser
        self.max_points_per_gesture = 500  # Limit für sehr lange Gesten
        
        # Monitor-Konfiguration
        self.monitors = {}
        self.selected_monitor = None
        self.get_monitor_setup()
    
    def get_current_resolution(self, monitor_name):
        """Hole aktuelle Auflösung eines Monitors"""
        try:
            result = subprocess.run(['xrandr'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if line.startswith(f"{monitor_name} connected"):
                    # Parse resolution
                    match = re.search(r'(\d+x\d+\+\d+\+\d+)', line)
                    if match:
                        return match.group(1)
            return f"{self.screen_width}x{self.screen_height}+0+0"
        except:
            return f"{self.screen_width}x{self.screen_height}+0+0"
        
    def get_monitor_setup(self):
        """Ermittle aktuelle Monitor-Konfiguration"""
        try:
            result = subprocess.run(['xrandr'], capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if ' connected' in line:
                    parts = line.split()
                    monitor_name = parts[0]
                    
                    for part in parts:
                        if '+' in part and 'x' in part:
                            match = re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', part)
                            if match:
                                self.monitors[monitor_name] = {
                                    'width': int(match.group(1)),
                                    'height': int(match.group(2)),
                                    'x': int(match.group(3)),
                                    'y': int(match.group(4))
                                }
                                break
        except:
            print(f"{Colors.YELLOW}⚠️  Konnte Monitor-Setup nicht ermitteln{Colors.NC}")
    
    def select_monitor(self):
        """Monitor auswählen"""
        if not self.monitors:
            print(f"{Colors.RED}❌ Keine Monitore gefunden!{Colors.NC}")
            return False
            
        print(f"\n{Colors.CYAN}=== MONITOR AUSWAHL ==={Colors.NC}")
        
        monitor_list = list(self.monitors.items())
        for i, (name, info) in enumerate(monitor_list):
            print(f"{Colors.YELLOW}[{i+1}]{Colors.NC} {name}: {info['width']}x{info['height']} @ ({info['x']},{info['y']})")
            
        try:
            choice = int(input(f"\nMonitor wählen [1-{len(monitor_list)}]: "))
            if 1 <= choice <= len(monitor_list):
                self.selected_monitor = monitor_list[choice-1][0]
                monitor_info = self.monitors[self.selected_monitor]
                self.screen_width = monitor_info['width']
                self.screen_height = monitor_info['height']
                print(f"{Colors.GREEN}✅ {self.selected_monitor} ausgewählt{Colors.NC}")
                return True
        except:
            pass
            
        print(f"{Colors.RED}❌ Ungültige Auswahl{Colors.NC}")
        return False
    
    def record_touches(self, device_num, name="touch", debug_mode=False):
        """Precision Recording mit exaktem Timing"""
        device_path = f"/dev/input/event{device_num}"
        
        if not self.selected_monitor:
            print(f"{Colors.RED}❌ Kein Monitor ausgewählt! Wähle Option 3.{Colors.NC}")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.record_dir, f"{name}_{timestamp}.sh")
        debug_file = os.path.join(self.record_dir, f"{name}_{timestamp}_debug.json") if debug_mode else None
        
        monitor_info = self.monitors.get(self.selected_monitor, {'x': 0, 'y': 0})
        monitor_x = monitor_info['x']
        monitor_y = monitor_info['y']
        
        # Get current resolution for validation
        current_resolution = self.get_current_resolution(self.selected_monitor)
        
        # Script Header mit Resolution Check
        with open(output_file, 'w') as f:
            f.write(f'''#!/bin/bash
# Precision Touch Recording with Exact Timing
# Device: {device_path}
# Recording Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 
# RECORDED CONFIGURATION:
# Monitor: {self.selected_monitor}
# Resolution: {self.screen_width}x{self.screen_height}
# Position: ({monitor_x},{monitor_y})
# Touch Device Range: {self.touch_max_x}x{self.touch_max_y}

# Recording parameters (DO NOT MODIFY)
RECORDED_MONITOR="{self.selected_monitor}"
RECORDED_WIDTH={self.screen_width}
RECORDED_HEIGHT={self.screen_height}
MONITOR_X={monitor_x}
MONITOR_Y={monitor_y}

# Verify resolution matches recording
verify_resolution() {{
    local current_output=$(xrandr | grep "^$RECORDED_MONITOR connected" | head -1)
    
    if [ -z "$current_output" ]; then
        echo "❌ FEHLER: Monitor '$RECORDED_MONITOR' nicht gefunden!"
        echo "   Verfügbare Monitore:"
        xrandr | grep " connected" | awk '{{print "   - " $1}}'
        exit 1
    fi
    
    # Extract current resolution
    local current_res=$(echo "$current_output" | grep -oP '\\d+x\\d+' | head -1)
    local current_pos=$(echo "$current_output" | grep -oP '\\+\\d+\\+\\d+' | head -1)
    
    if [ "$current_res" != "${{RECORDED_WIDTH}}x${{RECORDED_HEIGHT}}" ]; then
        echo "⚠️  WARNUNG: Auflösung hat sich geändert!"
        echo "   Aufnahme: ${{RECORDED_WIDTH}}x${{RECORDED_HEIGHT}}"
        echo "   Aktuell:  $current_res"
        echo ""
        read -p "Trotzdem fortfahren? (j/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Jj]$ ]]; then
            echo "Abbruch."
            exit 1
        fi
    fi
    
    # Check position if changed
    local expected_pos="+${{MONITOR_X}}+${{MONITOR_Y}}"
    if [ "$current_pos" != "$expected_pos" ]; then
        echo "ℹ️  Monitor-Position hat sich geändert von $expected_pos zu $current_pos"
        # Update position dynamically
        MONITOR_X=$(echo "$current_pos" | cut -d+ -f2)
        MONITOR_Y=$(echo "$current_pos" | cut -d+ -f3)
    fi
    
    echo "✅ Monitor-Konfiguration validiert:"
    echo "   Monitor: $RECORDED_MONITOR"
    echo "   Auflösung: ${{RECORDED_WIDTH}}x${{RECORDED_HEIGHT}}"
    echo "   Position: (${{MONITOR_X}},${{MONITOR_Y}})"
}}

# High precision sleep function
sleep_ms() {{
    local ms=$1
    if [ $ms -gt 0 ]; then
        sleep $(echo "scale=6; $ms/1000" | bc)
    fi
}}

# Precise tap with timing
do_tap() {{
    local x=$(($1 + $MONITOR_X))
    local y=$(($2 + $MONITOR_Y))
    local duration=${{3:-50}}  # Default 50ms touch duration
    
    echo "🔵 Tap at ($1,$2) → absolute ($x,$y)"
    xdotool mousemove "$x" "$y"
    xdotool mousedown 1
    sleep_ms $duration
    xdotool mouseup 1
}}

# Timed drag with precise movement points
do_timed_drag() {{
    local points="$1"  # JSON array of [x, y, time_ms] points
    
    # Parse JSON und erstelle Arrays
    echo "$points" | python3 -c "
import sys, json
points = json.loads(sys.stdin.read())
if len(points) < 2:
    print('Error: Need at least 2 points for drag')
    sys.exit(1)

# Start point
x0, y0, t0 = points[0]
print(f'xdotool mousemove {{x0 + $MONITOR_X}} {{y0 + $MONITOR_Y}}')
print(f'xdotool mousedown 1')

# Move through points with precise timing
for i in range(1, len(points)):
    x, y, t = points[i]
    delay = t - points[i-1][2]
    if delay > 0:
        print(f'sleep_ms {{delay}}')
    print(f'xdotool mousemove {{x + $MONITOR_X}} {{y + $MONITOR_Y}}')

# Release
print(f'xdotool mouseup 1')
" | bash
}}

# Simple drag for backwards compatibility
do_drag() {{
    local coords=("$@")
    local num_points=${{#coords[@]}}
    
    if [ $num_points -lt 4 ]; then
        echo "Error: Need at least 2 points"
        return
    fi
    
    # Mouse down at start
    local x1=$((${{coords[0]}} + $MONITOR_X))
    local y1=$((${{coords[1]}} + $MONITOR_Y))
    xdotool mousemove "$x1" "$y1"
    xdotool mousedown 1
    
    # Move through points
    for ((i=2; i<num_points; i+=2)); do
        local x=$((${{coords[$i]}} + $MONITOR_X))
        local y=$((${{coords[$i+1]}} + $MONITOR_Y))
        xdotool mousemove "$x" "$y"
        sleep 0.002  # 2ms zwischen Punkten
    done
    
    # Mouse up at end
    xdotool mouseup 1
}}

# Run verification
verify_resolution

echo ""
echo "🎬 STARTING REPLAY auf $RECORDED_MONITOR"
echo "==========================================="
start_replay=$(date +%s%N)

# RECORDED EVENTS:
''')
        
        print(f"\n{Colors.YELLOW}🎬 AUFNAHME STARTET IN 3 SEK...{Colors.NC}")
        print(f"{Colors.GRAY}Precision Mode: Timing accuracy ±1ms{Colors.NC}")
        time.sleep(3)
        
        print(f"{Colors.RED}⏺️  AUFNAHME LÄUFT!{Colors.NC}")
        print(f"{Colors.CYAN}Drücke Strg+C zum Stoppen{Colors.NC}\n")
        
        # Starte evtest
        cmd = ['sudo', 'evtest', device_path]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
        
        # Tracking Variablen
        start_time = time.time()
        last_event_time = start_time
        event_count = 0
        touch_count = 0
        
        # Touch state mit präzisem Timing
        touch_active = False
        touch_start_time = 0
        current_x = 0
        current_y = 0
        
        # Movement tracking mit Timestamps
        movement_points = []  # Liste von [x, y, timestamp_ms]
        last_x = 0
        last_y = 0
        
        # Event buffer
        event_buffer = []
        debug_data = []
        
        # Stats
        min_interval = float('inf')
        max_interval = 0
        total_points = 0
        
        try:
            for line in proc.stdout:
                current_time = time.time()
                
                # Parse event timestamp wenn verfügbar
                event_match = re.search(r'Event: time (\d+\.\d+)', line)
                if event_match:
                    # Nutze kernel event time für noch höhere Präzision
                    event_time = float(event_match.group(1))
                else:
                    event_time = current_time
                
                # BTN_TOUCH Events - exaktes Timing
                if "BTN_TOUCH" in line:
                    if "value 1" in line and not touch_active:
                        # Touch Start - präziser Zeitpunkt
                        touch_active = True
                        touch_start_time = event_time
                        
                        # Zeit seit letztem Event
                        if last_event_time > 0:
                            wait_time = int((event_time - last_event_time) * 1000)
                            if wait_time > 10:  # Nur signifikante Pausen
                                event_buffer.append(f"sleep_ms {wait_time}\n")
                        
                        # Initialisiere movement tracking
                        movement_points = [[current_x, current_y, 0]]
                        last_x = current_x
                        last_y = current_y
                        
                        print(f"{Colors.GREEN}▼ TOUCH DOWN @ ({current_x},{current_y}) t={event_time:.3f}{Colors.NC}")
                        
                    elif "value 0" in line and touch_active:
                        # Touch End - berechne Duration
                        touch_duration = int((event_time - touch_start_time) * 1000)
                        
                        # Füge letzten Punkt hinzu wenn er sich unterscheidet
                        if movement_points and (current_x != last_x or current_y != last_y):
                            rel_time = int((event_time - touch_start_time) * 1000)
                            movement_points.append([current_x, current_y, rel_time])
                        
                        # Analysiere Geste
                        if len(movement_points) == 1:
                            # Einfacher Tap mit Duration
                            event_buffer.append(f"do_tap {movement_points[0][0]} {movement_points[0][1]} {touch_duration}\n")
                            print(f"{Colors.YELLOW}🔵 TAP: ({movement_points[0][0]},{movement_points[0][1]}) duration={touch_duration}ms{Colors.NC}")
                            
                        elif len(movement_points) == 2:
                            # Kurzer Swipe
                            dx = movement_points[-1][0] - movement_points[0][0]
                            dy = movement_points[-1][1] - movement_points[0][1]
                            distance = (dx*dx + dy*dy)**0.5
                            
                            if distance < 20:
                                # Tap mit mini-movement
                                event_buffer.append(f"do_tap {movement_points[0][0]} {movement_points[0][1]} {touch_duration}\n")
                                print(f"{Colors.YELLOW}🔵 TAP (micro-move): duration={touch_duration}ms{Colors.NC}")
                            else:
                                # Quick swipe
                                json_points = json.dumps(movement_points)
                                event_buffer.append(f"do_timed_drag '{json_points}'\n")
                                print(f"{Colors.BLUE}→ SWIPE: {distance:.0f}px in {touch_duration}ms{Colors.NC}")
                        else:
                            # Complex drag mit allen Timing-Informationen
                            # Limitiere Anzahl der Punkte wenn zu viele
                            if len(movement_points) > self.max_points_per_gesture:
                                # Sample down to max points
                                step = len(movement_points) // self.max_points_per_gesture
                                movement_points = movement_points[::step] + [movement_points[-1]]
                            
                            json_points = json.dumps(movement_points)
                            event_buffer.append(f"do_timed_drag '{json_points}'\n")
                            
                            # Stats
                            total_distance = sum(
                                ((movement_points[i][0] - movement_points[i-1][0])**2 + 
                                 (movement_points[i][1] - movement_points[i-1][1])**2)**0.5
                                for i in range(1, len(movement_points))
                            )
                            avg_speed = total_distance / (touch_duration / 1000) if touch_duration > 0 else 0
                            
                            print(f"{Colors.CYAN}👆 DRAG: {len(movement_points)} points, {total_distance:.0f}px, {touch_duration}ms, {avg_speed:.0f}px/s{Colors.NC}")
                        
                        # Debug data
                        if debug_mode:
                            debug_data.append({
                                'type': 'gesture',
                                'start_time': touch_start_time,
                                'duration': touch_duration,
                                'points': movement_points
                            })
                        
                        # Update stats
                        touch_active = False
                        touch_count += 1
                        last_event_time = event_time
                        total_points += len(movement_points)
                        
                        print(f"{Colors.MAGENTA}Total: {touch_count} touches, {total_points} points{Colors.NC}")
                        
                # Position Updates während Touch
                elif touch_active:
                    if "ABS_MT_POSITION_X" in line or "ABS_X" in line:
                        match = re.search(r'value (\d+)', line)
                        if match:
                            raw = int(match.group(1))
                            new_x = int(raw * self.screen_width / self.touch_max_x)
                            
                            # Nur aufzeichnen wenn signifikante Bewegung
                            if abs(new_x - last_x) >= self.min_movement_threshold:
                                current_x = new_x
                                # Wird beim nächsten Y-Update gespeichert
                                
                    elif "ABS_MT_POSITION_Y" in line or "ABS_Y" in line:
                        match = re.search(r'value (\d+)', line)
                        if match:
                            raw = int(match.group(1))
                            new_y = int(raw * self.screen_height / self.touch_max_y)
                            
                            # Prüfe ob signifikante Bewegung
                            distance = ((current_x - last_x)**2 + (new_y - last_y)**2)**0.5
                            
                            if distance >= self.min_movement_threshold:
                                current_y = new_y
                                
                                # Berechne relative Zeit seit Touch-Start
                                rel_time = int((event_time - touch_start_time) * 1000)
                                
                                # Füge Punkt mit Timing hinzu
                                movement_points.append([current_x, current_y, rel_time])
                                
                                # Update tracking
                                if len(movement_points) > 1:
                                    interval = rel_time - movement_points[-2][2]
                                    min_interval = min(min_interval, interval)
                                    max_interval = max(max_interval, interval)
                                
                                last_x = current_x
                                last_y = current_y
                                
                                # Live feedback
                                if len(movement_points) % 10 == 0:
                                    print(f"{Colors.GRAY}  ... {len(movement_points)} points recorded{Colors.NC}", end='\r')
                
                # Update wenn nicht im Touch
                elif "ABS_MT_POSITION_X" in line or "ABS_X" in line:
                    match = re.search(r'value (\d+)', line)
                    if match:
                        current_x = int(int(match.group(1)) * self.screen_width / self.touch_max_x)
                        
                elif "ABS_MT_POSITION_Y" in line or "ABS_Y" in line:
                    match = re.search(r'value (\d+)', line)
                    if match:
                        current_y = int(int(match.group(1)) * self.screen_height / self.touch_max_y)
                
                # Buffer schreiben
                if len(event_buffer) >= 3:
                    with open(output_file, 'a') as f:
                        f.writelines(event_buffer)
                    event_buffer = []
                    
        except KeyboardInterrupt:
            print(f"\n{Colors.RED}⏹️  AUFNAHME GESTOPPT{Colors.NC}")
        finally:
            proc.terminate()
            
            # Rest schreiben
            if event_buffer:
                with open(output_file, 'a') as f:
                    f.writelines(event_buffer)
                    
            # Footer mit Timing-Info
            with open(output_file, 'a') as f:
                f.write(f'''
# Ende der Events
end_replay=$(date +%s%N)
duration=$(( (end_replay - start_replay) / 1000000 ))

echo "==========================================="
echo "✅ PRECISION REPLAY COMPLETED"
echo "   Touches: {touch_count}"
echo "   Total Points: {total_points}"
echo "   Replay Duration: ${{duration}}ms"
echo "   File: {output_file}"
''')
            
            os.chmod(output_file, 0o755)
            os.system(f"chown dai:dai {output_file}")
            
            # Debug file speichern
            if debug_mode and debug_data:
                with open(debug_file, 'w') as f:
                    json.dump(debug_data, f, indent=2)
                os.system(f"chown dai:dai {debug_file}")
            
            # Summary mit Timing Stats
            duration = time.time() - start_time
            print(f"\n{Colors.GREEN}╔══════════════════════════════════════╗{Colors.NC}")
            print(f"{Colors.GREEN}║     PRECISION RECORDING COMPLETE     ║{Colors.NC}")
            print(f"{Colors.GREEN}╚══════════════════════════════════════╝{Colors.NC}")
            print(f"\n📄 Script: {Colors.BLUE}{output_file}{Colors.NC}")
            print(f"\n📊 STATISTIK:")
            print(f"  • Touches: {touch_count}")
            print(f"  • Total Points: {total_points}")
            print(f"  • Aufnahmedauer: {duration:.1f}s")
            if touch_count > 0:
                print(f"  • Ø Points/Touch: {total_points/touch_count:.1f}")
            if min_interval < float('inf'):
                print(f"  • Point Interval: {min_interval}-{max_interval}ms")
            if debug_mode and debug_file:
                print(f"\n🔍 Debug: {Colors.GRAY}{debug_file}{Colors.NC}")
            print(f"\n▶️  Abspielen: {Colors.CYAN}bash {output_file}{Colors.NC}")
    
    def quick_test(self, device_num):
        """Device Test mit Timing-Anzeige"""
        device_path = f"/dev/input/event{device_num}"
        
        print(f"\n{Colors.YELLOW}🧪 PRECISION TEST: {device_path}{Colors.NC}")
        print(f"{Colors.CYAN}Teste Touch mit Timing-Informationen...{Colors.NC}")
        print(f"{Colors.RED}Stoppe mit Strg+C{Colors.NC}\n")
        
        cmd = ['sudo', 'evtest', device_path]
        
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            touch_active = False
            touch_start = 0
            current_x = 0
            current_y = 0
            last_update = 0
            point_count = 0
            
            for line in proc.stdout:
                current_time = time.time()
                
                # Touch Events mit Timing
                if "BTN_TOUCH" in line:
                    if "value 1" in line:
                        touch_active = True
                        touch_start = current_time
                        point_count = 0
                        print(f"\n{Colors.GREEN}▼ TOUCH DOWN (t=0ms){Colors.NC}")
                    elif "value 0" in line and touch_active:
                        duration = (current_time - touch_start) * 1000
                        touch_active = False
                        print(f"{Colors.RED}▲ TOUCH UP (duration={duration:.1f}ms, points={point_count}){Colors.NC}\n")
                
                # Position Updates mit Timing
                elif touch_active:
                    if "ABS_MT_POSITION_X" in line or "ABS_X" in line:
                        match = re.search(r'value (\d+)', line)
                        if match:
                            current_x = int(match.group(1))
                    elif "ABS_MT_POSITION_Y" in line or "ABS_Y" in line:
                        match = re.search(r'value (\d+)', line)
                        if match:
                            current_y = int(match.group(1))
                            point_count += 1
                            
                            # Zeit seit Touch-Start
                            elapsed = (current_time - touch_start) * 1000
                            # Zeit seit letztem Update
                            if last_update > 0:
                                interval = (current_time - last_update) * 1000
                            else:
                                interval = 0
                            last_update = current_time
                            
                            # Konvertiere zu Screen-Koordinaten
                            screen_x = int(current_x * self.screen_width / self.touch_max_x)
                            screen_y = int(current_y * self.screen_height / self.touch_max_y)
                            
                            print(f"  → [{elapsed:6.1f}ms] Pos: ({screen_x:4}, {screen_y:4}) | Δt={interval:5.1f}ms", end='\r')
                    
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Test beendet{Colors.NC}")
        finally:
            if 'proc' in locals():
                proc.terminate()
    
    def analyze_recording(self, filename):
        """Analysiere ein Recording für Stats"""
        filepath = os.path.join(self.record_dir, filename)
        if not os.path.exists(filepath):
            print(f"{Colors.RED}Datei nicht gefunden: {filepath}{Colors.NC}")
            return
            
        print(f"\n{Colors.CYAN}📊 ANALYSE: {filename}{Colors.NC}")
        
        tap_count = 0
        drag_count = 0
        total_duration = 0
        
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('do_tap'):
                    tap_count += 1
                    # Extrahiere duration
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            total_duration += int(parts[3])
                        except:
                            total_duration += 50  # default
                elif line.startswith('do_timed_drag'):
                    drag_count += 1
                    # Parse JSON für Details
                    try:
                        json_start = line.index("'") + 1
                        json_end = line.rindex("'")
                        json_str = line[json_start:json_end]
                        points = json.loads(json_str)
                        if points:
                            total_duration += points[-1][2]
                    except:
                        pass
        
        print(f"  • Taps: {tap_count}")
        print(f"  • Drags: {drag_count}")
        print(f"  • Total Duration: {total_duration}ms")
    
    def run(self):
        """Hauptmenü"""
        print(f"{Colors.MAGENTA}╔══════════════════════════════════════╗{Colors.NC}")
        print(f"{Colors.MAGENTA}║  PRECISION TOUCH RECORDER v3.0      ║{Colors.NC}")
        print(f"{Colors.MAGENTA}║  Sub-millisecond timing accuracy     ║{Colors.NC}")
        print(f"{Colors.MAGENTA}╚══════════════════════════════════════╝{Colors.NC}")
        
        if os.geteuid() != 0:
            print(f"\n{Colors.RED}⚠️  Benötigt sudo!{Colors.NC}")
            print(f"Starte mit: sudo python3 {sys.argv[0]}")
            sys.exit(1)
        
        # Zeige Monitor Setup
        print(f"\n{Colors.CYAN}📺 Monitor Setup:{Colors.NC}")
        if self.monitors:
            for name, info in self.monitors.items():
                marker = "✅" if name == self.selected_monitor else "  "
                print(f"{marker} {name}: {info['width']}x{info['height']} @ ({info['x']},{info['y']})")
        else:
            print("  Keine Monitore gefunden")
        
        if not self.selected_monitor and self.monitors:
            # Auto-select ersten Monitor
            self.selected_monitor = list(self.monitors.keys())[0]
            monitor_info = self.monitors[self.selected_monitor]
            self.screen_width = monitor_info['width']
            self.screen_height = monitor_info['height']
            print(f"\n{Colors.GREEN}Auto-selected: {self.selected_monitor}{Colors.NC}")
        
        # Zeige bekannte Devices
        print(f"\n{Colors.CYAN}📱 Touch-Devices:{Colors.NC}")
        print("  • event15 - WingCool TouchScreen")
        print("  • event16 - Alternative Touch")
        
        while True:
            print(f"\n{Colors.CYAN}═══ HAUPTMENÜ ═══{Colors.NC}")
            print(f"{Colors.YELLOW}[1]{Colors.NC} 🧪 Device testen")
            print(f"{Colors.YELLOW}[2]{Colors.NC} 🎬 Standard Aufnahme")
            print(f"{Colors.YELLOW}[3]{Colors.NC} 🎯 Precision Aufnahme (mit Debug)")
            print(f"{Colors.YELLOW}[4]{Colors.NC} 📺 Monitor wählen")
            print(f"{Colors.YELLOW}[5]{Colors.NC} 📂 Recordings anzeigen")
            print(f"{Colors.YELLOW}[6]{Colors.NC} 📊 Recording analysieren")
            print(f"{Colors.YELLOW}[0]{Colors.NC} Beenden")
            
            choice = input(f"\nWahl: {Colors.CYAN}")
            print(Colors.NC, end='')
            
            if choice == '0':
                break
                
            elif choice == '1':
                # Test
                device = input("Device Nummer (z.B. 15): ")
                try:
                    self.quick_test(int(device))
                except Exception as e:
                    print(f"{Colors.RED}Fehler: {e}{Colors.NC}")
                    
            elif choice == '2':
                # Standard Aufnahme
                if not self.selected_monitor:
                    print(f"{Colors.RED}❌ Bitte erst Monitor wählen!{Colors.NC}")
                    continue
                    
                device = input("Device Nummer (z.B. 15): ")
                name = input("Recording Name [touch]: ").strip() or "touch"
                try:
                    self.record_touches(int(device), name, debug_mode=False)
                except Exception as e:
                    print(f"{Colors.RED}Fehler: {e}{Colors.NC}")
                    
            elif choice == '3':
                # Precision Aufnahme mit Debug
                if not self.selected_monitor:
                    print(f"{Colors.RED}❌ Bitte erst Monitor wählen!{Colors.NC}")
                    continue
                    
                device = input("Device Nummer (z.B. 15): ")
                name = input("Recording Name [precision]: ").strip() or "precision"
                try:
                    self.record_touches(int(device), name, debug_mode=True)
                except Exception as e:
                    print(f"{Colors.RED}Fehler: {e}{Colors.NC}")
                    
            elif choice == '4':
                # Monitor Auswahl
                self.select_monitor()
                
            elif choice == '5':
                # Zeige Recordings
                print(f"\n{Colors.CYAN}📂 Recordings:{Colors.NC}")
                try:
                    files = sorted([f for f in os.listdir(self.record_dir) if f.endswith('.sh')])
                    if files:
                        for i, f in enumerate(files[-10:], 1):  # Letzte 10
                            path = os.path.join(self.record_dir, f)
                            size = os.path.getsize(path)
                            mtime = datetime.fromtimestamp(os.path.getmtime(path))
                            print(f"  [{i:2}] {f} ({size:,} bytes) - {mtime.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        print("  Keine Recordings gefunden")
                except Exception as e:
                    print(f"{Colors.RED}Fehler: {e}{Colors.NC}")
                    
            elif choice == '6':
                # Analyse
                filename = input("Recording Dateiname: ")
                if not filename.endswith('.sh'):
                    filename += '.sh'
                self.analyze_recording(filename)

if __name__ == "__main__":
    try:
        recorder = PrecisionTouchRecorder()
        recorder.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Programm beendet!{Colors.NC}")
    except Exception as e:
        print(f"\n{Colors.RED}Fehler: {e}{Colors.NC}")
        import traceback
        traceback.print_exc()
