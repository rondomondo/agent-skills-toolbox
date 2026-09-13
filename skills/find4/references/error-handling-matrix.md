# Error handling matrix

| Condition | Action |
|---|---|
| Input fetch/read fails | Stop immediately, report full error |
| `find4_input.txt` empty after URL fetch | Attempt WebFetch fallback; stop if that also fails |
| JSON generation clearly invalid | Retry once; stop on second failure |
| Script exits non-zero (steps 3-5) | Retry once with fixed input; stop on second failure |
| Script exits non-zero (step 7) | Log warning, continue -- library is non-critical |
| Screenshot fails | Log warning, continue -- non-critical |
| Zip creation fails (step 8) | Log warning, continue -- zip is non-critical |
| SIGPIPE / exit 141 in Step 9 heredoc | `set -o pipefail` treats SIGPIPE from `/dev/urandom \| tr \| head` as a failure and kills the heredoc silently mid-run | Split the random suffix onto its own line: `RAND6=$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom \| head -c 6; true)`. The `; true` forces exit 0 after the subshell regardless of SIGPIPE. Do not use `set -euo pipefail` in the Step 9 heredoc — use it in secrets-loading only. |
