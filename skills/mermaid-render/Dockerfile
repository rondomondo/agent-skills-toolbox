ARG ALPINE_VERSION=3.24
ARG MERMAID_CLI_VERSION=12.0.0

FROM alpine:${ALPINE_VERSION} AS build
ARG MERMAID_CLI_VERSION
# Chromium comes from apk at run time; letting puppeteer fetch its own copy adds ~650MB of dead weight.
ENV PUPPETEER_SKIP_DOWNLOAD=true
RUN apk add --no-cache nodejs npm
RUN npm install --global --omit=dev --no-audit --no-fund --prefix /opt/mermaid-cli \
      @mermaid-js/mermaid-cli@${MERMAID_CLI_VERSION} \
    && find /opt/mermaid-cli -type f \( -name '*.map' -o -name '*.md' -o -name '*.ts' ! -name '*.d.ts' \) -delete \
    && rm -rf /root/.npm

FROM alpine:${ALPINE_VERSION}
ARG EXTRA_FONTS=""

# bash: entrypoint and USE_SHELL; imagemagick: jpg/gif/webp post-conversion in the host wrapper
RUN apk add --no-cache nodejs chromium font-dejavu bash imagemagick imagemagick-jpeg imagemagick-webp ${EXTRA_FONTS} \
    && adduser -D mermaidcli

COPY --from=build /opt/mermaid-cli /opt/mermaid-cli
COPY --chmod=644 puppeteer-config.json /puppeteer-config.json
COPY --chmod=755 entrypoint.sh install.sh uninstall.sh /
COPY --chmod=755 mermaid-render /usr/local/bin/mermaid-render

# Declared this late on purpose: an ARG changes the cache key of every RUN after it, so a new tag would rebuild the apk layer.
ARG MERMAID_RENDER_VERSION
# Pin the wrapper and the install/uninstall scripts to this image tag so installed copies stay in step with it.
RUN ln -s /opt/mermaid-cli/bin/mmdc /usr/local/bin/mmdc \
    && if [ -n "$MERMAID_RENDER_VERSION" ]; then \
         sed -i "s|rondomondo/mermaid-render:latest|rondomondo/mermaid-render:$MERMAID_RENDER_VERSION|g" /usr/local/bin/mermaid-render \
         && sed -i "s/IMAGE_TAG:-latest/IMAGE_TAG:-$MERMAID_RENDER_VERSION/" /install.sh /uninstall.sh; \
       fi

USER mermaidcli
WORKDIR /data
ENTRYPOINT ["/entrypoint.sh"]
