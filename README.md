# Touch Recorder & Player Suite

Ein präzises Tool-Set zur Aufzeichnung und Wiedergabe von Touchscreen-Eingaben unter Linux. Perfekt für automatisierte Tests, Demonstrationen und wiederholbare Touch-Sequenzen.

## 📋 Übersicht

Die Suite besteht aus zwei Hauptkomponenten:

- **`smooth-touch-recorder.py`** - Zeichnet Touch-Eingaben mit Millisekunden-Genauigkeit auf
- **`touch-player.py`** - Spielt aufgezeichnete Touch-Sequenzen mit Loop-Optionen ab

## 🎯 Features

### Touch Recorder

- **Präzises Timing**: Sub-Millisekunden genaue Aufzeichnung aller Touch-Events
- **Smooth Movement Tracking**: Erfasst alle Zwischenpunkte einer Bewegung
- **Multi-Monitor Support**: Automatische Erkennung und Auswahl von Monitoren
- **Resolution Validation**: Warnt bei geänderter Bildschirmauflösung
- **Debug Mode**: Detaillierte JSON-Logs für Analyse
- **Touch-Typen**: Taps, Swipes, komplexe Drag-Gesten

### Enhanced Touch Player v2.0

- **Speed Control**: Wiedergabe von 0.1x bis 10x Geschwindigkeit
- **Random Speed Mode**: Automatische Geschwindigkeitsvariation für Robustheitstests
- **Loop-Modi**: Single, Count, Infinite, Random, Duration-basiert
- **Speed-Modi**: Fixed, Per-Loop Random, Gradual, Chaos Mode
- **Live-Monitoring**: Echtzeit-Status mit Speed-Anzeige
- **Speed-Test**: Automatischer Test verschiedener Geschwindigkeiten
- **Erweiterte Statistiken**: Speed-Verteilung, Histogramme, Durchschnittswerte
- **Recording-Management**: Umbenennen, löschen, analysieren mit Duration-Schätzung

## 🚀 Installation

### Voraussetzungen

```bash
# System-Pakete
sudo apt update
sudo apt install python3 xdotool evtest bc xrandr

# Python (3.6+)
python3 --version
```

### Setup

```bash
# Repository klonen oder Dateien kopieren
mkdir ~/touch-tools
cd ~/touch-tools

# Scripts ausführbar machen
chmod +x smooth-touch-recorder.py
chmod +x touch-player.py

# Recording-Verzeichnis erstellen
mkdir -p ~/recordings
```

## 📱 Touch Device identifizieren

Finden Sie Ihr Touch-Device:

```bash
# Liste aller Input-Devices
sudo evtest

# Typische Touch-Devices:
# - event15: WingCool TouchScreen
# - event16: Alternative Touch
# - event7:  Mouse/Touchpad
```

## 🎬 Recording erstellen

### Basis-Verwendung

```bash
sudo python3 smooth-touch-recorder.py
```

### Workflow

1. **Monitor auswählen** (Option 4)
   
   - Bei Multi-Monitor-Setup wichtig
   - Auto-Detection der verfügbaren Monitore

2. **Device testen** (Option 1)
   
   - Prüfen ob das richtige Touch-Device gewählt wurde
   - Live-Anzeige der Touch-Koordinaten

3. **Aufnahme starten** (Option 2 oder 3)
   
   - Option 2: Standard-Aufnahme
   - Option 3: Precision-Mode mit Debug-Output
   - Device-Nummer eingeben (z.B. 15)
   - Recording-Namen vergeben

4. **Touch-Eingaben durchführen**
   
   - 3 Sekunden Countdown vor Start
   - Alle Gesten werden aufgezeichnet
   - `Strg+C` zum Stoppen

### Beispiel-Session

```bash
sudo python3 smooth-touch-recorder.py

# Ausgabe:
╔══════════════════════════════════════╗
║  PRECISION TOUCH RECORDER v3.0      ║
║  Sub-millisecond timing accuracy     ║
╚══════════════════════════════════════╝

📺 Monitor Setup:
✅ eDP-1: 1920x1200 @ (0,0)

═══ HAUPTMENÜ ═══
[1] 🧪 Device testen
[2] 🎬 Standard Aufnahme
[3] 🎯 Precision Aufnahme (mit Debug)
[4] 📺 Monitor wählen
[5] 📂 Recordings anzeigen

Wahl: 2
Device Nummer: 15
Recording Name: login_sequence

🎬 AUFNAHME STARTET IN 3 SEK...
⏺️  AUFNAHME LÄUFT!

▼ TOUCH DOWN @ (500,300)
🔵 TAP: (500,300) duration=150ms
▼ TOUCH DOWN @ (100,200)
👆 DRAG: 45 points, 350px, 1200ms
^C
⏹️  AUFNAHME GESTOPPT

✅ RECORDING COMPLETE
📄 Script: /home/dai/recordings/login_sequence_20241210_143022.sh
```

## ▶️ Wiedergabe

### Einfache Wiedergabe

```bash
# Direkt das generierte Script ausführen
bash ~/recordings/login_sequence_20241210_143022.sh
```

### Mit Enhanced Touch Player

```bash
python3 enhanced-touch-player.py
```

### Player Features

1. **Recording auswählen**
   
   - Zeigt alle verfügbaren Recordings
   - Mit Metadaten (Datum, Events, geschätzte Dauer)
   - Automatische Duration-Berechnung

2. **Speed Control (NEU!)**
   
   - Vordefinierte Geschwindigkeiten (0.25x - 3.0x)
   - Custom Speed (0.1x - 10.0x)
   - Automatische Anpassung aller Timings
   - Speed-Test Modus für alle Geschwindigkeiten

3. **Loop konfigurieren**
   
   - **Single**: Einmal abspielen
   - **Count**: X-mal wiederholen
   - **Infinite**: Endlosschleife
   - **Random Count**: 3-10 zufällige Wiederholungen
   - **Duration**: Zeit-basiert (z.B. 10 Minuten Test)
   - **Random Speed**: Verschiedene Geschwindigkeiten pro Durchlauf

4. **Random Speed Modi (NEU!)**
   
   - **Per-Loop**: Neue Geschwindigkeit für jeden Durchlauf
   - **Gradual**: Progressive Beschleunigung
   - **Chaos**: Extreme zufällige Variationen
   - Konfigurierbare Speed-Ranges

5. **Monitor-Modus**
   
   - Live-Status-Anzeige mit aktueller Speed
   - Durchlauf-Zähler
   - Zeit-Tracking bei Duration-Tests
   - Speed-Trend Anzeige

### Beispiel Loop-Setup mit Random Speed

```bash
python3 enhanced-touch-player.py

╔═══════════════════════════════════════╗
║  ENHANCED TOUCH PLAYER v2.0          ║
║  Mit Speed Control & Loop Support    ║
╚═══════════════════════════════════════╝

# Menü:
[1] Recording auswählen
[2] 🎮 Geschwindigkeit einstellen
[3] 🔁 Loop konfigurieren

# Loop-Konfiguration:
[1] Einmal abspielen
[2] X-mal wiederholen
[3] Unendlich wiederholen
[4] Zufällige Anzahl (3-10)
[5] ⏱️  Dauer-Test (Zeit-basiert)
[6] 🎲 Random Speed Mode

Loop-Modus: 6

# Random Speed Konfiguration:
[1] Standard Random (0.5x - 2.0x)
[2] Slow Motion Focus (0.25x - 1.0x)
[3] Speed Test (1.0x - 3.0x)
[4] Extreme Range (0.1x - 5.0x)

Range: 1
Loops: 25

# Während der Ausführung:
🎲 Durchlauf #1 mit 0.75x Speed
🎲 Durchlauf #2 mit 1.83x Speed
🎲 Durchlauf #3 mit 0.52x Speed

# Nach Abschluss - Statistiken:
📊 RANDOM SPEED STATISTIK:
  • Durchschnitt: 1.24x
  • Min/Max: 0.5x / 1.98x
  • Variationen: 25

Speed-Verteilung:
  0.50x [ 2] ██████
  1.00x [ 4] ████████████
  1.50x [ 5] ███████████████
  2.00x [ 3] █████████
```

## 📁 Dateistruktur

```
~/recordings/
├── touch_20241210_143022.sh       # Generierte Bash-Scripts
├── touch_20241210_143022_debug.json # Debug-Daten (optional)
├── playback_20241210_150000.log   # Player-Logs
└── ...
```

## 🔧 Generierte Script-Struktur

Die aufgezeichneten Scripts enthalten:

- Header mit Recording-Konfiguration
- Resolution-Validation
- Präzise Touch-Funktionen
- Zeitgesteuerte Event-Sequenz

```bash
#!/bin/bash
# RECORDED CONFIGURATION:
# Monitor: eDP-1
# Resolution: 1920x1200
# Position: (0,0)

verify_resolution() { ... }
do_tap() { ... }
do_timed_drag() { ... }

# Events:
sleep_ms 1500
do_tap 500 300 150
sleep_ms 800
do_timed_drag '[[100,200,0],[150,250,50],[200,300,100]]'
```

## ⚠️ Troubleshooting

### Permission Denied

```bash
# Recorder benötigt sudo für evtest
sudo python3 smooth-touch-recorder.py
```

### Touch-Device nicht gefunden

```bash
# Alle Devices listen
sudo evtest
# Device-Nummer notieren und im Recorder verwenden
```

### Resolution geändert

```bash
# Bei Warnung:
⚠️  WARNUNG: Auflösung hat sich geändert!
   Aufnahme: 1920x1200
   Aktuell:  1280x800

# Entweder:
# - Auflösung zurücksetzen
# - Neue Aufnahme erstellen
# - Mit 'j' trotzdem fortfahren (kann ungenau sein)
```

### xdotool nicht gefunden

```bash
sudo apt install xdotool
```

## 🎯 Use Cases

### Mit Speed Control

1. **Debugging & Analyse (0.25x - 0.5x)**
   
   - Frame-by-frame Analyse von UI-Problemen
   - Präzise Beobachtung von Animationen
   - Touch-Event Timing debuggen

2. **Automatisierte UI-Tests (1.0x - 2.0x)**
   
   - Regressionstests in normaler Geschwindigkeit
   - Schnelle Smoke-Tests mit 2x Speed
   - Feature-Verifikation

3. **Stress & Performance Tests (2.0x - 5.0x)**
   
   - Belastungstests mit hohen Eingabegeschwindigkeiten
   - Race-Condition Detection
   - Performance-Schwellwerte finden

4. **Robustheitstests (Random Speed)**
   
   - Simuliert verschiedene Benutzertypen
   - Findet timing-abhängige Bugs
   - Testet UI-Reaktionszeiten

5. **Langzeit-Stabilitätstests (Duration Mode)**
   
   - 10 Minuten bis mehrere Stunden Tests
   - Memory-Leak Detection
   - Kombinierbar mit Random Speed

### Random Speed Modi im Detail

#### Standard Random (0.5x - 2.0x)

- Simuliert realistische Benutzervariationen
- Von langsamen bis schnellen Benutzern
- Ideal für allgemeine Robustheitstests

#### Slow Motion Focus (0.25x - 1.0x)

- Detaillierte Analyse jeder Aktion
- Perfekt für visuelle Verifikation
- UI-Animation Debugging

#### Speed Test (1.0x - 3.0x)

- Performance-Orientierte Tests
- Findet Engpässe bei schnellen Eingaben
- Testet Responsiveness

#### Chaos Mode (0.1x - 5.0x)

- Extreme Variationen für Stress-Tests
- 10% Chance für Extremwerte
- Variable Pausen zwischen Aktionen
- Findet unerwartete Edge-Cases

#### Gradual Mode

- Progressive Beschleunigung
- Startet langsam, wird kontinuierlich schneller
- Bei Endlos-Loops: Sinus-Wellen-Pattern
- Ideal für Performance-Grenzwert-Tests

## 📊 Technische Details

- **Timing-Genauigkeit**: ±1ms
- **Speed-Range**: 0.1x bis 10.0x einstellbar
- **Max. Punkte pro Geste**: 500 (konfigurierbar)
- **Bewegungs-Threshold**: 2px (konfigurierbar)
- **Unterstützte Gesten**: Tap, Swipe, Drag, Multi-Touch (teilweise)
- **Output-Format**: Bash-Script mit xdotool-Commands
- **Speed-Anpassung**: Automatische Skalierung aller Timings (sleep_ms, tap duration, drag timestamps)

## 🛠️ Erweiterte Konfiguration

### Recording-Parameter anpassen

Im `smooth-touch-recorder.py`:

```python
# Precision tracking settings
self.min_movement_threshold = 2  # Minimale Bewegung in Pixel
self.max_points_per_gesture = 500  # Max Punkte pro Geste

# Touch-Controller Bereiche (device-spezifisch)
self.touch_max_x = 16382
self.touch_max_y = 9598
```

### Player-Optionen

Im `touch-player.py`:

```python
# Standard-Verzeichnisse
self.recordings_dir = "/home/dai/recordings"

# Loop-Einstellungen
self.loop_mode = "single"  # single, count, infinite, random
self.pause_duration = 0  # Sekunden zwischen Loops
```

## 🔍 Debug & Analyse

### Recording analysieren

```bash
# Mit Player
python3 touch-player.py
# Option 9: Recording Details

# Manuell
cat ~/recordings/touch_*.sh | grep -c "do_tap"  # Anzahl Taps
cat ~/recordings/touch_*.sh | grep -c "do_drag"  # Anzahl Drags
```

### Debug-Modus nutzen

```bash
# Recording mit Debug-Output
sudo python3 smooth-touch-recorder.py
# Option 3: Precision Aufnahme

# Debug-JSON analysieren
cat ~/recordings/*_debug.json | python3 -m json.tool
```

### Live-Device-Test

```bash
# Touch-Events live beobachten
sudo evtest /dev/input/event15

# Oder im Recorder
sudo python3 smooth-touch-recorder.py
# Option 1: Device testen
```

## 📈 Performance-Tipps

### Geschwindigkeits-Empfehlungen

1. **Debugging/Analyse**: 0.25x - 0.5x
   
   - Detaillierte Beobachtung jeder Aktion
   - Problem-Identifikation

2. **Standard-Tests**: 0.75x - 1.5x  
   
   - Normale Benutzergeschwindigkeit
   - Funktionale Verifikation

3. **Quick-Tests**: 1.5x - 2.5x
   
   - Zeitsparend für bekannte Flows
   - Smoke-Tests in CI/CD

4. **Stress-Tests**: 2.0x - 5.0x
   
   - Performance-Limits testen
   - Race-Conditions aufdecken

### Optimierung für lange Recordings

- **Standard-Modus** statt Debug für lange Sequenzen
- **Pausen zwischen Loops** bei intensiven Tests
- **Speed-Verteilung** nutzen für realistische Tests
- **Duration-Mode** für zeitbasierte statt anzahlbasierte Tests

### Best Practices für Random Speed

1. **Erste Tests**: Standard Random (0.5x-2.0x) mit 10-25 Loops
2. **Bug-Hunting**: Chaos Mode mit Duration-Test (z.B. 5 Minuten)
3. **CI/CD Integration**: Gradual Mode mit fester Loop-Anzahl
4. **Nightly Tests**: Duration Mode mit Random Speed über 30+ Minuten

### CPU-Last Management

- Bei hohen Geschwindigkeiten (>3x): Kürzere Test-Sessions
- Random Speed verteilt Last besser als konstant hohe Speed
- Monitor-Mode zeigt Live-Performance

## 🔒 Sicherheitshinweise

- Recordings enthalten exakte Bewegungsmuster - nicht für sensitive Eingaben verwenden
- Scripts mit `sudo` nur von vertrauenswürdigen Quellen ausführen
- Recordings sind Klartext-Bash-Scripts - können eingesehen und modifiziert werden

## 📝 Bekannte Einschränkungen

- Multi-Touch wird nur teilweise unterstützt
- Pressure-Sensitivity wird nicht aufgezeichnet
- Gesten-Rotation wird nicht erkannt
- Maximale Aufzeichnungsdauer abhängig vom verfügbaren RAM

## 🤝 Beitragen

Verbesserungsvorschläge und Bug-Reports sind willkommen! 

### Mögliche Erweiterungen

- GUI-Interface für einfachere Bedienung
- Multi-Touch Support verbessern
- Cloud-Sync für Recordings
- Export in andere Formate (Selenium, Appium)
- Machine Learning für intelligente Speed-Anpassung
- Windows/macOS Portierung
- Integration in Test-Frameworks

## 📄 Lizenz

MIT License - Frei verwendbar für private und kommerzielle Zwecke.

## 🙏 Credits

Entwickelt mit Python 3 und Linux-Tools:

- `evtest` für Device-Input
- `xdotool` für Maus-Simulation  
- `xrandr` für Monitor-Detection
- `bc` für präzise Berechnungen

## 📚 Changelog

### v3.0 - Touch Recorder

- Precision timing mit Sub-Millisekunden Genauigkeit
- Smooth movement tracking
- Resolution validation
- Multi-monitor support

### v2.0 - Enhanced Touch Player

- Speed Control (0.1x - 10x)
- Random Speed Modi
- Duration-basierte Tests
- Erweiterte Statistiken
- Speed-Test Modus

### v1.0 - Initial Release

- Basic recording und playback
- Loop support
- Recording management

---

**Aktuelle Version**: Recorder 3.0 | Player 2.0  
**Autor**: DAI  
**Stand**: August 2025
