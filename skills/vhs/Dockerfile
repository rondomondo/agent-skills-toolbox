# Custom VHS image with four font families baked in, plus a full dev toolset
# and zsh/oh-my-zsh for the vhs user.
#
# Includes: git, make, golang, python3 (uv), docker/docker-compose, curl/wget,
#           zsh + oh-my-zsh (philips theme), sudo, and common CLI utilities.
#
# Pinned fonts (check release pages to bump):
#   JetBrains Mono v2.304  -- https://github.com/JetBrains/JetBrainsMono/releases
#   Fira Code v6.2         -- https://github.com/tonsky/FiraCode/releases
#   Cascadia Code v2407.24 -- https://github.com/microsoft/cascadia-code/releases
#
# Auto-updated (follows /latest/ redirect):
#   JetBrains Mono Nerd Font -- https://github.com/ryanoasis/nerd-fonts/releases

# Digest-pinned so an upstream tag move cannot silently invalidate every layer; bump with:
#   docker buildx imagetools inspect ghcr.io/charmbracelet/vhs:latest | grep ^Digest
FROM ghcr.io/charmbracelet/vhs:latest@sha256:ea49a6a1c529be83153e88321892b5585964418f0b9055e8c1e0d732194234a3


COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /usr/local/bin/

ARG ZSH_IN_DOCKER_VERSION=1.2.1

USER root

# -- Apt packages + Fonts ----------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        fontconfig \
        make htop less git procps sudo curl wget unzip gnupg2 \
        zsh man-db gettext-base lsof docker-compose golang file \
        iptables ipset iproute2 dnsutils aggregate ssh-client docker.io docker-cli \
        python3-pip python3-venv libmagic1 libmagic-dev locate \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p \
        /usr/share/fonts/truetype/jetbrains-mono \
        /usr/share/fonts/truetype/jetbrains-mono-nerd \
        /usr/share/fonts/truetype/fira-code \
        /usr/share/fonts/truetype/cascadia-code \
    && wget -q -O /tmp/jbm.zip \
        "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip" \
    && unzip -q /tmp/jbm.zip -d /tmp/jbm \
    && find /tmp/jbm -name "*.ttf" -path "*ttf*" -exec cp {} /usr/share/fonts/truetype/jetbrains-mono/ \; \
    && wget -q -O /tmp/jbm-nerd.zip \
        "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip" \
    && unzip -q /tmp/jbm-nerd.zip -d /tmp/jbm-nerd \
    && find /tmp/jbm-nerd -name "*NerdFontMono*.ttf" -exec cp {} /usr/share/fonts/truetype/jetbrains-mono-nerd/ \; \
    && wget -q -O /tmp/fira.zip \
        "https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip" \
    && unzip -q /tmp/fira.zip -d /tmp/fira \
    && find /tmp/fira -name "*.ttf" -exec cp {} /usr/share/fonts/truetype/fira-code/ \; \
    && wget -q -O /tmp/cascadia.zip \
        "https://github.com/microsoft/cascadia-code/archive/refs/tags/v2407.24.zip" \
    && unzip -q /tmp/cascadia.zip -d /tmp/cascadia \
    && find /tmp/cascadia -name "*.ttf" -exec cp {} /usr/share/fonts/truetype/cascadia-code/ \; \
    && fc-cache -f \
    && rm -rf /tmp/jbm.zip /tmp/jbm /tmp/jbm-nerd.zip /tmp/jbm-nerd \
              /tmp/fira.zip /tmp/fira /tmp/cascadia.zip /tmp/cascadia

# -- vhs user ----------------------------------------------------------------
# The base image may already have a vhs user/group; delete them before
# recreating so -m reliably creates /home/vhs.
RUN userdel  -r vhs 2>/dev/null || true && \
    groupdel    vhs 2>/dev/null || true && \
    groupadd --gid 1000 vhs && \
    useradd  --uid 1000 --gid 1000 -m -s /bin/zsh vhs && \
    echo "vhs ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/vhs && \
    chmod 0440 /etc/sudoers.d/vhs && \
    mkdir -p /commandhistory /workspace /opt && \
    touch /commandhistory/.bash_history /commandhistory/.zsh_history && \
    chown -R vhs:vhs /commandhistory /workspace /home/vhs && \
    usermod -aG docker vhs && \
    updatedb || true

# -- Zsh + Oh My Zsh (installed directly into the vhs user's home) -----------
USER vhs
RUN sh -c "$(curl -fsSL https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
      -t philips \
      -p git && \
    echo "alias ll='ls -lrta'" >> /home/vhs/.zshrc && \
    echo "alias c=clear"       >> /home/vhs/.zshrc && \
    echo "export RPROMPT=''"   >> /home/vhs/.zshrc
USER root
RUN echo "alias ll='ls -lrta'" >> /root/.bashrc && \
    echo "alias c=clear"       >> /root/.bashrc

COPY --chown=root:root entrypoint.sh /entrypoint.sh
COPY --chown=root:root install.sh   /install.sh
COPY --chown=root:root uninstall.sh /uninstall.sh
COPY --chown=root:root vhs-rec      /usr/local/bin/vhs-rec
COPY --chown=root:root vhs-demo.py  /usr/local/bin/vhs-demo
RUN chmod +x /entrypoint.sh /install.sh /uninstall.sh /usr/local/bin/vhs-rec /usr/local/bin/vhs-demo

# Bake the image version into the wrapper so installed copies default to this tag.
ARG VHS_REC_VERSION
RUN if [ -n "$VHS_REC_VERSION" ]; then \
      sed "s|rondomondo/vhs-rec:latest|rondomondo/vhs-rec:$VHS_REC_VERSION|g" /usr/local/bin/vhs-rec > /tmp/wrapper.pinned \
      && cat /tmp/wrapper.pinned > /usr/local/bin/vhs-rec && rm -f /tmp/wrapper.pinned; \
    fi

USER vhs

# vhs record defaults --shell to "." unless SHELL is set.
ENV SHELL=/bin/zsh

ENTRYPOINT ["/entrypoint.sh"]
