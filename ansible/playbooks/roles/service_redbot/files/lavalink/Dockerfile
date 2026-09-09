FROM eclipse-temurin:17-jre-jammy

WORKDIR /opt/Lavalink

# Must match JAR_VERSION in redbot/cogs/audio/managed_node/version_pins.py - Red's
# bundled client only speaks the wire protocol of this specific Lavalink build.
ADD https://github.com/Cog-Creators/Lavalink-Jars/releases/download/3.7.13+red.5/Lavalink.jar /opt/Lavalink/Lavalink.jar
RUN chmod 644 /opt/Lavalink/Lavalink.jar

ENTRYPOINT ["java", "-jar", "Lavalink.jar"]
