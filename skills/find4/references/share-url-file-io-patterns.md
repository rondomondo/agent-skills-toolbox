# Share URL file I/O patterns

Share URLs are 2,000-3,000+ characters. Always redirect to a file. Never capture in a variable.

## Anti-patterns (silently truncate)

```bash
# bash variable
URL=$(bash share_game.sh ...)

# Python -c inline string
python3 -c "url = 'https://find4.org/#game=AAAA...'"

# heredoc with long line
python3 << 'EOF'
url = 'https://...very long...'
EOF
```

## Correct pattern

```bash
# write to file, read from file
bash $FIND4_SCRIPTS/share_game.sh ... > url.txt
url=$(cat url.txt)    # safe -- already in a file
```

## Play button

Never use `window.open()` or `onclick` for the Play button in standalone HTML -- use a plain
`<a href="...">`. The `generate_html.py` script handles this correctly; do not override it.
