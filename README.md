# agent-skills-toolbox

**Skills for AI coding agents.**

A collection of skills that give AI coding agents structured workflows and tool integrations -- packaged for use with Claude Code.

---

## Contents

| Skill | What it does |
|-------|-------------|
| [inspect-sandbox](#inspect-sandbox) | Performs automated linux container or sandbox environment inspection that parses system state into a self-contained HTML viewer with collapsible sections, category filters, and rendered Mermaid diagrams. When running inside an AI sandbox (like Claude Web UI etc), the full output is packaged into a downloadable zip that the user can run locally with a single command. A multi page landscape A4 PDF of all text sections is also rendered via Playwright and presented inline in the chat client as well as in the download bundle. |
| [mermaid-render](#mermaid-render) | Renders Mermaid diagrams from a Markdown file, directory, or URL to SVG, PNG, PDF, JPG, GIF, or WebP |
| [project-scaffold](#project-scaffold) | Scaffolds a production-ready Python project: devcontainer, VS Code settings, Makefile, pyproject.toml, pytest, commit-msg hook, and .gitignore |
| [qr](#qr) | Generates styled QR codes via Docker or Node fallback; accepts natural-language colour names, dot styles, and logo embedding |
| [sanitise-ascii](#sanitise-ascii) | Detects and auto-fixes non-ASCII characters (smart quotes, en/em dashes, curly apostrophes, non-breaking spaces, BOMs, and more) before they cause silent failures in pipelines, CI, or tools that expect plain ASCII. Flags anything it cannot fix for manual review |
| [find4](#find4) | Generates Find4 (Connections-style) game JSON from any text source: URL, local file, or stdin |

---

## Quick Start

**Install a skill to your user profile (global):**

```bash
make skill-install name=inspect-sandbox
```

**Install to the current project only:**

```bash
make skill-install-local name=inspect-sandbox
```

**Install all skills:**

```bash
make install-all-skills
```

---

## Skills

### inspect-sandbox

Automated environment inspection that parses system state into a self-contained HTML viewer with collapsible sections, category filters, and rendered Mermaid diagrams. When running inside the Claude sandbox, the full output is packaged into a downloadable zip that the user can run locally with a single command. A multi-page landscape A4 PDF of all text sections is also rendered via Playwright and presented inline in the chat client.

---

> **Try it now** -- just say one of these to your agent:
> - *Inspect this sandbox and show me what's available*
> - *What tools, runtimes, and network access do I have in here?*
> - *Run /inspect-sandbox and give me a full environment report*

---

## Why inspect the sandbox?

When you build skills or agents that run inside an AI sandbox -- whether Claude's web UI, a CI runner, or a cloud container -- you are working inside an environment you did not configure and cannot easily observe. That gap can cause real problems:

**The slow-burn discover-as-you-fail loop.** Skills break at runtime because a tool isn't installed, a capability is blocked, the network is restricted, or a write path doesn't exist. You fix one thing, redeploy, and hit the next issue. Rince and repeat. Each iteration costs minutes or hours. `inspect-sandbox` collapses this loop into a single upfront inspection and read.

**Things you didn't know you needed to know.** You only discover that `mmdc` needs a real display server, that `pip` is replaced by `uv`, that `/tmp` is a `tmpfs` with a 512 MB cap, or that outbound DNS is filtered -- when your skill fails silently at silly o'clock. The inspection surfaces all of it before you hopefully get too deep in despair.

**Concrete constraints, not assumptions.** How much disk can I write? Which Linux capabilities do I have? Is `ptrace` blocked? Is there a proxy? Does `sudo` work? Is seccomp enabled? These answers are not typically documented in detail if at all -- they depend on how the specific sandbox was configured. The generated report here gives you the actual reality.

**What the report covers:**

| Section | What you learn |
|---|---|
| Filesystem & mounts | Where you can write, overlay/rclone mounts, tmpfs limits, symlink layout |
| Security context | uid/gid, Linux capabilities (decoded), seccomp mode, AppArmor/SELinux, namespace isolation |
| Network | Interfaces, routing, DNS, iptables rules, proxy variables, custom CA certs |
| Processes | Process tree, CPU/RAM, open file descriptors, listening ports |
| Runtime environment | Installed languages and versions, package managers, OS/kernel/CPU info |
| Skill tool availability | Presence of runtimes, PDF tools, OCR, media tools, browsers, shell utilities |

See [skills/inspect-sandbox/README.md](skills/inspect-sandbox/README.md) for full documentation.

---

### mermaid-render

Renders Mermaid diagrams from Markdown files to SVG, PNG, PDF, JPG, GIF, or WebP. Supports a named colour palette (16 classDef colours) for consistent diagram styling.

**Triggers when:** you type `/mermaid-render`, or ask to render, generate, export, or convert Mermaid diagrams or charts from a `.md` file, local directory, or URL.

**Input sources:**

| Type | Example |
|------|---------|
| Single file | `examples/example1.md` |
| Multiple files | `examples/example1.md examples/example2.md` |
| Local directory | `./docs/` |
| URL (single file) | `https://example.com/diagram.md` |
| URL (GitHub directory) | `https://github.com/user/repo/tree/main/docs` |

**Backends:**

| Environment | Backend |
|-------------|---------|
| Outside sandbox | `mermaid-render` script (Docker-backed via `ghcr.io/rondomondo/mermaid-render`) |
| Inside sandbox | `mmdc` with bundled Chromium; auto-detects Chromium path; uses split mode on single-vCPU sandboxes with 3+ diagrams |

**Output:**

- Numbered image files alongside the source (e.g. `example1.md-1.svg`)
- A companion `.md` with `![diagram](./image-N.ext)` references replacing fenced blocks
- The original file is never modified

**Formats:** `svg` (default), `png`, `pdf`, `jpg`, `gif`, `webp`

See [skills/mermaid-render/SKILL.md](skills/mermaid-render/SKILL.md) for the full workflow.

---

### project-scaffold

Scaffolds a complete, ready-to-open Python project in one command: devcontainer config (Dockerfile-based or base image), VS Code settings and extensions, a full Makefile, pyproject.toml, pytest setup, commit-msg hook, and optional GitHub SSH wiring.

**Triggers when:** you ask Claude to scaffold, create, or initialise a project, or type phrases like "new repo", "bootstrap a project", "clone this scaffold", "lite scaffold".

**Two modes:**

- **Full mode** - gathers requirements (project name, devcontainer style, SSH key, extra extensions) then generates the full project tree
- **Lite mode** - clones an existing scaffolded project to a new name, substitutes the project name throughout, and resets git history

**Output:**

A ready-to-open project folder under `~/Code/<project-name>/` (or a user-specified root), with all files wired together and consistent from the first commit.

See [skills/project-scaffold/SKILL.md](skills/project-scaffold/SKILL.md) for the full workflow.

---

### qr

Generates styled QR codes via the `rondomondo/qr-cli` Docker image, with automatic fallback to a Python/Node implementation when Docker is unavailable.

**Triggers when:** you type `/qr`, or ask to generate, create, render, or style a QR code.

**Features:**

- Natural-language colour names resolved via `colourmapper`
- Dot and corner style keywords: `rounded`, `circles`, `classy`, `extra-rounded`
- Logo embedding
- Output formats: SVG, PNG, JPG, WEBP
- Always saves to disk and reports the path

**Example invocations:**

```
/qr https://example.com blue on white rounded
/qr https://example.com with logo ./logo.png save to ./out.png
```

See [skills/qr/SKILL.md](skills/qr/SKILL.md) for the full workflow.

---

### sanitise-ascii

Detects and auto-fixes non-ASCII characters (smart quotes, en/em dashes, curly apostrophes, non-breaking spaces, BOMs, and more) before they cause silent failures in pipelines, CI, or tools that expect plain ASCII. Flags anything it cannot fix for manual review.

**Triggers when:** you type `/sanitise-ascii`, or ask to sanitise/sanitize, check for non-ASCII, clean before push, strip unicode, or prepare files for Remote Agent use or GitHub.

**Two deliverables:**

| File | Purpose |
|------|---------|
| `sanitise-ascii.py` | Standalone script -- run manually or from CI |
| `pre-commit-sanitise-ascii` | Git hook -- checks staged files automatically on every commit |

**Usage:**

```bash
sanitise-ascii README.md              # check a single file (no writes)
sanitise-ascii --fix README.md        # auto-fix in place
sanitise-ascii --fix --dir ./skills   # fix all supported files under a directory
```

**Safe by default** -- check mode never writes. Pass `--fix` to allow modifications.

See [skills/sanitise-ascii/README.md](skills/sanitise-ascii/README.md) for the full reference.

---

### find4

Generates a fully post-processed, drag-and-drop-ready JSON file for the [Find4 game](https://find4.org) -- a Connections-style word-grouping game where players find groups of four words sharing a hidden theme.

**Triggers when:** you type `/find4`, ask to create a Find4 game, generate game content from a document or webpage, or mention "connections game", "word groups", or "game JSON".

**Input sources:**

- A URL (webpage content is fetched and parsed)
- A local file (text, Markdown, PDF)
- Piped stdin content

**Output:**

- A validated, ID-assigned JSON file ready for the Find4 library
- Colour-fixed and metadata-finalised via the skill's own post-processing scripts

<br>

**Examples:**

| Input | Prompt | Result |
|-------|--------|--------|
| Pasting a URL | ![Prompt: /find4 quiz me on 'brendangregg.com/ebpf.html'][img-brendan-gregg] | <details><summary>Game Board</summary>[![bpftrace One-Liners & Internals game][img-bpftrace]][link-bpftrace] </details>|
| Typing text | ![Prompt: /find4 generate some games from this PDF][img-highschoolers-prompt] | <details><summary>Game Board</summary>[![World Geography for High Schoolers game][img-world-geo]][link-world-geo] </details> |
| Pasting a document | ![Prompt: /find4 generate some games from this pdf][img-pdf-prompt] | <details><summary>Game Board</summary> [![Kubernetes Operators: Core Concepts][img-k8s-operators]][link-k8s-operators] </details>|

---

## Makefile Reference

```bash
# Install a skill
make skill-install name=inspect-sandbox        # global (~/.claude/skills/)
make skill-install-local name=inspect-sandbox  # project-local (.claude/skills/)

# Install all skills
make install-all-skills

# Run a skill's own Makefile targets
make skill name=inspect-sandbox target=help
make skill name=inspect-sandbox target=inspect

# Package a skill as a zip
make skill-zip name=inspect-sandbox

# Regenerate plugin.json and marketplace.json
make plugin-generate

# Show current plugin config
make plugin-show
```

---

## Contributing

Skills should be **specific** (actionable steps, not vague advice), **verifiable** (clear exit criteria), and **minimal** (only what's needed to guide the agent).

Each skill lives in its own directory under `skills/` with a `SKILL.md` as the entry point.

---

## License

MIT

<!-- Link and image references -->

[img-bpftrace]: skills/find4/examples/bpftrace-one-liners-and-internals.html.png
[link-bpftrace]: https://find4.org/#game=1Zh9b9u6FYe_CuELDClmxS-Jk9j_OY7SGnFiI3bveu9WGJRE2ZxlUSOpOG7R777foSTbTdoubVdgA4qaoc7hoQ4fnhd9rK2F5RG3vNb7WFuIVGhuRTTnttartZvtM6_Z8drNWbPZc__-rNVrRuU6FHi-tDYzvUZjs9kcB1qkEU8XWiwWx6FaN0SQxcdLu05II18shKF1U74mzUSm-aNHIp7VPJTpwrNKJeb4n0alUFirSMbyS_vo9lrd3knruNNsNTvt3W7mMvquDVmRQT6WKU_kBzHfOaFek9EcKtJYvXUu0SrP5kZYWDC13t9rZ80ovjiBYLd70oloBxdRV7TOMOCBOGvy2vt6bYHXPFQKTuNYkIhoxUG3EHELSyvWlVB4zoOoA6GAn3XCEIMwbrdPLjA4O-1exDToBGeBs97unImuMxp1Lk4iehSfdoMWBidhHISnGJyHzYAHtOD5SafZxaAZt7sBCXfPw_iCZkQzbHbIVhCKbkjq5-L87KJVe_-JfAEnTaPtH77w__WmtfHnqj-sfdq_H-37Y80uhTtVOJhOU7BxKryRBEuG_YUNUys0_Gxq9b03SRGaG6WLd7-Z3I8vfUjc3Puzavy2Gszu-wN_Mh7ezchzIQhdKDqevcWJVoFgs20mWD-R3AiyFqpEaZJKcoE_c528mJHfqpUzrRaar9dAFEtEwoRaZlaC0gPrmbNuyTovrPfYyk02VkymYClfi9QatoInRMLiPA1pDYZJva2zlRa2FNfflIdcrlN2FPIMA-yJZh548qrO8mKBnMVKs9wI7SXiAbqlieJllExtwzoRY3mQCPqxMqwMuTUM-0febrZO8ZeIhT5QNUw9YGJVim2WQguayJQxEqvRzVrJJJk70_CQO_u1iCSOzLEaSXoPnsyLa-vOvjqRhbTLPHDnINWDNEo3Kg83gkQFjTXHvdWNSIWm4bYmUtz8RS4jcbyOCI3vJbG8ftDYXZrDC4_58nJ_qh_AOhjf3kJyMrwiNt3_oPb3_uhrdF7mMrEyZb9zLcnrh3ACPpH-Cjp9Y3D2kidst4-A9uFhIw_VRhh_4DJxJGC64Jg71oAwbK6ZNAxepUc4LtOgOZ5GjAJ5nWUyeiLAhleAbT9tl1rwyM0WqLKCXVE8LoHGfC6Yit3c_gKIaI_-kUqT7efb3V-bvBqVBL96RuIlYnoKDv67FNrcKngymatUzBPH2U-TuIvaLyDxzXA6g-So_B2M397R73TWn02_BuMtz9h16dVDEJUGa782Tq555mUqyxPEHMQuvqAVuTve6pyB3RLJ9-iVgzUCoIguG0QzFXtt98jZqbPkqRi5n-u9CNvgJJl4zBIZSsuwMxzdY4NSfx1o5ylpu1_DAAn9IMQprIRt1l1gNJDQIiRvF5LsryAQJdJCYGSVBc4US3kB8P9x-NtVCC-A7gZ4DW4oP1cD5Onr4YgyNVK0f_-NSDi1PFxhLzNJpBRp-xBCmUZyoX4Uwq-TZ5xdCly2sIwoxAOZ4Dxcsi6e70JTmQ6LWbeCQYZ9IuSSrMn2y1eCuAuxTERv-aF3x2JJsiCck2kkSx5qpEsUCgkbTN4aBxAGpRb2VicOhQZSPbNbIBNaoigOobZlsVZrLCmcHulr5Gft7hT-EI_SPkOxHz1w4BL9b2O4q0-_guH7-mHReDm5no_Gr9sjKND4Zja89eev_dn8blpOuQpyfu_3r8oJV0piGqDePIFU4DkbsDcigbO_GCK189_3oRmG3wqNI7Wp6rTC-tJZd3BFlOMuBwNWLgBOsex8RRjNF3BNSvEpFjZcUiJHSk6VQbQqIEe_xdeIY6TikuKcEjEUDI8FGApVJvekr8UaTgBTCICUg2kzDupigUQt2okLl-sst2Xu_lJcRjgOV8Ji55F4LHQdAtgCoF5hiY2WtEAkghy05hbrMTJaSEmU0EflM-T753ncf4R77A9RHIa_HuBdX_UE4LI1_CyOXs6uXc727ilyjoaXxOeA0veNP_Jn47snfN6qCHYLUCa47kX82h7waQVPXgYoHLFooK9ueq2W1zylK-6FytPCC2zsJTI4aJY_J_ZwF9l-FwUtPYaXYkf0zPVi10qvuX2FJiSE2o421ynJNHZPsWydOS-wowH4QuSEv-F014WcsPs8ZT6S7ta1G69Ygu4RtBtcJ0gGaOEBroZQGVhLG9AwdH1RKbi3wd0qS9Iw13CHLdsb7e4ZTjSmg3b9TYRqRpDjIzbZ2qVytxAVwUrANpZkXKNKRunn7T6YYPWN5pm7uhSQnXfKa_ujDKd8pbdypdyBocWypjwmnNKOW89x2_g5ancfAV5A7burCVE7HA3fUhN0dTWezm-Hs-Hr_mwIZEGvP0CDNPlScL0UW4pO48BQenuGb5brLPnuClThvfUzTJ09BFGka0P5N7cGfqI06qgjvsovTz2GV2JH4h0OHfhcccvZhNslUVv0SEu5WCLRC0eKV7XK3AW6su1xaXuAF8rXVUXanww9viFUEJItp3NgqbBw5Mol6uIO1YubJMuIT-ygikV8vrpS08pIpBUiOVUviO8Ug72SrwdJt0rEMUpcQtpsDVUIqBkSnDaZca0-NAP1WOSfHywLQvdux1I1IFpNJpv0GK_U6KP2COGpxul5p3l68pM07r5EvYDG67d3g1F_5t8N_oCC_252Oh2N_-bfU7Yfzvzp8E-KrZf96RuqAUbDO_9ZUMUBUZKdunjiTcAgsiib0efIAza3IknU5hmbX84zv9lS-3Mm-zsPO4tFBPOy0qLT6blGCP0R7vYWWZkbV2pWE-iQebqtQlz5oWfXO4GlR3tqEsrLZTFKJAhQAecylSFyBYhw1CyVC1J7bpYqiZCrKS_LDyhml2qDPr4xZu7PiL6FyiB3bVqwrYiHAjeuuafGqzJXfh4wLsS7AoZwRHROCUbSwPJwpfnxBv0_hQN4xlH2k1148RX0qxC-__wrL0Wc4tPup_ef_g0=

[img-brendan-gregg]: skills/find4/examples/brendan-gregg.png

[img-world-geo]: skills/find4/examples/world-geography-for-high-schoolers.html.png

[link-world-geo]: https://find4.org/#game=tZhdc-I6Eob_ioqLPTcwId-BOwcI8W74WOOpqTO7qZSwhdGMLXklORwyNf_9vC0DgeRMVWZytooqG1tqSd2P3m75W6MQjqfc8Ub3WyMTShjuRPrAXaPbOGmfXLTa562Tdtxud_3vc6PZsLoyicB761Kp6EGVZcJSN8ULerGU2dImS63z1lJap826lQmdGV4u1x--WE2dCp3Khfyroa66553u-emHdvvs8uxiN-CDTPfHdKLE34VUPJdP4mG3jGZDpg9GZBjXrP2ijK7KByscDNhG9z8NvhCd03M05B0-Ty5xs1jMLy7o5oqfJ2LRuG82Mqxkv9PxxdVpStaTS77otH0Tb1g6UWwbXZwez8_ITidtz0-OcXOeHJ9dzXFzynnaSan_6fGJSHBz0k475_Tq7PIynZ_RqzY_PengZt6ZX53SYJ0FP7uiqbbF6eX5AjcXl1f8lHrNF-05p8YXJ1fi3C_nIjm-PMGN6CQnncvG_XfyBZzUfhhdXepSxq7fSp4-dxrfn9dH8_7WcEvhA_dJmzxlw22s2EIbdotgspmPpjC20Xx2KPVF55U29fKDUfB5MkaLcXg3wOX3YDyMP9PdKJzN6DedhuS5BIxlmsLTGBrBHYvkI2wzvWCYCfOzIH_oXBu0meeVwN_K5MSWc6XtHh2tVqsPcyMdV0om_EOii6My54k4Cgr-pFXLm0SvVNjEyNJJUNdtxDC_IvO_WVZo69iCF7qyzPgJdP3wY5kLxlXKaksMpkvhhHdGrhWh3vQNf-cqc0-CScsCKzlMHrweSWvpV5aSpYZLZf3jpeDG0VLH2rglBhEGCyCkv8o8f8jFo6B1XgNhpfwSeJpKmj_PH-qt4L297wjF6_fbXSYT7xChHqXRqhDKHWFQmeTiSGF1Lb9cisQvBH4DPMVli-n-FqNNWW-n7809NmbBbRAFaDucXIe4BHHQAy90FwXXYTB-wcVNHZe-sMI4uwfDWuS5Xr0dhxlfcsNfgTDiX7DEtDZfx71uSdF0e5Tk3FBI2VK7TfM6ukM9lwwaI1yyFJbxxGhrWQJXG557Hup2geMJL2BWsd6SyHphPzVyR0xg-FxytVk1S3UBeXPCbnBKU3QfcOveB8tf75p6mq166HejsROut6ARR0EYs8kNG4bXUXAXBxE6Pj-9nUSjj5R4riez6ST6ODt4Owrugl4veIHPzFEey2TCPuFqVny9z5ATPP8JgmBLupZetIZyjuA6_lpXxtwYvWJWcFZyazmQoS2-rDJBkGzmIosSe56rRHTZzhb0BaFLHETE5Vxhl3rxGQnEURjDleCqyW61KaonauuMzi2bwu-EyrDKF0zLvMmutYV17Jlcqq-WXWPuX9kME3L6pbERx8tkh3qG6cFDbC7cSgjFpjxBaq6nEaqUhpkk6GhfcRekj7Sa9Ne5e3ZuvcJ3k7fLlG8gL44m07BHPA3-_TGIJ8TdNApHAzYaRGGfVIn0qReHPdYLox6y2iFmd1JRoFWtCLmeiz3KMgNnvgUzm0gBLx6J_1UcxdIruMKCY3tzs2ZGLIShthRksdGtQd2NpfJRoiMSTCFtuURDW8vK1MgC-oE842NJmdtnKumqVLAnYTRDDh7SdFcyWdadYoOKIfEU9yjGxuPQ4yWylTaKFdx89Q1tpSBjiwrJjHQS-XxrIjAJ0dyTBonHd6h5K2SqEEbXQleGDCv-9uSnTYbkl6yTXJdAn29de_RuvHb11w_wum_uV0SjyXg28SXR4I6Nw_EEd1Cu_oB9Csd9Au-fg5hBzAbB6AVavVwW-Mf-wT6hQkI02WyNorfY1zGJzZnpn0Gs0MpqX38fIkbsIm2tNkOV3EEuFADbdLAMBlVGAmfJ12xTz2g20xVVMT7fDXIUT_-t2u3FsQaO1lQlUNvKCSZf0vGiAph1-luBV6BiODBcYTGUDfUjkOISfGctu5QlE3-UWK2PcY3VF-F84uUFLoLqRjpiFLscvB0HmwS9iPHXwhUqrK8gNJz4FfHa-nOQt8ZS6feXUttq_gVWmwPJgWpF4XhIme8mjKi2ngVjFoz7QGjGboKPd7Gvt_utIL4LxqRcULIhNbwNKVeiKGfXA7Q6xC1GBtJYHrsRdYT2MDNe4N-YLSMKHOT8Rhrxg6prsRmCtAWdECi3GX2jaGSDXpINBj97Aam1YwvTSoK6R50nXOmtzs0gboFKQYal1MaJLGXh_wJlfpU7X4PhuIgnalueoapq7fJuJNNM1F1tCTMpzcOXdKJufYs9mfM17JNVkbIVyWydJJGb8xxAp_XcaEe8H7u3aJt3YWvnwr9B47YnyjfA2B_cTKLBLA7i0OtcfzAbRHF4E_a2Tz5G18E4nG3_DlGuhcEdiwakei8xvK0KBDEsSp44yqt3SDo24eUBj1ADHLN-RvZSgYUjO3lvvqLyE6pDlGoYGZFHOJMl7FPoKeTwrhKuyw5MIMsVECqPAZ75KxgzBRqnzc05gTitW4N2mF7Qs5xUCYkUyrk9TVRmzpW0dVO4fIVjBLCg_YFTGlviTIBRwXiGDSZJe4Xzp2a7NL7Uk6gH7FJQWuf2UGaNtOL_QuGPjpcvlv5uFncfNd7A4rA_JZnr0_nyOoziWxYFcf35YRjV_B3S1ieH6JIWgDw71WWV11EYQUJeiGBZmTJ_E3SOCqejjHJRC0c48CGTVml0WiXuFXv_EmtWbEYjffIYst3XMpwT-tPnBgL1Pw6FCUPSLavNqbHeM_trgR6JP-i7xdzXp8jquUNNJjCDen1EIHRQUHKFbqC-WzfZXNL3CJ84IZwJwCqfPUJcko1CZmYDdd3GF3QA1Q9Mgi40_LQ7S_ik8I6DwzI1HyqVll726ANfi_RYmCPvqFb6vOqWpFW_G7jNx7MfAnd_-HEQbzZfBL_ff_8T


[img-highschoolers-prompt]: skills/find4/examples/game-for-highschoolers.png

[img-k8s-operators]: skills/find4/examples/kubernetes-operators-core-concepts.html.png
[link-k8s-operators]: https://find4.org/#game=tVhrb9s4Fv0rhBdYJIAdO87DifeT46ipMY4dyE5md3aLgJZom2NJFEgqqafof59zqZfdNNNO0wUCR6L4uOQ999xz-akRC8tDbnmj_6mxEonQ3IrwkdtGv9HtdM9bnbNWtzPvdPru77dGs2FUpgOB779kC6ETYYWZpjROaeMtlNpMfSGjaHuUhkvqnq1WwtCkCY9p2KYa1lLluKPfjUrQOVahXMqvGXDZP-n1O92j7uXpaa9bmfEow--3xIoUnZcy4ZH8QzxWW282ZPioxUoaq7fuILTK0kcjLKY3jf5_G-dBKIITdBS9i84yxMOCn3UuAzx0e-EZ7zU-NBsr7G93UO8s6IQ9dOEnwUmv47q4iaUVcdlpcRp0F2QCpjk7PcXDcae3XJ7hAdOeLQQewt5lxz1cdPlxcIyH5XmXC9fn7PTk-JLMuDw9P3GGXfS6p9TS6QUnx9T57ELwC2rhl53z83NaK1gGJ7TWohdcLGgUP-32Li4aHz7TWeCQfL2Krv89iqLwP4kemN8bn-v9kd2fGnYt4n0UsOrw-2yotMBPEogU_Zv1idJgjH5WOt__0L_G56FPP_ez-fSWDaeTuT8djz1qm955_mByTWcXAJkrRQ5qzNeiWoxdZTIKZbJiV5EKNrRYoCKl0W0RZXRqmY7wsrY2Nf12u4bfkVTtUAWmHRR2tsVHK5KwVXdp81S2XKuRKmkHmbEqbmmRg8-0yTnCBFqmFt8Ly5b4yFItY2nlE46FJ7Wx0rAF7LVsqVXcZ5xh_-xg6Ob1i2mvBSAqacJDlqNSaMNw3iwRz2xwN2J2m4qmG1yOZeXgQ1oCK8rEWI5tMbVk0jbd8Nx8hu1araJIaPbMbbCGiUOfBoWMB9Y03RP1d-GJZ5mvztM0kvACDGMLQSce84SvBOHHbBBoj5F4EnTWV7A6AZcQsMLQbYVHj8Whkdd_zBklXbQJDj-CvyLwCBpl2O2GOtqLQP_c3IGo7wGSw9HYY-Pp9A5jrr3ZyPeu2Ww-mHsE0quZ5z_sNIy9B2_M5v7o5sbzR5Obr8B3mDuBjZVK2a0KcW41cFdaiORvIZfrYI3dBTbTol07-CVA36vnGo11R8Ow3U3f-VkLmlZGgkVkHHWSSaYyE23xEqcc-GeYVWoRMqDMCnZgUhEcMr7ihDumFkbop52v-JeZwxxYfEMxETgYWUXTPwm9ErR0_C_mINSyWiJraIcxwZMcfzu41YKQSsNzXGstElushq2t0cWuEQX0FRPiG14tC3hmYBXFQ8w3NLu0LIFtmiNNMBmKOFVAnX2B6FGCIIxFKLHCN1FNqeeIvEWhHgpN7nrFQS2d4XRjcbS2cfR2WFdJ5DtgTZgdDT02GA6n95M5BoF1veLf1WhyTcAFK49By57vvu3DuIKRfzUYsruK8HaArB05fBPGWiwFPBiINg9wlqbFM7tO3O8fbb3gwUscuzUrIs7duwJb2X26BUjwHEtD_G2IcGdApgzEIAgUjp58DgdAc-QYq0amKiSG9RXCICRCJtBGkXoGfoiCgdmFAcuiD-kak_JAlAOuZOIS0gL_82ndNAVa9w1wNB5lxPGuE4XIzns5VU6GGA8uDvLPrWfY_jagfsUVlpuN45WlXAGqLZxDi-CKwAad1O0m30WL59v4CZRc6Z7vwO5oAqodj9H5_u7GH1wTbAGIX-6Jngf38-ndaDydv4bXW4p4abc577K7NTd7qE0znUYvlUOZfpYaDie6pEMrG1sBT_lCRjjtV3UBgoNV3bY51RlK0HvI27eun5vHjtnBFTcyYCNK7FEEMs2QzLl1XJxGahsLQlPeu8sOZoLHEWKJ3aeIC1hzyMCIIZoIuxQOLEADtHk56IQdvMsipCS5FME2iKAlAB8IFh5sshRBCvWgRdn7lB1cC5GSPXK1tphefEwVDhKMDfoGlDj4zVazn7GDASxmdzJStraFdtEyARQ5UO7yQ5bg8cclhQk3R1_1lIO3eiLciufX_PZmFFei_RUUf2juqt_J4Nab3Q3AwrMhpG5Nt9W7E8DzqX_jTx24fx3Mh--rYa8hfBZgf-yfbC4SiMDtDrat4NFLZEfxX5wZD59ISYYtq1Lya3V0BqvAVyAiu65qObdv8w3h8SSNLKKACK1Mh2G_JlM3O8i2OnumEuToXHLuMD8oWCVil4RLfnwxgVO7uSYA58OPRc9m1eeGjGcHlELGt9Uih1UGeF5LzFCtta_tAwIX8L7vIqz1xJ64E1s5dxrmLGPIWEX2fxuL_zXiF0V5VBfb7ZWKEPj7fhQ_AftVnfoF9ouieV993HlD9CTFfD_Dw937wczhfwrhMR9NJ7MvsI1aZwCppuJdNCtNDPY9EiPPay9rihcl3RcNrbCqxr4C6hlqrJDrENwuorDQA19UZH1G4pitVVSIgVI6l4DIKyoSO4qaF1sGlUpAymXzzsgvdPUz0gT2QyP29XGTpY5zqRRkRsbIZmwNlm45fDGTxTHXW8ziFPaBOFodMT9LiHjb7ziUf3jYpOly1EFCafUEsUEDMqdgQ1JVOCNuYHlhJmJKk4wiNmCEarTHqfn_FIcE8Ujx0LQhUNxPKyrTVvsfhWgpzH87sKt7l-8AtjcfXrOStTHkYTQb4WnG8I8A_t4Ds-x8H0xmoyvUllXTK5TufeTkR4cx8vYVioydSCCduFIvImEFZ2SLI5RtdbhXHLHDAOHmBbbpPDROaodAXfXE4erSFrvGgazWKrPOJip88hpS2KBmXnbg4MkTlUhkegSLRpFYTML-l3U7x6cFsZt8ZEHMrPLpYX6D8YC84SyZwTl0IQGuJiOEaCF_a9fijITQQDEH51u60GQ3qv1eRHF7ALGyiNxIrThdfWBi-rJj67PmKcWNa4ZE0hZ9yoF1t1CXlzvltzTiWzqBwx-HfOkQ8tmOuGzTobwdxtWt4XfA-N1oMhiPfssv4X6dQJH43jvP9yZDAvGNNyG0gqapXvRm03sfme7B82fUtI_gQSEf6Lbqtr5yLYG7FVRV_a3Ljjr4dy4w2iuOSnElEPh4d9cLL_m6XL_k6_xWoLiKUYvfMa7GXJ-VV8UA3IIuF4GpSDi2prwdAaaCJxAMkVpBmdPdSEQWN5l6hrf9sqqlgEk1aXG6O0lsK1gjJ0NeRI76zVoCcEaxYges3gGCBto4pCmLy3lqlBSYJPdJE9H9BnE55Zhc0KOwsJaIffd6JxR0-cCA2iWqhDK7PRSVQH5n6EJPCxJn7m5mg9ziomkJwCucIepo6zaa5FcuTlnuQ7309pvYvVLp5OlaYTr_mHbtlZ-h18sL9Fdi4sP-xT7dseTX-p8_fP4T

[img-pdf-prompt]: skills/find4/examples/pdf-file-attachment.png
