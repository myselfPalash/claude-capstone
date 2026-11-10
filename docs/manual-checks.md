# Manual checks (browser)

Status of every item below: **MANUAL - NOT RUN**. Automated tests (`pytest`) do not cover browser rendering, focus or refresh behaviour. Do not mark an item as passed unless a person actually ran it in a browser; record the date, browser and result next to it.

Setup: start the app with `python run.py` and open `http://127.0.0.1:5000/` (adjust if you changed host or port via environment variables; see README).

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 1 | Add a task | Appears in the list with an incomplete state | MANUAL - NOT RUN |
| 2 | View the list | All tasks shown in id order | MANUAL - NOT RUN |
| 3 | Toggle incomplete to complete | Visual completed state shown and kept | MANUAL - NOT RUN |
| 4 | Toggle complete to incomplete | Visual state reverts | MANUAL - NOT RUN |
| 5 | Edit a description | New text displayed; empty or over-255 text rejected with a visible message | MANUAL - NOT RUN |
| 6 | Delete a task | Task removed from the list | MANUAL - NOT RUN |
| 7 | Refresh persistence (T6) | After a browser refresh all tasks and their states are still present | MANUAL - NOT RUN |
| 8 | Stored HTML text | Add `<b>x</b>`; it is displayed literally, not rendered bold | MANUAL - NOT RUN |
| 9 | No login prompt (T7) | No authentication prompt appears at any point | MANUAL - NOT RUN |
| 10 | Keyboard and focus | All controls reachable and operable by keyboard; focus visible | MANUAL - NOT RUN |
| 11 | Rendering | Layout is readable and the completed state is distinguishable | MANUAL - NOT RUN |

## Automated result (for reference)

Full suite run for T-19: `pytest -q -p no:cacheprovider` gave `194 passed`.
