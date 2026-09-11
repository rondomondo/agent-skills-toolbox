
### Widget HTML reference — display only (no share URLs)

This is the pattern for the `show_widget` chat widget. It is display only: no share URLs,
no onclick handlers, no hidden spans. Play links live exclusively in the downloaded `.html` files.

```html
<div class="f4-wrap">
    <div class="f4-game">
        <div class="f4-game-header">
            <div class="f4-game-icon" style="background:#FAEEDA;">
                <i class="ti ti-building-castle" style="font-size:18px;color:#633806;" aria-hidden="true"></i>
            </div>
            <div class="f4-game-title-block">
                <p class="f4-game-title">World History for Teens</p>
                <p class="f4-game-meta">2 group sets · 32 words</p>
            </div>
            <div class="f4-play" style="cursor:default;opacity:0.6;">
                <div class="f4-play-icon">
                    <i class="ti ti-device-gamepad-2" style="font-size:18px;color:#0F6E56;" aria-hidden="true"></i>
                </div>
                <div>
                    <span style="display:block;font-size:11px;color:var(--color-text-secondary);">find4.org</span>
                    <span style="display:block;font-size:14px;font-weight:500;color:var(--color-text-primary);"
                        >Download HTML to play ↓</span
                    >
                </div>
            </div>
        </div>

        <div class="f4-groups">
            <div class="f4-round">Round 1</div>
            <div class="f4-group">
                <div class="f4-dot dot-red"></div>
                <div class="f4-cat">Famous Battles in History</div>
                <span class="f4-skill sk-i">Intermediate</span>
                <div class="f4-words">MARATHON · THERMOPYLAE · HASTINGS · WATERLOO</div>
            </div>
            <!-- one .f4-group per category, one .f4-round label per group_set -->
        </div>
    </div>

    <div class="f4-game">
        <!-- second game set, same structure -->
    </div>
</div>
```
