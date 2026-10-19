---
name: shell-install-pattern
description: >
    Audit and fix the install/uninstall strategy for a shell-based CLI tool distributed via
    `docker run ... install | sh` or a Makefile. Enforces: correct install dir priority
    (/usr/local/bin -> sudo -> ~/.local/bin, drop ~/bin), cross-file consistency between
    install.sh / uninstall.sh / Makefile, and a POSIX-safe PATH guard that detects the user's
    shell, writes the export line to the right rc file (~/.zshrc, ~/.bashrc, fish config),
    and guards against duplicate writes. Use this skill whenever the user asks to review,
    improve, or apply best-practice install patterns to shell scripts or Makefiles.
    Trigger phrases: "install best practice", "install dir", "path guard", "shell install pattern",
    "fix install script", "align install", "rc file injection".
---

# Shell Install Pattern Skill

Audits and rewrites install/uninstall scripts and Makefile targets to follow the canonical
best-practice pattern for shell-distributed CLI tools. Covers install directory selection,
cross-file consistency, and automatic PATH injection with rc-file detection.

---

## What This Skill Does

1. Reads every file that references an install directory
2. Aligns them all to the correct priority order and fallback
3. Adds a POSIX-safe PATH guard with rc-file injection wherever the fallback dir is used
4. Updates every display string (printf/echo output) to match the real dirs

---

## Step 1: Read the Files

Before touching anything, read:

- `install.sh` (or equivalent streaming install script)
- `uninstall.sh` (or equivalent)
- `Makefile`
- Any other script that references `/usr/local/bin`, `~/bin`, or `~/.local/bin`

Grep for these patterns to find every reference site:

```
/usr/local/bin
~/bin
$HOME/bin
~/.local/bin
$HOME/.local/bin
```

---

## Step 2: Install Directory Priority Order

Apply this order everywhere, consistently:

| Priority | Directory | When |
|---|---|---|
| 1 | `/usr/local/bin` | writable directly (CI, containers, root) |
| 2 | `/usr/local/bin` via sudo | sudo available |
| 3 | `~/.local/bin` | fallback -- user-writable, XDG default |

**Drop `~/bin` entirely.** It is a legacy pre-XDG convention. Modern tooling (pip, uv, cargo,
pipx, volta) all use `~/.local/bin`. Having both creates confusion and a third code path.

---

## Step 3: PATH Guard -- The Core Pattern

This function must be included in every script that installs to `~/.local/bin`. It runs under plain
`/bin/sh` (the streamed installer is piped to `sh`) and works on macOS bash 3.2 and dash. It does use `local`,
which is not strict POSIX but is supported by every `sh` in practice; do not use bash 4 features, arrays or
`sed -i` here.

```sh
add_to_path_if_needed() {
    local dir="$1"
    local rcfile

    # Already on PATH -- nothing to do.
    case ":$PATH:" in
        *":$dir:"*) return 0 ;;
    esac

    # Detect rc file from current shell.
    case "${SHELL##*/}" in
        zsh)  rcfile="$HOME/.zshrc" ;;
        bash) rcfile="$HOME/.bashrc" ;;
        fish) rcfile="$HOME/.config/fish/config.fish" ;;
        *)    rcfile="" ;;
    esac

    if [ -n "$rcfile" ]; then
        # Guard against duplicate writes.
        if ! grep -qF "$dir" "$rcfile" 2>/dev/null; then
            mkdir -p "$(dirname "$rcfile")"
            case "$rcfile" in
                */config.fish) printf '\nfish_add_path "%s"\n' "$dir" >> "$rcfile" ;;
                *)             printf '\nexport PATH="%s:$PATH"\n' "$dir" >> "$rcfile" ;;
            esac
            ok "added $dir to PATH in $rcfile"
            warn "restart your shell or run: source $rcfile"
        else
            info "$dir already referenced in $rcfile -- skipping"
        fi
    else
        warn "$dir is not on PATH -- add: export PATH=\"$dir:\$PATH\""
    fi
}
```

**Key design decisions:**

- `case ":$PATH:"` with colons on both sides prevents false substring matches (e.g. `/bin`
  matching `/usr/local/bin`)
- `grep -qF` uses fixed-string (not regex) matching -- safe for paths with dots or slashes
- `2>/dev/null` on grep handles the case where the rc file does not exist yet, and `mkdir -p` on its
  directory handles a missing `~/.config/fish/`
- Write without prompting -- stdin is consumed in a `| sh` pipe so interactive confirmation is impossible
- Fish needs different syntax: `export PATH=...` is bash/zsh only, so the fish rc file gets
  `fish_add_path "<dir>"` instead. This is what every installer and Makefile in the toolbox does
- An unknown shell writes nothing and prints the `export` line for the user to add themselves

---

## Step 4: Apply to install.sh (Streaming Script)

The streaming script emits sh code that runs on the host. The `add_to_path_if_needed`
function goes inside the heredoc (between `cat <<'HEADER'` and `HEADER`) so it is emitted
into the generated script.

Structure of `try_install()`:

```sh
try_install() {
    local bin_dir

    # Prefer /usr/local/bin (with or without sudo), fall back to ~/.local/bin.
    USE_SUDO=0

    if install -m 755 /dev/null /usr/local/bin/.probe 2>/dev/null; then
        rm -f /usr/local/bin/.probe
        bin_dir=/usr/local/bin
    elif sudo install -m 755 /dev/null /usr/local/bin/.probe 2>/dev/null; then
        sudo rm -f /usr/local/bin/.probe
        bin_dir=/usr/local/bin
        USE_SUDO=1
    else
        bin_dir="$HOME/.local/bin"
        mkdir -p "$bin_dir"
        add_to_path_if_needed "$bin_dir"   # <-- PATH guard fires here only
    fi

    # Install and symlink, using sudo only when USE_SUDO=1 ...
}
```

The PATH guard fires **only** on the `~/.local/bin` branch. `/usr/local/bin` is always on
PATH so no guard is needed there.

---

## Step 5: Apply to Makefile install Target

Makefile syntax requires `$$` for shell variables and nested `case`/`esac` blocks. The
guard is inlined (no function extraction in make). Same priority as the streamed installer: direct,
then sudo, then `~/.local/bin`:

```makefile
.PHONY: install
install: ## Install; tries /usr/local/bin (direct then sudo), falls back to ~/.local/bin
	@if install -m 755 <src> /usr/local/bin/<name> 2>/dev/null; then \
	  IDIR=/usr/local/bin; \
	elif sudo install -m 755 <src> /usr/local/bin/<name> 2>/dev/null; then \
	  IDIR=/usr/local/bin; \
	else \
	  mkdir -p ~/.local/bin; \
	  install -m 755 <src> ~/.local/bin/<name>; \
	  IDIR=~/.local/bin; \
	  case ":$$PATH:" in \
	    *":$$IDIR:"*) ;; \
	    *) RCFILE=""; \
	       case "$${SHELL##*/}" in \
	         zsh)  RCFILE="$$HOME/.zshrc" ;; \
	         bash) RCFILE="$$HOME/.bashrc" ;; \
	         fish) RCFILE="$$HOME/.config/fish/config.fish" ;; \
	       esac; \
	       if [ -n "$$RCFILE" ]; then \
	         if ! grep -qF "$$IDIR" "$$RCFILE" 2>/dev/null; then \
	           mkdir -p "$$(dirname "$$RCFILE")"; \
	           case "$$RCFILE" in \
	             */config.fish) printf '\nfish_add_path "%s"\n' "$$IDIR" >> "$$RCFILE" ;; \
	             *) printf '\nexport PATH="%s:$$PATH"\n' "$$IDIR" >> "$$RCFILE" ;; \
	           esac; \
	           printf "$(GREEN)Added$(RESET)   $$IDIR to PATH in $$RCFILE\n"; \
	           printf "$(YELLOW)Restart$(RESET) your shell or run: source $$RCFILE\n"; \
	         else \
	           printf "$(CYAN)Skipped$(RESET) $$IDIR already referenced in $$RCFILE\n"; \
	         fi; \
	       else \
	         printf "$(YELLOW)Warning$(RESET) $$IDIR is not on PATH -- add: export PATH=\"$$IDIR:\$$PATH\"\n"; \
	       fi ;; \
	  esac; \
	fi
	# ... install and symlink steps follow
```

---

## Step 6: Apply to uninstall.sh and make uninstall

The uninstall search dirs must exactly mirror the install dirs. Search both, handle sudo for
`/usr/local/bin`:

```sh
try_remove_bin() {
    local name="$1"
    local removed=0
    for dir in /usr/local/bin "$HOME/.local/bin"; do
        local target="$dir/$name"
        [ -f "$target" ] || [ -L "$target" ] || continue
        if rm -f "$target" 2>/dev/null; then
            ok "removed $target"
            removed=1
        elif sudo rm -f "$target" 2>/dev/null; then
            ok "removed $target (via sudo)"
            removed=1
        else
            warn "could not remove $target (permission denied)"
        fi
    done
    [ "$removed" -eq 0 ] && info "$name not found in /usr/local/bin or ~/.local/bin -- nothing to remove" || true
}
```

Makefile `uninstall` target:

```makefile
.PHONY: uninstall
uninstall: ## Remove binaries from /usr/local/bin and ~/.local/bin
	@for dir in /usr/local/bin ~/.local/bin; do \
	  for name in <name1> <name2>; do \
	    if [ -f "$$dir/$$name" ] || [ -L "$$dir/$$name" ]; then \
	      if rm -f "$$dir/$$name" 2>/dev/null || sudo rm -f "$$dir/$$name"; then \
	        printf "$(GREEN)Removed$(RESET) $$dir/$$name\n"; \
	      fi; \
	    fi; \
	  done; \
	done
```

---

## Step 7: Update Display Strings

After updating all logic, grep for every printf/echo that mentions a directory and update it.
Common places:

- Help/usage output in the interactive branch of `install.sh`
- The "Done." summary printed at the end of the streaming install
- The interactive branch of `uninstall.sh`
- Makefile help comments (the `## ...` strings after targets)

Replace all `~/bin` references with `~/.local/bin` in user-facing strings.

---

## Step 8: Verify Consistency

Run this mental checklist before finishing:

- [ ] `install.sh` uses `/usr/local/bin` -> sudo -> `~/.local/bin`
- [ ] `install.sh` PATH guard present in heredoc, fires only on `~/.local/bin` branch, and writes `fish_add_path` (not `export`) for fish
- [ ] `uninstall.sh` searches `/usr/local/bin` and `~/.local/bin` (not `~/bin`)
- [ ] `make install` uses same dir priority (including the sudo step) and has the same PATH guard
- [ ] `make uninstall` searches same dirs as `make install`
- [ ] No `~/bin` or `$HOME/bin` references remain anywhere (logic or display strings)
- [ ] All display strings reference `~/.local/bin` not `~/bin`

---

## Output

Report:
1. Every file changed and every reference site found
2. A before/after summary of the dir choices
3. Confirm the PATH guard is present and where it fires
4. Flag any edge cases (fish shell, sudo not available, unknown shell, etc.)
