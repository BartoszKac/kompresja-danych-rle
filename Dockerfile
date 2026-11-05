# Pakiety instalujemy przed kopiowaniem kodu, dzięki czemu zmiana w kodzie nie powoduje
# ponownego pobierania pakietów i obraz buduje się w kilka sekund.

FROM python:3.13-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app RLE_DATA_DIR=/data
RUN useradd --create-home --uid 1000 app
WORKDIR /app

# Testy i benchmark: sam Python, bez zależności zewnętrznych.
FROM base AS runtime
COPY rle_compressor ./rle_compressor
COPY tests ./tests
USER app

# Generator plików testowych: dokłada ffmpeg.
FROM base AS samples
RUN apt-get update \
    && apt-get install --yes --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
COPY rle_compressor ./rle_compressor
COPY scripts ./scripts
USER app
CMD ["python", "scripts/generate_samples.py"]

# Program z GUI: wirtualny ekran X11 udostępniony w przeglądarce przez noVNC.
FROM base AS gui
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        fonts-dejavu-core fonts-inter fonts-noto-color-emoji libtk8.6 novnc openbox \
        tigervnc-standalone-server websockify \
    && rm -rf /var/lib/apt/lists/* \
    && install --directory --mode=1777 /tmp/.X11-unix
# Także vnc.html, aby żaden adres nie otwierał domyślnego panelu noVNC.
COPY docker/novnc-index.html /usr/share/novnc/index.html
COPY docker/novnc-index.html /usr/share/novnc/vnc.html
COPY docker/openbox-rc.xml /etc/openbox-app.xml
COPY --chmod=755 docker/start-gui.sh /usr/local/bin/start-gui
COPY rle_compressor ./rle_compressor
USER app
EXPOSE 6080
CMD ["start-gui"]
