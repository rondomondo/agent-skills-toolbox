# vhs-rec

[vhs_rec](vhs-rec) is utility script wrapper used to interact with the [ghcr.io/rondomondo/vhs-rec](https://ghcr.io/rondomondo/vhs-rec) Docker image and that image in turn incorporates the [VHS](https://github.com/charmbracelet/vhs) image.

It adds three main capabilities to the base image functionality:

1) You can now use it to record Docker-related workflows that normally run externally.
2) It includes baked in extra utilities useful in container workflows: make, docker-compose, system utilities, zsh and themes, etc.
3) It also includes additional fonts and themes for recordings.

> **Also available as an [Agent Skill](#claude-code-skill)** -- install it to produce terminal GIF recordings directly from Claude Code with no terminal required. Use the `/vhs` slash command or just describe what you want and your AI Agent will handle it.

## Try it now

Install two lightweight wrappers, `vhs-rec` and [`vhs-demo`](#generate-the-command-with-vhs-demo), that call
Docker for you:

```bash
docker run --rm ghcr.io/rondomondo/vhs-rec install | sh
```

Then from any directory:

```bash
vhs-rec -- new test.tape                # generate a starter tape
vhs-rec test.tape                       # -> test.gif
vhs-rec demo -o ls.gif -- ls -l         # or skip the tape: record one command
```

> To uninstall: `docker run --rm ghcr.io/rondomondo/vhs-rec uninstall | sh`

The installer is a self-contained `sh` script streamed from the image. It installs `vhs-rec` and `vhs-demo`
(which needs `uv`) to `/usr/local/bin` if that is writable, otherwise retries with `sudo`, and finally falls back
to `~/.local/bin` (adding it to `PATH` in your `~/.zshrc`, `~/.bashrc` or fish config if needed). Running it again
is safe. The installed wrapper defaults to the image tag it shipped with.

## No install needed - just Docker

Add `-v /var/run/docker.sock:/var/run/docker.sock` if the recording itself runs docker commands.

```bash
docker run --rm -v "$PWD:/vhs" ghcr.io/rondomondo/vhs-rec:latest demo.tape -o demo.gif
```

## What is VHS
[VHS](https://github.com/charmbracelet/vhs) converts [.tape](https://github.com/charmbracelet/vhs#tutorial) script files into GIF (or other) recordings. Running it
directly as a container requires manually wiring up Docker volume mounts so the
container can read your tape file and write output back to the host.

This wrapper handles all of that automatically: also it rewrites the Output line in
your tape file to the correct filename and mounts the right directory, so you
can pass a single .tape file, multiple .tape files, or a directory full of .tape
files and get GIF files generated for all of them.

Note: calling with '--' passes everything through directly to the vhs app.

You do not even need a tape file: [one shot mode](#one-shot-recording) records any command in one line, and
can print the README snippet (GIF plus the command that made it) for you.

---

## Install from the github repository

```bash
# 1. Clone the toolbox repo
git clone https://github.com/rondomondo/toolbox.git && cd toolbox/vhs

# 2. Install the wrapper script
make install

# 3. Record a `tape` file using an example from the test directory 
vhs-rec test/test.tape

# 4. Done -- vhs/test/test.gif should now exist
file test/test.gif
```

No Docker pull needed upfront; `vhs-rec` pulls `ghcr.io/rondomondo/vhs-rec:latest` automatically on first run.

---

## Installation

From the cloned repository

### Install `vhs-rec` (`/usr/local/bin`, else `sudo`, else `~/.local/bin`)

```bash
make install
```


### Uninstall

```bash
make uninstall
```

---

## Usage

```
vhs-rec                          Show help
vhs-rec -h | --help              Show help only
vhs-rec <input.tape>             Convert one tape → <input>.gif
vhs-rec <input.tape> <out.gif>   Convert one tape with explicit output name
vhs-rec <directory>              Convert every .tape beneath a directory (recursive)
vhs-rec <tape1> <tape2> ...      Convert multiple tape files
vhs-rec demo [opts] -- CMD ARGS  One shot: record one command and its arguments
vhs-rec -x CMD [-x CMD ...]      One shot: record several commands in order
vhs-rec -- [args...]             Pass args directly to vhs (e.g. validate)
```

The `Output` line inside each `.tape` file is rewritten automatically to match the derived or explicit output path before vhs runs. The rewrite is made in place, so the tape file on disk is changed.

### Examples

```bash
# Single file
vhs-rec demo.tape

# Explicit output name
vhs-rec test/test.tape output/my-recording.gif

# Whole directory
vhs-rec test/

# Multiple files
vhs-rec test/m0.tape test/m1.tape test/m2.tape

# Pass args directly to original vhs (passthrough mode)
vhs-rec -- validate test/m0.tape
```

---

## One shot recording

Skip the tape file. Give `vhs-rec` the command and its arguments and it generates the tape, records it and
removes the tape again.

```bash
vhs-rec demo -o docs/url2pdf.gif --install screenshot --then 'ls -l pdfs' \
        -- url2pdf https://en.wikipedia.org/wiki/Special:Random
```

Everything after `--` is one command, quoted for you, so there is no nested quoting to get right. `--then`
(or `-x`) adds more commands to show afterwards. For several unrelated commands use `-x` alone:

```bash
vhs-rec --with pdf-strip \
        -x 'pdf-strip --check example.pdf' \
        -x 'pdf-strip example.pdf' \
        -o demo.gif
```

### Paste it into a README

Add `--snippet` and, once the GIF is written, `vhs-rec` prints the markdown for the GIF plus the command that
made it. Progress goes to stderr, so stdout is only the snippet and can be piped:

```bash
vhs-rec demo -o docs/url2pdf.gif --install screenshot --snippet -- url2pdf https://en.wikipedia.org/wiki/Special:Random | pbcopy
```

````markdown
![url2pdf demo](docs/url2pdf.gif)

```bash
vhs-rec demo \
        -o docs/url2pdf.gif \
        --install screenshot \
        -- url2pdf https://en.wikipedia.org/wiki/Special:Random
```
````

The image path is the `-o` path as given, so run from the repository root that holds the README. Running the
printed command again reproduces the same recording.

| Flag | Meaning |
|---|---|
| `-- CMD ARGS...` | One command with its arguments, quoted for you. Use with `demo`. |
| `-x, --exec CMD`, `--then CMD` | A command typed and run on screen. Repeatable, run in order, after any `-- CMD`. |
| `-s, --setup CMD` | Command run off screen before recording starts. Repeatable. |
| `--install TOOL`, `--with TOOL` | Off screen, install a docker-distributed tool: a toolbox name (`pdf-strip`, skipped if already on the PATH) or an image (`screenshot` or `ghcr.io/rondomondo/screenshot`). Repeatable. |
| `--env KEY=VALUE` | Off screen, export a variable before recording. Repeatable. |
| `-o, --output FILE` | Output file, inside the current directory. Default `demo.gif`. |
| `--theme NAME` | VHS theme. Default `Catppuccin Mocha`. |
| `--width N`, `--height N` | Size in pixels. Default `1200` x `700`. |
| `--wait SECS` | Linger after each command finishes. Default `2`. |
| `--timeout SECS` | Longest wait for one command to finish. Default `120`. |
| `--keep-tape` | Save the generated tape next to the output (`<output>.tape`) for hand editing. Refuses to overwrite. |
| `--snippet` | Print the markdown snippet described above. |

Notes:

- The recording shell starts in your current directory, so relative paths behave as they do on your host.
- After each command the recording waits for the shell prompt to return, so it is as long as the command takes
  plus `--wait`. Setup runs hidden and the screen is cleared before the first command; the wait for setup allows
  up to 300s, which covers a cold image pull.
- Your own shell expands globs and variables before `vhs-rec` sees them. Quote them (`'*.pdf'`) if the recording
  should show them unexpanded.
- A command can contain single quotes, double quotes or backticks, but not all three, and not a newline.
- Interactive programs (editors, pagers, prompts) cannot be driven this way. Write a tape for those.
- Use `--keep-tape` for more control, then edit the tape and run `vhs-rec <output>.tape`.

### Generate the command with vhs-demo

[vhs-demo.py](vhs-demo.py) prints the one shot line for you, so you only type the command you want to show. It
is installed as `vhs-demo` alongside `vhs-rec`, needs `uv`, and does not run Docker itself:

```bash
vhs-demo url2pdf https://en.wikipedia.org/wiki/1822_Vermont_gubernatorial_election
```

```
vhs-rec demo -o docs/url2pdf.gif --install screenshot --snippet -- url2pdf https://en.wikipedia.org/wiki/1822_Vermont_gubernatorial_election
```

Paste the line to record it (or pipe it: `./vhs-demo.py url2pdf URL | sh`). It knows how to get `url2pdf`,
`url2image`, `pdf-strip`, `mermaid-render`, `sanitise-ascii` and `regctl` into the recording container; git and
docker are already there. The GIF is named from the command (`docs/git-log.gif`, `docs/docker-ps-help.gif`).

| Option | Meaning |
|---|---|
| `--catalog` | One line per built-in help demo (the tools above, plus docker and git). `./vhs-demo.py --catalog \| sh` records them all. |
| `--head N` | Show the command piped through `head -n N`, so long help keeps its first lines on screen. |
| `-o FILE`, `-d DIR` | GIF path, or the directory for derived names (default `docs`). |
| `--install T`, `--env K=V`, `--then CMD` | Passed to `vhs-rec`. `--install` replaces the built-in choice, for tools it does not know. |
| `--list` | Show what it installs for each known tool. |

Put vhs-demo options before the command. git help uses `-h` because `--help` opens a pager.

---

## Tape file basics

A `.tape` file describes what to type and when:

```tape
Output demo.gif

Set Shell "zsh"
Set FontSize 16
Set FontFamily "JetBrains Mono"
Set Width 1200
Set Height 700
Set Theme "Catppuccin Mocha"
Set Padding 20

Type "echo hello"
Sleep 1s
Enter
Sleep 3s
```

See [test/](test/) for working examples including Catppuccin Mocha and Tokyo Night themes.

---

## What's in the image

Built on `ghcr.io/charmbracelet/vhs:latest` with:

| Category | Included |
|---|---|
| Shell | zsh + Oh My Zsh (philips theme) |
| Dev tools | git, make, golang, python3 (uv), docker, docker-compose, curl, wget |
| Fonts | JetBrains Mono, JetBrains Mono Nerd Font, Fira Code, Cascadia Code |
| Extras | sudo, htop, lsof, ssh-client, iproute2, dnsutils |

The container user (`vhs`) has passwordless sudo and is added to the `docker` group, so recordings can run real Docker commands.

---

## Docker targets

```bash
make build                     # Bump VERSION, build a single-arch image for local testing
make push                      # Build multi-platform (see PLATFORMS) and push :VERSION and :latest
make release                   # Bump patch version, then push
make release-rc                # Push VERSION-rc.1 without bumping VERSION or moving :latest
make retag FROM=latest TAG=v0.1.1   # Re-tag an existing remote image
make docker-shell              # Drop into a shell in the container
make inspect                   # Show the platforms in the remote :latest manifest
make clean                     # Remove local image tags (clean-builder removes the buildx builder)
```

Options:

```bash
make push NO_CACHE=1           # bust the build cache
make push REGISTRY=docker.io   # push somewhere else
```

`make push` and `make release` publish to the registry and need `docker login` first.

---

## Tests

The wrapper tests use a fake `docker`, so no containers or network are needed.

```bash
make test        # or: uv run pytest
```

---

## Requirements

- Docker (running locally)
- `bash` 3.2+
- `make` (for Makefile targets)

---

## Claude Code skill

<details>
<summary>Install the <code>/vhs</code> slash command for Claude Code</summary>

This repository ships a `/vhs` slash command skill for [Claude Code](https://claude.ai/code)
that lets Claude produce terminal GIF recordings -- no terminal required. Just describe what
you want and Claude will invoke the skill automatically.

### What it accepts

| Input | Example |
|---|---|
| Single tape file | `demo.tape` |
| Directory | `test/` |
| Multiple files | `m0.tape m1.tape m2.tape` |
| Commands (no tape file) | `demo -o x.gif -- ls -l` or `-x 'ls' -x 'date'` |

### Invoking the skill

Use the slash command directly:

```
/vhs demo.tape
/vhs test/
/vhs m0.tape m1.tape
```

Or just describe what you want in natural language -- Claude will invoke the skill automatically:

> *"Record a terminal GIF of the make install command"*
>
> *"Convert test/demo.tape to an animated GIF"*

### Installing the skill

#### Option A -- sync locally via `make`

```bash
# from inside the vhs directory
make sync-skill
```

This syncs `vhs-rec`, `SKILL.md`, and `README.md` to:

```
~/Code/agent-skills-toolbox/skills/vhs/
```

Override the target directory with `SKILLS_DIR`:

```bash
make sync-skill SKILLS_DIR=/path/to/your/project/.claude/skills/vhs
```

#### Option B -- copy manually

```bash
mkdir -p .claude/skills/vhs
cp vhs-rec SKILL.md README.md .claude/skills/vhs/
```

</details>
