#!/usr/bin/env bash
# Von niri per spawn-at-startup gestartet (config.kdl, erzeugt von setup.sh).
#
#   DYNDESKTOP_KIOSK=1            python -m tisch in Endlosschleife (systemd-Unit)
#   DYNDESKTOP_START=<modul>      einmal python -m <modul>, z. B. inbetrieb (Testmodus)
#   DYNDESKTOP_X11=1              über Xwayland statt nativ Wayland (Fallback)
#   sonst                         nichts
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" || exit 1

if [[ "${DYNDESKTOP_X11:-}" == 1 ]]; then
    unset SDL_VIDEODRIVER
else
    export SDL_VIDEODRIVER=wayland
fi

PY=.venv/bin/python

if [[ "${DYNDESKTOP_KIOSK:-}" == 1 ]]; then
    while true; do
        "$PY" -m tisch
        echo "kiosk.sh: tisch beendet (Exit $?), Neustart in 2 s" >&2
        sleep 2
    done
elif [[ -n "${DYNDESKTOP_START:-}" ]]; then
    if [[ ! "$DYNDESKTOP_START" =~ ^[a-z_][a-z0-9_.]*$ ]]; then
        echo "kiosk.sh: ungültiges Modul '$DYNDESKTOP_START'" >&2
        exit 2
    fi
    exec "$PY" -m "$DYNDESKTOP_START"
fi
