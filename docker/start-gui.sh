#!/bin/sh
# Uruchamia ekran wirtualny z serwerem VNC, noVNC, a na końcu program.
set -eu

export DISPLAY=:99
SCREEN_SOCKET=/tmp/.X11-unix/X99

rm -f /tmp/.X99-lock "$SCREEN_SOCKET"
# Xvnc pozwala przeglądarce zmieniać rozmiar ekranu, więc okno wypełnia całą kartę.
# Bez hasła, ponieważ serwer VNC przyjmuje połączenia tylko z wnętrza kontenera.
Xvnc "$DISPLAY" -geometry 1280x800 -depth 24 -dpi 96 -rfbport 5900 -localhost \
    -SecurityTypes None -AcceptSetDesktopSize=1 &

until [ -S "$SCREEN_SOCKET" ]; do
    sleep 0.1
done

openbox --config-file /etc/openbox-app.xml &
websockify --web=/usr/share/novnc 6080 localhost:5900 &

echo "Program działa: otwórz http://localhost:6080"
exec python -m rle_compressor
