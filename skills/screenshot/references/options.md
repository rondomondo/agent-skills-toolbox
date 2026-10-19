# Options reference

Run `url2image help` or `url2pdf help` for the authoritative list. Flags go before or after the target.

## Commands

| Command | Tools | Purpose |
| --- | --- | --- |
| (default) | both | Capture the target |
| `element` | url2image | Capture only the first match of `--selector` |
| `devices` | both | List devices usable with `--device` |
| `device-info <name>` | both | Print one device descriptor |

## Shared options

| Flag | Meaning |
| --- | --- |
| `--wait-for-timeout <ms>` | Wait before capture (default 3000) |
| `--wait-for, -w <text>` | Wait for text to appear |
| `--viewport-size <WxH>` | Default 1032x1376 |
| `--device <name>` | Emulate a Playwright device; overrides viewport, scale and user agent |
| `--user-agent <string>` | Default is desktop Chrome on macOS |
| `--no-scroll` | Skip the pre-render scroll that triggers lazy loading |
| `--dismiss-popups` / `--no-dismiss-popups` | Cookie and popup dismissal (default on; off for element) |
| `--custom-selector, -c <css>` | Extra popup selector to click (repeatable) |
| `--storage-state <file>` | Playwright storageState JSON; host path, mounted for you |
| `--log-level <level>` | DEBUG, INFO, WARNING (default), ERROR, CRITICAL |

## Image only (url2image)

| Flag | Meaning |
| --- | --- |
| `--convert <fmt>` | webp, jpeg, gif, ... via ImageMagick |
| `--device-scale-factor <n>` | Pixel ratio, default 2 |
| `--selector, -s <css>` | element only: what to capture |
| `--hide, -H <css>` | element: hide before capture (repeatable) |

## PDF only (url2pdf)

| Flag | Meaning |
| --- | --- |
| `--paper-format <fmt>` | A4 (default), Letter, A3, ... |
| `--headers-footers` / `--no-headers-footers` | Browser header and footer (default off) |
| `--unclip` / `--no-unclip` | Free fixed-height scroll containers so long app-shell pages paginate (default on) |
| `--hide, -H <css>` | Hide sidebars, TOCs, ads (repeatable) |

PDF rendering hides `position: fixed` elements and flattens `position: sticky`, so navbars do not repeat or
clip across page breaks.

## Environment

`IMAGE_TAG` (default latest), `IMAGE_REGISTRY` (ghcr.io), `IMAGE_REPO` (rondomondo/screenshot), `LOG_LEVEL`,
`DEBUG=1`, `MCP_PORT` (make targets, default 3000).
