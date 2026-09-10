## Widget HTML reference - card style with short links

This is the pattern for the `show_widget` chat widget when results are sourced from `themes.json`
(i.e. after publishing). One card per game round. Links are populated from the matching `themes.json`
entry for each round:

- `class="f4-card-title"` - `theme` field
- `class="f4-link f4-link-short"` - `https://find4.org/?` + `short_link`
- `class="f4-link f4-link-path"` (plain) - `https://find4.org/?config=` + `short_path`

Remember we want to screenshot and save this along with the other screenshots

```html
<style>
  .f4-cards { display: flex; flex-direction: column; gap: 10px; padding: 4px 0; }
  .f4-card { border: 0.5px solid var(--border); border-radius: 12px; background: var(--surface-2); overflow: hidden; }
  .f4-card-inner { display: flex; align-items: center; gap: 14px; padding: 12px 16px 10px; }
  .f4-card-icon { width: 38px; height: 38px; border-radius: 9px; background: #e1f5ee; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .f4-card-body { flex: 1; min-width: 0; }
  .f4-card-title { font-size: 14px; font-weight: 500; color: var(--text-primary); margin: 0 0 5px; }
  .f4-card-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
  .f4-badge { font-size: 11px; padding: 2px 7px; border-radius: 20px; background: var(--surface-1); border: 0.5px solid var(--border); color: var(--text-secondary); white-space: nowrap; }
  .f4-dots { display: flex; gap: 3px; align-items: center; }
  .f4-dot { width: 8px; height: 8px; border-radius: 50%; }
  .f4-links-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .f4-link { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; padding: 3px 9px; border-radius: 6px; text-decoration: none; border: 0.5px solid var(--border); color: var(--text-secondary); background: var(--surface-1); }
  .f4-link:hover { border-color: var(--border-strong); color: var(--text-primary); }
  .f4-link-short { background: #e1f5ee; border-color: #9fe1cb; color: #085041; }
  .f4-link-short:hover { background: #9fe1cb; color: #04342c; }
  @media (prefers-color-scheme: dark) {
    .f4-link-short { background: #04342c; border-color: #085041; color: #9fe1cb; }
    .f4-link-short:hover { background: #085041; color: #5dcaa5; }
  }
  .f4-link-path { background: #e8f0fe; border-color: #a8c0f8; color: #1a3a8f; }
  .f4-link-path:hover { background: #a8c0f8; color: #0d2260; }
  @media (prefers-color-scheme: dark) {
    .f4-link-path { background: #0d2260; border-color: #1a3a8f; color: #a8c0f8; }
    .f4-link-path:hover { background: #1a3a8f; color: #c5d8fc; }
  }
</style>

<div class="f4-game f4-cards">

  <!-- Round 1: themes.json entry [0] -->
  <div class="f4-card">
    <div class="f4-card-inner">
      <div class="f4-card-icon">
        <i class="ti ti-brain" style="font-size:20px;color:#085041;" aria-hidden="true"></i>
      </div>
      <div class="f4-card-body">
        <!-- theme -->
        <p class="f4-card-title">Frontier LLM Models and Advancements</p>
        <div class="f4-card-meta">
          <span class="f4-badge">2 rounds</span>
          <span class="f4-badge">32 words</span>
          <span class="f4-badge">8 categories</span>
          <div class="f4-dots">
            <div class="f4-dot" style="background:#e24b4a;"></div>
            <div class="f4-dot" style="background:#378add;"></div>
            <div class="f4-dot" style="background:#639922;"></div>
            <div class="f4-dot" style="background:#ba7517;"></div>
            <div class="f4-dot" style="background:#7f77dd;"></div>
            <div class="f4-dot" style="background:#1d9e75;"></div>
            <div class="f4-dot" style="background:#d85a30;"></div>
            <div class="f4-dot" style="background:#534ab7;"></div>
          </div>
        </div>
        <div class="f4-links-row">
          <!-- href = "https://find4.org/?" + short_link -->
          <a class="f4-link f4-link-short" href="https://find4.org/?ff-5844d766">
            <i class="ti ti-link" style="font-size:12px;" aria-hidden="true"></i>
            find4.org/?ff-5844d766
          </a>
          <!-- href = "https://find4.org/?config=" + short_path -->
          <a class="f4-link f4-link-path" href="https://find4.org/?config=games/frontier-llm-models-advancements.json">
            <i class="ti ti-external-link" style="font-size:12px;" aria-hidden="true"></i>
            find4.org/?config=games/frontier-llm-models-advancements.json
          </a>
        </div>
      </div>
    </div>
  </div>

  <!-- Round 2: themes.json entry [1] -->
  <div class="f4-card">
    <div class="f4-card-inner">
      <div class="f4-card-icon">
        <i class="ti ti-cpu" style="font-size:20px;color:#085041;" aria-hidden="true"></i>
      </div>
      <div class="f4-card-body">
        <!-- theme -->
        <p class="f4-card-title">LLM Capabilities, Inference and Ecosystem</p>
        <div class="f4-card-meta">
          <span class="f4-badge">2 rounds</span>
          <span class="f4-badge">32 words</span>
          <span class="f4-badge">8 categories</span>
          <div class="f4-dots">
            <div class="f4-dot" style="background:#e24b4a;"></div>
            <div class="f4-dot" style="background:#639922;"></div>
            <div class="f4-dot" style="background:#378add;"></div>
            <div class="f4-dot" style="background:#ba7517;"></div>
            <div class="f4-dot" style="background:#1d9e75;"></div>
            <div class="f4-dot" style="background:#7f77dd;"></div>
            <div class="f4-dot" style="background:#d85a30;"></div>
            <div class="f4-dot" style="background:#534ab7;"></div>
          </div>
        </div>
        <div class="f4-links-row">
          <!-- href = "https://find4.org/?" + short_link -->
          <a class="f4-link f4-link-short" href="https://find4.org/?ff-52b8630f">
            <i class="ti ti-link" style="font-size:12px;" aria-hidden="true"></i>
            find4.org/?ff-52b8630f
          </a>
          <!-- href = "https://find4.org/?config=" + short_path -->
          <a class="f4-link f4-link-path" href="https://find4.org/?config=games/frontier-llm-models-advancements.json">
            <i class="ti ti-external-link" style="font-size:12px;" aria-hidden="true"></i>
            find4.org/?config=games/frontier-llm-models-advancements.json
          </a>
        </div>
      </div>
    </div>
  </div>

</div>
```
