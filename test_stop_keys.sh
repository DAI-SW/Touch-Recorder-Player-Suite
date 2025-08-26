#!/bin/bash
# test_stop_keys.sh - Teste verschiedene Stop-Tasten

echo "=== STOP-KEY TESTER ==="
echo "Teste verschiedene Tasten-Kombinationen"
echo ""

# Finde Keyboard Device
KB_ID=$(xinput list | grep -i keyboard | grep -v "Virtual" | grep -oP 'id=\K\d+' | head -1)
echo "Keyboard Device ID: $KB_ID"
echo ""

test_key() {
    local key_name="$1"
    local key_code="$2"
    
    echo -n "Teste $key_name (Taste jetzt drücken)... "
    
    # 3 Sekunden testen
    local detected=false
    for i in {1..30}; do
        if xinput query-state $KB_ID 2>/dev/null | grep -q "key\[$key_code\]=down"; then
            echo -e "\033[0;32m✓ FUNKTIONIERT!\033[0m"
            detected=true
            break
        fi
        sleep 0.1
    done
    
    [ "$detected" = false ] && echo -e "\033[0;31m✗ Nicht erkannt\033[0m"
}

echo "Drücken Sie die jeweilige Taste wenn aufgefordert:"
echo ""

# Teste verschiedene Tasten
test_key "Rechte Strg" "105"
test_key "Rechte Alt" "108"
test_key "Linke Windows/Super" "133"
test_key "Rechte Windows/Super" "134"
test_key "Menu/Kontext" "135"
test_key "Pause/Break" "127"
test_key "Print Screen" "107"
test_key "Caps Lock" "66"
test_key "Num Lock" "77"
test_key "F8" "74"
test_key "F9" "75"
test_key "F10" "76"
test_key "F11" "95"
test_key "F12" "96"

echo ""
echo "Alternative: Maus-Gesten testen"
echo "Klicken Sie BEIDE Maustasten gleichzeitig:"

timeout 3 xinput test-xi2 --root 2>/dev/null | grep -E "button.*[13]" &
wait

echo ""
echo "Fertig! Verwenden Sie die Taste die funktioniert hat."