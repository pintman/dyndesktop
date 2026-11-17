#!/usr/bin/env bash
# Richtet ein frisches Debian 13 (ohne Desktop) als Touch-Tisch ein.
# Mehrfach ausführbar; meldet am Ende je Prüfpunkt OK/FEHLT.
#
#   ./setup.sh           Einrichtung, Autostart aus (Testmodus)
#   ./setup.sh --kiosk   zusätzlich Autostart: systemd → niri → python -m tisch
set -uo pipefail

NIRI_VERSION="26.04"            # Git-Tag v26.04, MSRV 1.85 = rustc in Debian 13
NIRI_MSRV="1.85"
NIRI_REPO="https://github.com/YaLTeR/niri"
UNIT="dyndesktop-kiosk"
UNIT_DATEI="/etc/systemd/system/${UNIT}.service"

PAKETE=(evtest libinput-tools python3-venv libmtdev1t64 git
        libgl1 libgl1-mesa-dri libegl1 libgles2)
NIRI_BAUPAKETE=(gcc clang cargo rustc pkg-config libudev-dev libgbm-dev
                libxkbcommon-dev libegl1-mesa-dev libwayland-dev libinput-dev
                libdbus-1-dev libsystemd-dev libseat-dev libpipewire-0.3-dev
                libpango1.0-dev libdisplay-info-dev)

PROJEKT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
KIOSK=0
for arg in "$@"; do
    case "$arg" in
        --kiosk) KIOSK=1 ;;
        -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
        *) echo "Unbekannter Schalter: $arg" >&2; exit 2 ;;
    esac
done

if [[ $EUID -eq 0 ]]; then
    echo "Bitte als normaler Benutzer starten, nicht als root bzw. mit sudo." >&2
    echo "Das Skript ruft sudo selbst auf, wo es nötig ist." >&2
    exit 1
fi

cd "$PROJEKT" || exit 1
BENUTZER="$(id -un)"

# --- Prüfpunkte -------------------------------------------------------------

NAMEN=()
STATUS=()
HINWEISE=()

punkt() {   # punkt <Name> OK|FEHLT [Hinweis]
    NAMEN+=("$1")
    STATUS+=("$2")
    HINWEISE+=("${3:-}")
    printf '>>> %-20s %s %s\n' "$1" "$2" "${3:-}"
}

titel() { printf '\n=== %s\n' "$1"; }

installiert() { dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -q "install ok installed"; }

apt_nachinstallieren() {   # installiert nur fehlende Pakete
    local fehlend=() p
    for p in "$@"; do installiert "$p" || fehlend+=("$p"); done
    if ((${#fehlend[@]})); then
        echo "Installiere: ${fehlend[*]}"
        sudo apt-get update -qq && sudo apt-get install -y "${fehlend[@]}"
    fi
}

version_ge() { [[ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" == "$2" ]]; }

# --- Pakete -------------------------------------------------------------------

titel "Pakete"
apt_nachinstallieren "${PAKETE[@]}"
fehlend=()
for p in "${PAKETE[@]}"; do installiert "$p" || fehlend+=("$p"); done
if ((${#fehlend[@]})); then punkt "Pakete" FEHLT "${fehlend[*]}"; else punkt "Pakete" OK; fi

# --- Gruppe input -------------------------------------------------------------

titel "Gruppe input"
if id -nG "$BENUTZER" | grep -qw input; then
    punkt "Gruppe input" OK
elif getent group input | cut -d: -f4 | tr ',' '\n' | grep -qx "$BENUTZER"; then
    punkt "Gruppe input" OK "neu – bitte ab- und wieder anmelden"
else
    sudo usermod -aG input "$BENUTZER"
    if getent group input | cut -d: -f4 | tr ',' '\n' | grep -qx "$BENUTZER"; then
        punkt "Gruppe input" OK "neu hinzugefügt – bitte ab- und wieder anmelden"
    else
        punkt "Gruppe input" FEHLT "usermod fehlgeschlagen"
    fi
fi

# --- niri ---------------------------------------------------------------------

niri_ok() {
    installiert niri && return 0                     # Debian-Paket, falls es eines gibt
    [[ -x /usr/local/bin/niri ]] &&
        [[ "$(/usr/local/bin/niri --version 2>/dev/null)" == "niri ${NIRI_VERSION} "* ]]
}

niri_bauen() {
    apt_nachinstallieren "${NIRI_BAUPAKETE[@]}"
    local cargo=cargo rustc_v
    rustc_v="$(rustc --version 2>/dev/null | awk '{print $2}')"
    if ! version_ge "${rustc_v:-0}" "$NIRI_MSRV"; then
        echo "rustc ${rustc_v:-fehlt} < ${NIRI_MSRV}, installiere Rust per rustup für $BENUTZER"
        if [[ ! -x "$HOME/.cargo/bin/rustup" ]]; then
            apt_nachinstallieren curl
            curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
        fi
        cargo="$HOME/.cargo/bin/cargo"
    fi
    local ziel="$HOME/.cache/dyndesktop/niri"
    mkdir -p "$ziel"
    echo "Baue niri ${NIRI_VERSION} (dauert eine Weile) ..."
    CARGO_TARGET_DIR="$ziel/target" "$cargo" install --locked --force \
        --git "$NIRI_REPO" --tag "v${NIRI_VERSION}" --root "$ziel/install" niri &&
        sudo install -m 0755 "$ziel/install/bin/niri" /usr/local/bin/niri
}

titel "Kompositor niri"
if ! niri_ok; then
    if apt-cache show niri >/dev/null 2>&1; then
        sudo apt-get install -y niri
    else
        niri_bauen
    fi
fi
if niri_ok; then
    NIRI_BIN="$(command -v niri || echo /usr/local/bin/niri)"
    punkt "Kompositor niri" OK "$("$NIRI_BIN" --version)"
else
    NIRI_BIN=""
    punkt "Kompositor niri" FEHLT "Build/Installation fehlgeschlagen, Ausgabe oben prüfen"
fi

# --- Python-Umgebung ----------------------------------------------------------

titel "Python-Umgebung"
[[ -x .venv/bin/python ]] || python3 -m venv .venv
mapfile -t ABH < <(python3 -c '
import tomllib
for d in tomllib.load(open("pyproject.toml", "rb"))["project"]["dependencies"]:
    print(d)')
.venv/bin/pip install -q --disable-pip-version-check "${ABH[@]}"
if .venv/bin/python -c "import kivy, ffpyplayer" >/dev/null 2>&1; then
    punkt "Python-Umgebung" OK "${ABH[*]}"
else
    punkt "Python-Umgebung" FEHLT "kivy/ffpyplayer nicht importierbar"
fi

# --- Touch-Gerät --------------------------------------------------------------

titel "Touch-Gerät"
PFAD="" PROVIDER="" TYP="" NAME="" WARNUNGEN=""
if ausgabe="$(python3 -m inbetrieb.geraet)"; then
    eval "$ausgabe"
    if [[ "$TYP" == single ]]; then
        echo
        echo "!!! WARNUNG: nur Single-Touch – das Gerät meldet keine Multitouch-Achsen !!!"
        echo
    fi
    punkt "Touch-Gerät" OK "$NAME, Typ $TYP, $PROVIDER, $PFAD${WARNUNGEN:+ – $WARNUNGEN}"
else
    punkt "Touch-Gerät" FEHLT "Rahmen per USB anschließen und setup.sh erneut starten"
fi

# --- Kivy-Konfiguration -------------------------------------------------------

titel "Kivy-Konfiguration"
KIVY_INI="${KIVY_HOME:-$HOME/.kivy}/config.ini"
if [[ ! -f "$KIVY_INI" ]]; then
    # Kivy legt seine Standarddatei selbst an (inkl. config_version), sonst
    # ergänzt es beim ersten Start wieder probesysfs.
    KIVY_NO_ARGS=1 .venv/bin/python -c "import kivy.config" >/dev/null 2>&1
fi
if [[ -n "$PFAD" ]] && python3 -m inbetrieb.kivyconfig input "$PFAD" "$PROVIDER" &&
        python3 -m inbetrieb.kivyconfig zeigen | grep -qF "$PROVIDER,$PFAD"; then
    punkt "Kivy-Konfiguration" OK "$KIVY_INI"
else
    punkt "Kivy-Konfiguration" FEHLT "ohne Touch-Gerät nicht möglich"
fi

# --- niri-Konfiguration -------------------------------------------------------

titel "niri-Konfiguration"
NIRI_KDL="${XDG_CONFIG_HOME:-$HOME/.config}/niri/config.kdl"
if python3 -m inbetrieb.niriconfig schreiben "$PROJEKT"; then
    if [[ -z "$NIRI_BIN" ]]; then
        punkt "niri-Konfiguration" FEHLT "geschrieben, aber ohne niri nicht prüfbar"
    elif "$NIRI_BIN" validate -c "$NIRI_KDL" >/dev/null 2>&1; then
        punkt "niri-Konfiguration" OK "$NIRI_KDL ($(python3 -m inbetrieb.niriconfig struts))"
    else
        punkt "niri-Konfiguration" FEHLT "niri validate -c $NIRI_KDL meldet Fehler"
    fi
else
    punkt "niri-Konfiguration" FEHLT "Schreiben fehlgeschlagen"
fi

# --- Autostart ----------------------------------------------------------------

titel "Autostart"
unit_text() {
    cat <<EOF
# Erzeugt von dyndesktop/setup.sh
[Unit]
Description=dyndesktop Kiosk (niri + Tisch-App)
After=systemd-user-sessions.service getty@tty1.service
Conflicts=getty@tty1.service

[Service]
User=${BENUTZER}
PAMName=login
TTYPath=/dev/tty1
TTYReset=yes
TTYVHangup=yes
StandardInput=tty
StandardOutput=journal
StandardError=journal
UtmpIdentifier=tty1
UtmpMode=user
WorkingDirectory=${PROJEKT}
Environment=DYNDESKTOP_KIOSK=1
ExecStart=${NIRI_BIN:-/usr/local/bin/niri}
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF
}
if [[ "$(cat "$UNIT_DATEI" 2>/dev/null)" != "$(unit_text)" ]]; then
    unit_text | sudo tee "$UNIT_DATEI" >/dev/null && sudo systemctl daemon-reload
fi
zustand="$(systemctl is-enabled "$UNIT" 2>/dev/null)"
if ((KIOSK)); then
    [[ "$zustand" == enabled ]] || sudo systemctl enable "$UNIT"
    zustand="$(systemctl is-enabled "$UNIT" 2>/dev/null)"
    if [[ "$zustand" == enabled ]]; then
        punkt "Autostart" OK "aktiv (Kiosk), wirksam nach Neustart"
    else
        punkt "Autostart" FEHLT "systemctl enable $UNIT fehlgeschlagen"
    fi
else
    [[ "$zustand" == enabled ]] && sudo systemctl disable "$UNIT"
    zustand="$(systemctl is-enabled "$UNIT" 2>/dev/null)"
    if [[ "$zustand" != enabled ]]; then
        punkt "Autostart" OK "aus (Testmodus: DYNDESKTOP_START=inbetrieb niri auf tty1)"
    else
        punkt "Autostart" FEHLT "systemctl disable $UNIT fehlgeschlagen"
    fi
fi

# --- Bericht ------------------------------------------------------------------

titel "Ergebnis"
fehler=0
for i in "${!NAMEN[@]}"; do
    printf '  %-6s %-20s %s\n' "${STATUS[$i]}" "${NAMEN[$i]}" "${HINWEISE[$i]}"
    [[ "${STATUS[$i]}" == OK ]] || fehler=1
done
exit "$fehler"
