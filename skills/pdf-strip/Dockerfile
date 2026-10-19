# Digest-pinned so an upstream tag move cannot silently invalidate every layer; bump with:
#   docker buildx imagetools inspect python:3.12-slim | grep ^Digest
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1

RUN pip install --no-cache-dir pikepdf

COPY strip.py /usr/local/bin/strip.py
RUN chmod +x /usr/local/bin/strip.py

COPY --chown=root:root entrypoint.sh /entrypoint.sh
COPY --chown=root:root install.sh    /install.sh
COPY --chown=root:root uninstall.sh /uninstall.sh
COPY --chown=root:root pdf-strip     /usr/local/bin/pdf-strip
RUN chmod +x /entrypoint.sh /install.sh /uninstall.sh /usr/local/bin/pdf-strip

# Bake the image version into the wrapper so installed copies default to this tag.
ARG PDF_STRIP_VERSION
RUN if [ -n "$PDF_STRIP_VERSION" ]; then \
      sed "s|rondomondo/pdf-strip:latest|rondomondo/pdf-strip:$PDF_STRIP_VERSION|g" /usr/local/bin/pdf-strip > /tmp/wrapper.pinned \
      && cat /tmp/wrapper.pinned > /usr/local/bin/pdf-strip && rm -f /tmp/wrapper.pinned; \
    fi

WORKDIR /data
ENTRYPOINT ["/entrypoint.sh"]
