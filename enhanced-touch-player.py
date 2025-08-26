#!/usr/bin/env python3
"""
Enhanced Touch Recording Player - Mit einstellbarer Wiedergabegeschwindigkeit
"""

import os
import sys
import time
import subprocess
import signal
import threading
from datetime import datetime
import glob
import re
import tempfile
import shutil

# Farben
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    GRAY = '\033[0;90m'
    NC = '\033[0m'

class EnhancedTouchPlayer:
    def __init__(self):
        self.recordings_dir = "/home/dai/recordings"
        self.temp_dir = tempfile.mkdtemp(prefix="touch_player_")
        self.log_file = os.path.join(self.recordings_dir, f"playback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.running = False
        self.current_process = None
        self.play_count = 0
        self.selected_script = None
        self.loop_mode = "single"  # single, count, infinite, random_count, duration
        self.loop_count = 1
        self.pause_duration = 0
        self.test_duration = 60  # Sekunden für Duration-Test
        
        # Speed control settings
        self.playback_speed = 1.0  # 1.0 = normal, 0.5 = half speed, 2.0 = double speed
        self.speed_presets = {
            "sehr langsam": 0.25,
            "langsam": 0.5,
            "normal": 1.0,
            "schnell": 1.5,
            "sehr schnell": 2.0,
            "turbo": 3.0
        }
        self.modified_script = None
        
        # Random speed settings
        self.use_random_speed = False
        self.random_speed_min = 0.5
        self.random_speed_max = 2.0
        self.speed_change_mode = "per_loop"  # per_loop, gradual, chaos
        
    def __del__(self):
        """Cleanup temp directory"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def log(self, message, level="INFO"):
        """Schreibe in Log-Datei und Console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # Console mit Farbe
        color = Colors.GREEN if level == "INFO" else Colors.YELLOW if level == "WARN" else Colors.RED
        print(f"{color}{log_entry}{Colors.NC}")
        
        # Log-Datei
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def find_recordings(self):
        """Finde alle Touch-Recording Scripts"""
        scripts = []
        pattern = os.path.join(self.recordings_dir, "*.sh")
        
        for file in sorted(glob.glob(pattern)):
            # Prüfe ob es ein Touch-Script ist
            with open(file, 'r') as f:
                content = f.read(500)
                if "Touch Recording" in content or "do_tap" in content:
                    scripts.append(file)
                    
        return scripts
    
    def show_recordings(self, scripts):
        """Zeige verfügbare Recordings"""
        print(f"\n{Colors.CYAN}=== VERFÜGBARE RECORDINGS ==={Colors.NC}")
        
        for i, script in enumerate(scripts):
            filename = os.path.basename(script)
            size = os.path.getsize(script) / 1024  # KB
            mtime = datetime.fromtimestamp(os.path.getmtime(script))
            
            # Zähle Touch-Events
            touch_count = 0
            with open(script, 'r') as f:
                content = f.read()
                touch_count = content.count('do_tap') + content.count('do_drag') + content.count('do_timed_drag')
            
            print(f"{Colors.YELLOW}[{i+1}]{Colors.NC} {filename}")
            print(f"    📅 {mtime.strftime('%Y-%m-%d %H:%M')}")
            print(f"    📊 {touch_count} Touch-Events, {size:.1f} KB")
            
            # Zeige geschätzte Duration
            duration = self.estimate_duration(script)
            if duration:
                print(f"    ⏱️  ~{duration:.1f}s @ 1x Speed")
    
    def estimate_duration(self, script_path):
        """Schätze die Dauer eines Scripts"""
        try:
            with open(script_path, 'r') as f:
                content = f.read()
            
            total_ms = 0
            
            # Finde alle sleep_ms commands
            for match in re.finditer(r'sleep_ms (\d+)', content):
                total_ms += int(match.group(1))
            
            # Finde do_tap mit duration
            for match in re.finditer(r'do_tap \d+ \d+ (\d+)', content):
                total_ms += int(match.group(1))
            
            # Schätze drag duration aus JSON
            for match in re.finditer(r'do_timed_drag \'([^\']+)\'', content):
                try:
                    import json
                    points = json.loads(match.group(1))
                    if points and len(points) > 0:
                        # Letzter timestamp ist die Duration
                        total_ms += points[-1][2]
                except:
                    total_ms += 1000  # Default 1s für drag
            
            return total_ms / 1000.0
        except:
            return None
    
    def select_recording(self):
        """Wähle ein Recording aus"""
        scripts = self.find_recordings()
        
        if not scripts:
            self.log("Keine Recordings gefunden!", "ERROR")
            return False
            
        self.show_recordings(scripts)
        
        try:
            choice = int(input(f"\n{Colors.CYAN}Recording wählen [1-{len(scripts)}]: {Colors.NC}"))
            if 1 <= choice <= len(scripts):
                self.selected_script = scripts[choice-1]
                self.log(f"Ausgewählt: {os.path.basename(self.selected_script)}")
                
                # Zeige geschätzte Dauer bei verschiedenen Speeds
                duration = self.estimate_duration(self.selected_script)
                if duration:
                    print(f"\n{Colors.GRAY}Geschätzte Dauer:{Colors.NC}")
                    for name, speed in self.speed_presets.items():
                        adjusted_duration = duration / speed
                        print(f"  • {name:12}: {adjusted_duration:5.1f}s")
                
                return True
        except:
            pass
            
        self.log("Ungültige Auswahl", "ERROR")
        return False
    
    def configure_speed(self):
        """Konfiguriere Wiedergabegeschwindigkeit"""
        print(f"\n{Colors.CYAN}=== GESCHWINDIGKEIT EINSTELLEN ==={Colors.NC}")
        print(f"Aktuell: {Colors.GREEN}{self.playback_speed}x{Colors.NC}")
        
        print(f"\n{Colors.YELLOW}[1]{Colors.NC} Sehr langsam (0.25x) - Debugging")
        print(f"{Colors.YELLOW}[2]{Colors.NC} Langsam (0.5x) - Präzise Beobachtung")
        print(f"{Colors.YELLOW}[3]{Colors.NC} Normal (1.0x) - Original-Geschwindigkeit")
        print(f"{Colors.YELLOW}[4]{Colors.NC} Schnell (1.5x) - Zeitsparend")
        print(f"{Colors.YELLOW}[5]{Colors.NC} Sehr schnell (2.0x) - Quick Test")
        print(f"{Colors.YELLOW}[6]{Colors.NC} Turbo (3.0x) - Stress-Test")
        print(f"{Colors.YELLOW}[7]{Colors.NC} Custom - Eigene Geschwindigkeit")
        
        try:
            choice = input(f"\n{Colors.CYAN}Geschwindigkeit [1-7]: {Colors.NC}")
            
            if choice == '1':
                self.playback_speed = 0.25
                preset = "Sehr langsam"
            elif choice == '2':
                self.playback_speed = 0.5
                preset = "Langsam"
            elif choice == '3':
                self.playback_speed = 1.0
                preset = "Normal"
            elif choice == '4':
                self.playback_speed = 1.5
                preset = "Schnell"
            elif choice == '5':
                self.playback_speed = 2.0
                preset = "Sehr schnell"
            elif choice == '6':
                self.playback_speed = 3.0
                preset = "Turbo"
            elif choice == '7':
                custom = float(input(f"{Colors.CYAN}Custom Speed (0.1-10.0): {Colors.NC}"))
                self.playback_speed = max(0.1, min(10.0, custom))
                preset = f"Custom {self.playback_speed}x"
            else:
                return False
            
            print(f"{Colors.GREEN}✅ Geschwindigkeit: {preset} ({self.playback_speed}x){Colors.NC}")
            
            # Zeige angepasste Duration
            if self.selected_script:
                duration = self.estimate_duration(self.selected_script)
                if duration:
                    adjusted = duration / self.playback_speed
                    print(f"{Colors.GRAY}Angepasste Dauer: ~{adjusted:.1f}s{Colors.NC}")
            
            return True
            
        except Exception as e:
            self.log(f"Ungültige Eingabe: {e}", "ERROR")
            return False
    
    def create_speed_adjusted_script(self):
        """Erstelle ein geschwindigkeits-angepasstes Script"""
        if not self.selected_script:
            return None
        
        # Wenn normale Geschwindigkeit, nutze Original
        if self.playback_speed == 1.0:
            return self.selected_script
        
        # Lese Original-Script
        with open(self.selected_script, 'r') as f:
            content = f.read()
        
        # Passe sleep_ms Zeiten an
        def adjust_sleep(match):
            original_ms = int(match.group(1))
            adjusted_ms = int(original_ms / self.playback_speed)
            return f"sleep_ms {adjusted_ms}"
        
        content = re.sub(r'sleep_ms (\d+)', adjust_sleep, content)
        
        # Passe do_tap duration an
        def adjust_tap_duration(match):
            x, y = match.group(1), match.group(2)
            duration = int(match.group(3)) if match.group(3) else 50
            adjusted_duration = int(duration / self.playback_speed)
            return f"do_tap {x} {y} {adjusted_duration}"
        
        content = re.sub(r'do_tap (\d+) (\d+)(?: (\d+))?', adjust_tap_duration, content)
        
        # Passe do_timed_drag JSON an
        def adjust_timed_drag(match):
            json_str = match.group(1)
            try:
                import json
                points = json.loads(json_str)
                # Passe Timestamps an
                for point in points:
                    if len(point) >= 3:
                        point[2] = int(point[2] / self.playback_speed)
                adjusted_json = json.dumps(points)
                return f"do_timed_drag '{adjusted_json}'"
            except:
                return match.group(0)  # Unverändert lassen bei Fehler
        
        content = re.sub(r"do_timed_drag '([^']+)'", adjust_timed_drag, content)
        
        # Füge Speed-Info zum Header hinzu
        speed_info = f"\n# PLAYBACK SPEED: {self.playback_speed}x\n"
        content = content.replace("# RECORDED EVENTS:", speed_info + "# RECORDED EVENTS:")
        
        # Speichere modifiziertes Script
        modified_path = os.path.join(self.temp_dir, f"speed_{self.playback_speed}x_{os.path.basename(self.selected_script)}")
        with open(modified_path, 'w') as f:
            f.write(content)
        
        os.chmod(modified_path, 0o755)
        self.modified_script = modified_path
        
        return modified_path
    
    def configure_loop(self):
        """Konfiguriere Loop-Optionen mit Random Speed Support"""
        print(f"\n{Colors.CYAN}=== LOOP KONFIGURATION ==={Colors.NC}")
        print(f"{Colors.YELLOW}[1]{Colors.NC} Einmal abspielen")
        print(f"{Colors.YELLOW}[2]{Colors.NC} X-mal wiederholen")
        print(f"{Colors.YELLOW}[3]{Colors.NC} Unendlich wiederholen")
        print(f"{Colors.YELLOW}[4]{Colors.NC} Zufällige Anzahl (3-10)")
        print(f"{Colors.YELLOW}[5]{Colors.NC} ⏱️  Dauer-Test (Zeit-basiert)")
        print(f"{Colors.YELLOW}[6]{Colors.NC} 🎲 Random Speed Mode")
        
        try:
            choice = input(f"\n{Colors.CYAN}Loop-Modus [1-6]: {Colors.NC}")
            
            if choice == '1':
                self.loop_mode = "single"
                self.loop_count = 1
                self.use_random_speed = False
                
            elif choice == '2':
                count = int(input(f"{Colors.CYAN}Anzahl Wiederholungen: {Colors.NC}"))
                self.loop_mode = "count"
                self.loop_count = max(1, count)
                
            elif choice == '3':
                self.loop_mode = "infinite"
                self.loop_count = -1
                
            elif choice == '4':
                import random
                self.loop_mode = "random_count"
                self.loop_count = random.randint(3, 10)
                print(f"{Colors.GREEN}Zufällig gewählt: {self.loop_count} Wiederholungen{Colors.NC}")
                
            elif choice == '5':
                # Duration-basierter Test
                duration_min = float(input(f"{Colors.CYAN}Test-Dauer in Minuten [1-60]: {Colors.NC}"))
                self.test_duration = duration_min * 60
                self.loop_mode = "duration"
                self.loop_count = -1  # Unbekannt
                print(f"{Colors.GREEN}Duration-Test: {duration_min} Minuten{Colors.NC}")
                
            elif choice == '6':
                # Random Speed Mode
                self.configure_random_speed()
                return True
            
            else:
                return False
            
            # Frage nach Random Speed bei Loops
            if self.loop_mode != "single":
                print(f"\n{Colors.CYAN}=== SPEED OPTIONEN ==={Colors.NC}")
                print(f"{Colors.YELLOW}[1]{Colors.NC} Feste Geschwindigkeit beibehalten")
                print(f"{Colors.YELLOW}[2]{Colors.NC} 🎲 Zufällige Geschwindigkeit pro Durchlauf")
                print(f"{Colors.YELLOW}[3]{Colors.NC} 📈 Graduelle Änderung (langsam → schnell)")
                print(f"{Colors.YELLOW}[4]{Colors.NC} 🌀 Chaos Mode (völlig zufällig)")
                
                speed_choice = input(f"\n{Colors.CYAN}Speed-Modus [1-4]: {Colors.NC}")
                
                if speed_choice == '2':
                    self.use_random_speed = True
                    self.speed_change_mode = "per_loop"
                    self.configure_random_speed_range()
                    
                elif speed_choice == '3':
                    self.use_random_speed = True
                    self.speed_change_mode = "gradual"
                    print(f"{Colors.GREEN}Graduelle Beschleunigung aktiviert{Colors.NC}")
                    
                elif speed_choice == '4':
                    self.use_random_speed = True
                    self.speed_change_mode = "chaos"
                    self.random_speed_min = 0.1
                    self.random_speed_max = 5.0
                    print(f"{Colors.YELLOW}⚠️  CHAOS MODE: 0.1x - 5.0x{Colors.NC}")
                else:
                    self.use_random_speed = False
                
                # Pause zwischen Wiederholungen
                pause = input(f"\n{Colors.CYAN}Pause zwischen Wiederholungen (Sekunden) [0]: {Colors.NC}")
                self.pause_duration = float(pause) if pause else 0
                
            return True
            
        except Exception as e:
            self.log(f"Ungültige Eingabe: {e}", "ERROR")
            return False
    
    def configure_random_speed(self):
        """Konfiguriere Random Speed Mode im Detail"""
        print(f"\n{Colors.CYAN}=== RANDOM SPEED KONFIGURATION ==={Colors.NC}")
        
        print(f"{Colors.YELLOW}[1]{Colors.NC} Standard Random (0.5x - 2.0x)")
        print(f"{Colors.YELLOW}[2]{Colors.NC} Slow Motion Focus (0.25x - 1.0x)")
        print(f"{Colors.YELLOW}[3]{Colors.NC} Speed Test (1.0x - 3.0x)")
        print(f"{Colors.YELLOW}[4]{Colors.NC} Extreme Range (0.1x - 5.0x)")
        print(f"{Colors.YELLOW}[5]{Colors.NC} Custom Range")
        
        try:
            choice = input(f"\n{Colors.CYAN}Range auswählen [1-5]: {Colors.NC}")
            
            if choice == '1':
                self.random_speed_min = 0.5
                self.random_speed_max = 2.0
            elif choice == '2':
                self.random_speed_min = 0.25
                self.random_speed_max = 1.0
            elif choice == '3':
                self.random_speed_min = 1.0
                self.random_speed_max = 3.0
            elif choice == '4':
                self.random_speed_min = 0.1
                self.random_speed_max = 5.0
            elif choice == '5':
                self.random_speed_min = float(input(f"{Colors.CYAN}Min Speed (0.1-10): {Colors.NC}"))
                self.random_speed_max = float(input(f"{Colors.CYAN}Max Speed (0.1-10): {Colors.NC}"))
                
            # Loop-Anzahl für Random Speed
            print(f"\n{Colors.CYAN}Loop-Anzahl:{Colors.NC}")
            print(f"{Colors.YELLOW}[1]{Colors.NC} 10 Durchläufe")
            print(f"{Colors.YELLOW}[2]{Colors.NC} 25 Durchläufe")
            print(f"{Colors.YELLOW}[3]{Colors.NC} 50 Durchläufe")
            print(f"{Colors.YELLOW}[4]{Colors.NC} Unendlich")
            print(f"{Colors.YELLOW}[5]{Colors.NC} Zeit-basiert")
            
            loop_choice = input(f"\n{Colors.CYAN}Auswahl [1-5]: {Colors.NC}")
            
            if loop_choice == '1':
                self.loop_mode = "count"
                self.loop_count = 10
            elif loop_choice == '2':
                self.loop_mode = "count"
                self.loop_count = 25
            elif loop_choice == '3':
                self.loop_mode = "count"
                self.loop_count = 50
            elif loop_choice == '4':
                self.loop_mode = "infinite"
                self.loop_count = -1
            elif loop_choice == '5':
                minutes = float(input(f"{Colors.CYAN}Minuten [1-60]: {Colors.NC}"))
                self.test_duration = minutes * 60
                self.loop_mode = "duration"
                
            self.use_random_speed = True
            self.speed_change_mode = "per_loop"
            
            print(f"\n{Colors.GREEN}✅ Random Speed konfiguriert:{Colors.NC}")
            print(f"   Range: {self.random_speed_min}x - {self.random_speed_max}x")
            print(f"   Loops: {self.loop_count if self.loop_count > 0 else 'Unendlich/Zeit-basiert'}")
            
        except Exception as e:
            self.log(f"Fehler: {e}", "ERROR")
    
    def configure_random_speed_range(self):
        """Konfiguriere Random Speed Range"""
        print(f"\n{Colors.CYAN}Speed Range festlegen:{Colors.NC}")
        try:
            self.random_speed_min = float(input(f"Min Speed [0.25]: ") or "0.25")
            self.random_speed_max = float(input(f"Max Speed [2.0]: ") or "2.0")
            
            # Validierung
            self.random_speed_min = max(0.1, min(self.random_speed_min, 10.0))
            self.random_speed_max = max(self.random_speed_min, min(self.random_speed_max, 10.0))
            
            print(f"{Colors.GREEN}Random Speed: {self.random_speed_min}x - {self.random_speed_max}x{Colors.NC}")
        except:
            self.random_speed_min = 0.5
            self.random_speed_max = 2.0
            print(f"{Colors.YELLOW}Standard Range: 0.5x - 2.0x{Colors.NC}")
    
    def get_next_speed(self):
        """Berechne nächste Geschwindigkeit basierend auf Modus"""
        import random
        
        if not self.use_random_speed:
            return self.playback_speed
        
        if self.speed_change_mode == "per_loop":
            # Zufällige Speed pro Loop
            return round(random.uniform(self.random_speed_min, self.random_speed_max), 2)
            
        elif self.speed_change_mode == "gradual":
            # Graduelle Änderung von langsam zu schnell
            if self.loop_count > 0:
                progress = self.play_count / self.loop_count
                speed = self.random_speed_min + (self.random_speed_max - self.random_speed_min) * progress
                return round(speed, 2)
            else:
                # Bei unendlich: Sinus-Welle
                import math
                cycle = math.sin(self.play_count * 0.2) * 0.5 + 0.5
                speed = self.random_speed_min + (self.random_speed_max - self.random_speed_min) * cycle
                return round(speed, 2)
                
        elif self.speed_change_mode == "chaos":
            # Völlig zufällig mit extremen Werten
            if random.random() < 0.1:  # 10% Chance für Extrem
                return round(random.choice([0.1, 0.2, 4.0, 5.0]), 2)
            else:
                return round(random.uniform(0.5, 2.5), 2)
    
    def play_script(self):
        """Spiele das Script einmal ab"""
        # Erstelle speed-angepasstes Script
        script_to_play = self.create_speed_adjusted_script()
        if not script_to_play:
            self.log("Kein Script zum Abspielen", "ERROR")
            return False
        
        speed_info = f" @ {self.playback_speed}x Speed" if self.playback_speed != 1.0 else ""
        self.log(f"Starte Playback #{self.play_count + 1}{speed_info}")
        
        try:
            # Führe Script aus
            self.current_process = subprocess.Popen(
                ['bash', script_to_play],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Zeige Output mit Speed-Indikator
            for line in self.current_process.stdout:
                if self.playback_speed != 1.0:
                    # Füge Speed-Indikator hinzu
                    print(f"  {Colors.WHITE}[{self.playback_speed}x] {line.strip()}{Colors.NC}")
                else:
                    print(f"  {Colors.WHITE}{line.strip()}{Colors.NC}")
                    
            # Warte auf Ende
            self.current_process.wait()
            
            if self.current_process.returncode == 0:
                self.play_count += 1
                self.log(f"Playback #{self.play_count} erfolgreich{speed_info}")
                return True
            else:
                self.log(f"Playback Fehler: Return Code {self.current_process.returncode}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Playback Fehler: {e}", "ERROR")
            return False
        finally:
            self.current_process = None
    
    def run_loop(self):
        """Hauptloop für Playback mit Random Speed Support"""
        self.running = True
        self.play_count = 0
        start_time = time.time()
        
        # Speed History für Statistiken
        speed_history = []
        
        speed_info = f" @ {self.playback_speed}x" if self.playback_speed != 1.0 else ""
        if self.use_random_speed:
            speed_info = f" mit Random Speed ({self.random_speed_min}x-{self.random_speed_max}x)"
        
        self.log(f"Starte Loop-Modus: {self.loop_mode}{speed_info}")
        
        try:
            while self.running:
                # Setze Speed für diesen Durchlauf
                if self.use_random_speed:
                    self.playback_speed = self.get_next_speed()
                    speed_history.append(self.playback_speed)
                    print(f"\n{Colors.CYAN}🎲 Durchlauf #{self.play_count + 1} mit {self.playback_speed}x Speed{Colors.NC}")
                
                # Spiele Script
                if not self.play_script():
                    break
                
                # Check Loop-Bedingung
                if self.loop_mode == "single":
                    break
                elif self.loop_mode == "count" and self.play_count >= self.loop_count:
                    break
                elif self.loop_mode == "random_count" and self.play_count >= self.loop_count:
                    break
                elif self.loop_mode == "duration":
                    elapsed = time.time() - start_time
                    remaining = self.test_duration - elapsed
                    if remaining <= 0:
                        self.log(f"Duration-Test beendet nach {elapsed:.1f}s")
                        break
                    else:
                        print(f"{Colors.GRAY}⏱️  Noch {remaining:.0f}s verbleibend...{Colors.NC}")
                
                # Pause zwischen Loops
                if self.pause_duration > 0 and self.running:
                    # Variiere Pause bei Random Speed
                    pause_time = self.pause_duration
                    if self.use_random_speed and self.speed_change_mode == "chaos":
                        import random
                        pause_time = random.uniform(0.5, self.pause_duration * 2)
                    
                    self.log(f"Pause {pause_time:.1f}s...")
                    
                    # Interruptible sleep
                    for i in range(int(pause_time)):
                        if not self.running:
                            break
                        time.sleep(1)
                        remaining = int(pause_time - i - 1)
                        if remaining > 0:
                            print(f"\r  ⏱️  Noch {remaining}s...", end='', flush=True)
                    print()  # Neue Zeile
                    
        except KeyboardInterrupt:
            self.log("Abbruch durch Benutzer", "WARN")
        finally:
            self.running = False
            total_time = time.time() - start_time
            
            # Erweiterte Statistiken
            if self.use_random_speed and speed_history:
                avg_speed = sum(speed_history) / len(speed_history)
                min_speed = min(speed_history)
                max_speed = max(speed_history)
                
                print(f"\n{Colors.CYAN}📊 RANDOM SPEED STATISTIK:{Colors.NC}")
                print(f"  • Durchschnitt: {avg_speed:.2f}x")
                print(f"  • Min/Max: {min_speed}x / {max_speed}x")
                print(f"  • Variationen: {len(set(speed_history))}")
                
                # Speed Distribution
                print(f"\n{Colors.CYAN}Speed-Verteilung:{Colors.NC}")
                for speed_val in sorted(set(speed_history)):
                    count = speed_history.count(speed_val)
                    bar = "█" * min(30, int(count * 30 / len(speed_history)))
                    print(f"  {speed_val:4.2f}x [{count:3}] {bar}")
            
            self.log(f"Loop beendet. Total: {self.play_count} Durchläufe in {total_time:.1f}s")
    
    def show_stats(self):
        """Zeige Statistiken"""
        print(f"\n{Colors.GREEN}╔══════════════════════════════════════╗{Colors.NC}")
        print(f"{Colors.GREEN}📊 PLAYBACK STATISTIKEN{Colors.NC}")
        print(f"{Colors.GREEN}╚══════════════════════════════════════╝{Colors.NC}")
        print(f"Script: {Colors.BLUE}{os.path.basename(self.selected_script)}{Colors.NC}")
        print(f"Geschwindigkeit: {Colors.YELLOW}{self.playback_speed}x{Colors.NC}")
        print(f"Durchläufe: {Colors.YELLOW}{self.play_count}{Colors.NC}")
        print(f"Log-Datei: {Colors.BLUE}{self.log_file}{Colors.NC}")
    
    def monitor_mode(self):
        """Live-Monitor Modus mit Speed-Anzeige und Random Speed Support"""
        print(f"\n{Colors.CYAN}=== LIVE MONITOR MODUS ==={Colors.NC}")
        print(f"Script: {os.path.basename(self.selected_script)}")
        
        if self.use_random_speed:
            print(f"Speed Mode: {Colors.YELLOW}RANDOM ({self.random_speed_min}x - {self.random_speed_max}x){Colors.NC}")
            print(f"Change Mode: {Colors.YELLOW}{self.speed_change_mode}{Colors.NC}")
        else:
            print(f"Speed: {Colors.YELLOW}{self.playback_speed}x{Colors.NC}")
            
        print(f"Status: {Colors.GREEN}LÄUFT{Colors.NC}")
        print(f"\n{Colors.YELLOW}[Strg+C zum Stoppen]{Colors.NC}\n")
        
        # Speed tracking
        speed_log = []
        
        def status_thread():
            """Zeige Live-Status mit aktueller Speed"""
            while self.running:
                status = f"\r📊 Durchlauf: {self.play_count + 1}"
                
                if self.loop_mode == "count":
                    status += f" / {self.loop_count}"
                elif self.loop_mode == "infinite":
                    status += " / ∞"
                elif self.loop_mode == "duration":
                    elapsed = time.time() - self.start_time
                    remaining = max(0, self.test_duration - elapsed)
                    status += f" | ⏱️  {remaining:.0f}s"
                    
                # Aktuelle Speed anzeigen
                if self.use_random_speed:
                    status += f" | 🎲 Speed: {self.playback_speed}x"
                    if self.speed_change_mode == "gradual":
                        # Zeige Trend
                        if len(speed_log) > 1:
                            trend = "↑" if speed_log[-1] > speed_log[-2] else "↓"
                            status += f" {trend}"
                else:
                    status += f" | Speed: {self.playback_speed}x"
                    
                print(status, end='', flush=True)
                time.sleep(0.5)
        
        # Track start time für duration mode
        self.start_time = time.time()
        
        # Starte Status-Thread
        thread = threading.Thread(target=status_thread, daemon=True)
        thread.start()
        
        # Starte Loop
        self.run_loop()
    
    def speed_test_mode(self):
        """Teste verschiedene Geschwindigkeiten automatisch"""
        if not self.selected_script:
            print(f"{Colors.RED}❌ Bitte erst Recording auswählen!{Colors.NC}")
            return
        
        print(f"\n{Colors.CYAN}=== SPEED TEST MODUS ==={Colors.NC}")
        print(f"Teste verschiedene Geschwindigkeiten...")
        
        test_speeds = [0.5, 1.0, 1.5, 2.0, 3.0]
        
        for speed in test_speeds:
            self.playback_speed = speed
            print(f"\n{Colors.YELLOW}Testing {speed}x Speed...{Colors.NC}")
            
            start_time = time.time()
            if self.play_script():
                elapsed = time.time() - start_time
                print(f"{Colors.GREEN}✓ {speed}x: {elapsed:.1f}s{Colors.NC}")
            else:
                print(f"{Colors.RED}✗ {speed}x: Fehler{Colors.NC}")
            
            # Kleine Pause zwischen Tests
            if speed != test_speeds[-1]:
                time.sleep(2)
        
        # Reset auf normal
        self.playback_speed = 1.0
        print(f"\n{Colors.GREEN}Speed-Test abgeschlossen!{Colors.NC}")
    
    def run(self):
        """Hauptprogramm"""
        print(f"{Colors.MAGENTA}╔═══════════════════════════════════════╗{Colors.NC}")
        print(f"{Colors.MAGENTA}║  ENHANCED TOUCH PLAYER v2.0          ║{Colors.NC}")
        print(f"{Colors.MAGENTA}║  Mit Speed Control & Loop Support    ║{Colors.NC}")
        print(f"{Colors.MAGENTA}╚═══════════════════════════════════════╝{Colors.NC}")
        
        self.log("Enhanced Touch Player gestartet")
        
        while True:
            print(f"\n{Colors.CYAN}=== HAUPTMENÜ ==={Colors.NC}")
            
            if self.selected_script:
                print(f"✅ Script: {Colors.GREEN}{os.path.basename(self.selected_script)}{Colors.NC}")
                
                # Speed-Anzeige
                if self.use_random_speed:
                    print(f"🎲 Speed: {Colors.YELLOW}Random ({self.random_speed_min}x-{self.random_speed_max}x){Colors.NC}")
                else:
                    print(f"🎮 Speed: {Colors.GREEN}{self.playback_speed}x{Colors.NC}")
                    
                # Loop-Anzeige
                if self.loop_mode == "duration":
                    print(f"🔁 Loop: {Colors.GREEN}Duration ({self.test_duration/60:.0f} min){Colors.NC}")
                else:
                    print(f"🔁 Loop: {Colors.GREEN}{self.loop_mode} ({self.loop_count}x){Colors.NC}")
            else:
                print(f"❌ Kein Script ausgewählt")
            
            print(f"\n{Colors.YELLOW}[1]{Colors.NC} Recording auswählen")
            print(f"{Colors.YELLOW}[2]{Colors.NC} 🎮 Geschwindigkeit einstellen")
            print(f"{Colors.YELLOW}[3]{Colors.NC} 🔁 Loop konfigurieren")
            print(f"{Colors.YELLOW}[4]{Colors.NC} ▶️  Playback starten")
            print(f"{Colors.YELLOW}[5]{Colors.NC} 📊 Monitor-Modus")
            print(f"{Colors.YELLOW}[6]{Colors.NC} 🧪 Speed-Test (alle Geschwindigkeiten)")
            print(f"{Colors.YELLOW}[7]{Colors.NC} 📈 Statistiken")
            print(f"{Colors.YELLOW}[0]{Colors.NC} Beenden")
            
            choice = input(f"\n{Colors.CYAN}Auswahl: {Colors.NC}")
            
            if choice == '0':
                self.log("Enhanced Touch Player beendet")
                break
                
            elif choice == '1':
                self.select_recording()
                
            elif choice == '2':
                self.configure_speed()
                    
            elif choice == '3':
                if self.selected_script:
                    self.configure_loop()
                else:
                    print(f"{Colors.RED}❌ Bitte erst Recording auswählen!{Colors.NC}")
                    
            elif choice == '4':
                if self.selected_script:
                    self.run_loop()
                    self.show_stats()
                else:
                    print(f"{Colors.RED}❌ Bitte erst Recording auswählen!{Colors.NC}")
                    
            elif choice == '5':
                if self.selected_script:
                    self.monitor_mode()
                    self.show_stats()
                else:
                    print(f"{Colors.RED}❌ Bitte erst Recording auswählen!{Colors.NC}")
                    
            elif choice == '6':
                self.speed_test_mode()
                    
            elif choice == '7':
                if os.path.exists(self.log_file):
                    self.show_stats()
                else:
                    print(f"{Colors.YELLOW}Noch keine Statistiken vorhanden{Colors.NC}")


if __name__ == "__main__":
    try:
        player = EnhancedTouchPlayer()
        player.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.RED}Abbruch!{Colors.NC}")
    except Exception as e:
        print(f"\n{Colors.RED}Fehler: {e}{Colors.NC}")
        import traceback
        traceback.print_exc()
