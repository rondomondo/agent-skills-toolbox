# cast2gif image -- wraps ghcr.io/asciinema/agg with the cast2gif wrapper
# script and an entrypoint that handles volume-mount wiring automatically.
#
# The base image already contains the `agg` binary; we add:
#   - bash (for entrypoint and wrapper scripts)
#   - the cast2gif wrapper script at /usr/local/bin/cast2gif
#   - install.sh so `docker run ... install` drops cast2gif into the caller's CWD
#
# Usage (via wrapper):
#   cast2gif demo.cast          # derives demo.gif automatically
#   cast2gif -- --help          # passthrough to agg
#
# Usage (raw Docker):
#   docker run --rm \
#     -u "$(id -u):$(id -g)" \
#     -v "$PWD:/data" \
#     ghcr.io/rondomondo/cast2gif:latest \
#     demo.cast demo.gif

# Digest-pinned so an upstream tag move cannot silently invalidate every layer; bump with:
#   docker buildx imagetools inspect ghcr.io/asciinema/agg:latest | grep ^Digest
FROM ghcr.io/asciinema/agg:latest@sha256:84e04c21013e4fb91cbdb3eade5977c1e66685c18f0d234da78d3350bb3404b2

USER root

# -- Apt packages + Fonts ----------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        make htop less git procps sudo curl wget unzip \
        zsh lsof file iptables ipset iproute2 dnsutils aggregate locate


COPY --chown=root:root demo.cast /demo.cast
COPY --chown=root:root entrypoint.sh /entrypoint.sh
COPY --chown=root:root install.sh    /install.sh
COPY --chown=root:root uninstall.sh /uninstall.sh
COPY --chown=root:root cast2gif      /usr/local/bin/cast2gif
RUN chmod +x /entrypoint.sh /install.sh /uninstall.sh /usr/local/bin/cast2gif

# Bake the image version into the wrapper and the install/uninstall scripts so installed copies default to this tag.
ARG CAST2GIF_VERSION
RUN if [ -n "$CAST2GIF_VERSION" ]; then \
      sed "s|rondomondo/cast2gif:latest|rondomondo/cast2gif:$CAST2GIF_VERSION|g" /usr/local/bin/cast2gif > /tmp/wrapper.pinned \
      && cat /tmp/wrapper.pinned > /usr/local/bin/cast2gif && rm -f /tmp/wrapper.pinned \
      && sed -i "s/IMAGE_TAG:-latest/IMAGE_TAG:-$CAST2GIF_VERSION/" /install.sh /uninstall.sh; \
    fi

WORKDIR /data

ENTRYPOINT ["/entrypoint.sh"]
