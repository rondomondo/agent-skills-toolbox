
### Widget CSS style HTML

```html
<style>
    .f4-wrap {
        padding: 1rem 0;
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }
    .f4-game {
        background: var(--color-background-primary);
        border: 0.5px solid var(--color-border-secondary);
        border-radius: var(--border-radius-lg);
        padding: 1rem 1.25rem;
        margin-bottom: 48px;
    }
    .f4-game-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }
    .f4-game-icon {
        width: 36px;
        height: 36px;
        border-radius: var(--border-radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .f4-game-title-block {
        flex: 1;
        min-width: 0;
    }
    .f4-game-title {
        font-size: 15px;
        font-weight: 500;
        color: var(--color-text-primary);
        margin: 0;
    }
    .f4-game-meta {
        font-size: 12px;
        color: var(--color-text-secondary);
        margin: 0;
    }
    .f4-play {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        background: var(--color-background-secondary);
        border: 0.5px solid var(--color-border-secondary);
        border-radius: var(--border-radius-lg);
        text-decoration: none;
        cursor: pointer;
        transition: background 0.15s;
        margin-left: auto;
    }
    .f4-play:hover {
        background: var(--color-background-tertiary);
    }
    .f4-play-icon {
        width: 30px;
        height: 30px;
        border-radius: var(--border-radius-md);
        background: #e1f5ee;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .f4-groups {
        display: flex;
        flex-direction: column;
        gap: 5px;
    }
    .f4-round {
        font-size: 11px;
        font-weight: 500;
        color: var(--color-text-secondary);
        padding: 8px 0 3px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .f4-group {
        display: grid;
        grid-template-columns: 16px 1fr 90px minmax(0, 2fr);
        align-items: start;
        gap: 8px;
        padding: 7px 10px;
        border-radius: var(--border-radius-md);
        border: 0.5px solid var(--color-border-tertiary);
        background: var(--color-background-secondary);
    }
    .f4-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        flex-shrink: 0;
        margin-top: 3px;
    }
    .f4-cat {
        font-size: 13px;
        font-weight: 500;
        color: var(--color-text-primary);
        line-height: 1.3;
    }
    .f4-skill {
        font-size: 11px;
        padding: 2px 7px;
        border-radius: 20px;
        text-align: center;
        white-space: nowrap;
    }
    .f4-words {
        font-size: 11px;
        color: var(--color-text-secondary);
        line-height: 1.5;
        word-break: break-word;
    }

    /* Skill level badges */
    .sk-b {
        background: #e1f5ee;
        color: #085041;
    }
    .sk-i {
        background: #e6f1fb;
        color: #0c447c;
    }
    .sk-a {
        background: #faeeda;
        color: #633806;
    }
    .sk-e {
        background: #fcebeb;
        color: #791f1f;
    }

    /* Colour dots */
    .dot-red {
        background: #e24b4a;
    }
    .dot-green {
        background: #639922;
    }
    .dot-blue {
        background: #378add;
    }
    .dot-yellow {
        background: #ba7517;
    }
    .dot-purple {
        background: #7f77dd;
    }
    .dot-teal {
        background: #1d9e75;
    }
    .dot-orange {
        background: #d85a30;
    }
    .dot-indigo {
        background: #534ab7;
    }
</style>
```
