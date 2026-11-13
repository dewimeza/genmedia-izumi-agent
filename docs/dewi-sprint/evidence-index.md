# Evidence index

One list of what exists, where it lives, and which items are private. Private items are named but not stored in this repository.

## In this repository (branch `dewi-sprint`)

| Item | Where |
| --- | --- |
| Fork | https://github.com/dewimeza/genmedia-izumi-agent |
| Upstream commit at clone time | `e5f12b0` (GoogleCloudPlatform/genmedia-izumi-agent) |
| Day 1 note: setup, live model request, code changes, failures, five sentences | `docs/dewi-sprint/day-1.md` |
| One-page problem brief: persona, acceptance criteria, comparison criteria | `docs/dewi-sprint/problem-brief.md` |
| Initial flow map with real file paths | `docs/dewi-sprint/flow-map.md` |
| Reviewer test results and what failed | `docs/dewi-sprint/test-results.md` |
| Reviewer code | `demos/backend/creative_toolbox/tools/product_review_tools.py`, `demos/backend/creative_toolbox/instructions/product_reviewer.py` |
| Reviewer tests (79 in the creative_toolbox folder, all passing when last run) | `tests/demos/creative_toolbox/tools/test_product_review_tools.py` |

## Commits

| Commit | What |
| --- | --- |
| `aaeee5f` | Run Izumi locally, fix retired model and empty image references |
| `ae8e888` | Problem brief |
| `d82ad66` | Flow map |
| `49c9cf6` | Product fidelity review tool |
| `c286a7a` | Reviewer test results |

Later commits are on the branch; use `git log` for the full list. Nothing has been pushed to the fork yet.

## Private (not in this repository)

| Item | Why private |
| --- | --- |
| Live model output: `beige_canvas_tote_bag.png`, the prompt and configuration for it are in `day-1.md` | Kept with the other images; a generic bag with no third-party design |
| Reference photo `scarfwflash.jpeg` and the earlier no-flash photo | The scarf design's maker is unknown; permission to publish is unconfirmed |
| AI-generated scarf images `genscarf.png`, `nomaiz.png` | Same |
| Seven edited test images (`scarf_test_2a` to `5b`) and their README | Same |
| Two screenshots from 2026-11-12: the blurry-scarf review and the partly-hidden review | They show the scarf |

Images are kept in a private folder outside the repository, and `.gitignore` blocks photo files under `docs/dewi-sprint/`.

## Not recorded here on purpose

Project IDs, bucket names, billing details, account emails and credentials.
