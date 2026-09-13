
# Find4 UI & Styling Reference

## Visual Rules
* **Icons**: Choose emojis based on theme (e.g., 🚀 for Tech, 🏛️ for History).
* **Backgrounds**: Pair icons with light tints (e.g., `#e6f1fb` for Blue-50).



## Widget vs. HTML File

### What is the Widget
The widget implied an element rendered via `show_widget`
It is display only so has NO share URLs contained in it. Never embed share URLs in the widget — NEVER in `href`,
not in hidden `<span>` tags, not in JS string literals. These count toward the 10KB payload limit and cause truncation.
Any reference to `Play Buttons` is to be replaced with a static "Download HTML to play" label.
Refer to `ui-widget.html.md` for how the Widget HTML is to look (remember for the "No URL" pattern)

#### Canonical Widget CSS
Refer to `ui-widget.css.md` for the CSS styling for the Widget which you must include
within the `<style></style>` block in all standalone HTML files.

### What is the Standalone HTML File
This is the Full self contained HTML file. It DOES Includes the `href` with the Base64 share URL generated as previously geberated by `share_game.sh`.
Note the use the lazy-href pattern described in SKILL.md Step 6.
