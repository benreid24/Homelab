FROM ubuntu:22.04

ARG SEAFCLI_APPIMAGE=https://sos-ch-dk-2.exo.io/seafile-downloads/Seafile-cli-x86_64-9.0.15.AppImage

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
        ca-certificates \
        curl \
        fuse \
        libfuse2 \
        python3 \
        tini \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/seafile

# Download seaf-cli AppImage
RUN curl -L -o seaf-cli.AppImage \
    ${SEAFCLI_APPIMAGE} && \
    chmod +x seaf-cli.AppImage && \
    mv seaf-cli.AppImage /usr/local/bin/seaf-cli

# Create directories for config and data
RUN mkdir -p \
    /config \
    /data

COPY entrypoint.sh /entrypoint.sh
COPY sync_libraries.py /sync_libraries.py
RUN chmod +x /entrypoint.sh

# Default config location (maps cleanly to volume)
ENV SEAFILE_CONFIG_DIR=/config

ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
