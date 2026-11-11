# The PC as a UPnP AV renderer: Rygel's MPRIS plugin in front of an MPRIS2 player.
# Debian testing from a pinned image (build.sh sets it); apt over https only. D-Bus needs a passwd entry for the uid that runs it.
FROM debian:testing
RUN --mount=type=bind,source=https-only-apt.sh,target=/run/https-only-apt.sh \
    --mount=type=bind,source=/etc/ssl/certs/ca-certificates.crt,target=/run/host-ca.crt \
    sh /run/https-only-apt.sh && apt-get update -qq \
 && DEBIAN_FRONTEND=noninteractive apt-get -y -qq --no-install-recommends install \
      rygel mpv mpv-mpris vlc-bin vlc-plugin-base dbus-daemon dbus-bin libglib2.0-bin python3 \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --uid 1000 --create-home pc
COPY pc-renderer.sh pc-probe.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/pc-renderer.sh"]
