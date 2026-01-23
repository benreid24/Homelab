FROM debian:bullseye

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        seafile-cli \
        ca-certificates \
        fuse \
        libfuse2 \
        python3 \
        tini && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/seafile

RUN mkdir -p /config /data

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
