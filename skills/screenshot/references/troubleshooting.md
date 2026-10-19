# Troubleshooting

| Symptom | Fix |
| --- | --- |
| Cookie banner or modal in the shot | Add `--custom-selector '<css of the accept button>'`; for `element` add `--dismiss-popups` |
| Images missing, content cut short | Lazy loading: raise `--wait-for-timeout 8000` or use `--wait-for "<text>"`; do not pass `--no-scroll` |
| PDF is one huge clipped page | Keep `--unclip` on; check it was not disabled |
| Navbar repeated or cut in PDF | Already handled (fixed hidden, sticky flattened); use `--hide` for what remains |
| Sidebar or TOC wastes PDF width | `--hide '<css>'` |
| Mobile layout not applied | Use `--device`, not `--viewport-size`; check the name with `url2image devices` |
| `storage state file not found` | Path is a host path and must exist |
| Local file not found | Must be in `./html/` and given relative to it |
| `element` captures nothing | Selector matched no node: check it in a browser; only the first match is used |
| Old behaviour after a fix | Wrapper pulled a cached image: `docker pull ghcr.io/rondomondo/screenshot:latest` |
| MCP port in use | `MCP_PORT=3001 make mcp-up` |
| CJK text shows as empty boxes | The container has no CJK fonts; known limitation, not a site problem |
| Anything else | Re-run with `DEBUG=1` to see the docker command and shell trace |
