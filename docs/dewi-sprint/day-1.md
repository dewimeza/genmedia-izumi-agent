# Day 1: Understand and run Izumi

Date: 2026-11-10
Branch: `dewi-sprint`
Fork: https://github.com/dewimeza/genmedia-izumi-agent
Upstream: https://github.com/GoogleCloudPlatform/genmedia-izumi-agent
Upstream commit at clone time: `e5f12b07a8fc39baadcb9e654f8a5e26faf059cd` (2026-10-22, "ads_x: change a finished campaign in place")

Project IDs, bucket names and billing details are intentionally not recorded in this repository.

## Setup

| Item | Value |
| --- | --- |
| uv | 0.13.6 |
| Node | 23.11.0 |
| Google Cloud CLI | 591.0.0 (593.0.0 from 2026-11-13) |
| Java (Firestore emulator) | Temurin 21.0.13 (Temurin 25.0.5 from 2026-11-13, see failure 7) |
| Python | 3.11.14, installed by uv (project allows >=3.11,<3.13; README mentions 3.12) |
| Run command | `./scripts/start-all.sh --with-db-emulator` (local Firestore emulator) |
| Cloud | Vertex AI enabled; billing linked; $10 monthly budget alert |

The budget alert is a notification only. It does not stop spending.

## Live model request

- App: Izumi Studio, Creative Toolbox agent
- Prompt typed: "Use Gemini Image, not Imagen. Generate one studio photo of a plain beige canvas tote bag on a white background. Standard size, one image only, no reference images."
- Prompt the agent sent to the image model: "Studio product photography of a plain beige canvas tote bag standing upright on a seamless solid white background, centered, clean studio lighting, minimalist, sharp focus, high quality" (aspect ratio 1:1)
- Agent model: `gemini-3.7-flash`
- Image model: `gemini-3.1-flash-image`
- Model location: `global`
- Result: HTTP 200 from the image model, one asset saved as `beige_canvas_tote_bag.png`
- Cost: free trial credits used so far across all Day 1 usage (chat text calls and the image): $0.09 of $300.00 ($299.91 remaining), read from Billing on 2026-11-10 at about 18:13 Pacific. Billing does not split out the single image; the published price suggests roughly $0.07 for one 1K image.

## Changes to upstream code

| File | Change | Reason |
| --- | --- | --- |
| `demos/backend/creative_toolbox/agent.py` | `MODEL_ID_FLASH_MODEL` changed from `gemini-2.5-flash` to `gemini-3.7-flash` | The agent hard-codes the old model and ignores `mediagent_config.json`. It returned 404. A secondary source says Google retired it on Vertex AI on 2026-10-20; Google's own page could not be checked. |
| `demos/backend/creative_toolbox/tools/image_gen_tools.py` | Empty reference-image names are filtered out in `generate_image_with_gemini` | The tool passed four empty names and the service tried to load an asset named "", so every request without reference images failed. |
| `demos/backend/.env.local` (not tracked by git) | `GOOGLE_CLOUD_LOCATION` changed from `us-central1` to `global` | The repo notes that these text models are served from `global`, and the repo's cloud deploy file also uses `global`. |

Side effect: Imagen returns 404 at `global`, so use Gemini Image for generation in this setup.

## What failed, and why

1. Second start of the app: "Address already in use". The first copy still held the backend, frontend and emulator ports. Fix: stop the old copy before starting again.
2. "No agents available": the frontend had no `demos/frontend/.env` (it needs `VITE_API_BASE_URL=http://localhost:8000`).
3. "Reauthentication is needed": the application-default credentials expired. Fix: `gcloud auth application-default login`, then set the quota project.
4. 404 for `gemini-2.5-flash`: see the changes table.
5. 404 for Imagen at `global`: see the side effect above.
6. Gemini Image failed on empty reference names: see the changes table.
7. Later, on 2026-11-13: the Firestore emulator had gone missing after a gcloud update. Reinstalling it (`gcloud components install cloud-firestore-emulator`, with `sudo` because gcloud is installed through Homebrew) brought a version that needs Java 25 or newer. Fix: Temurin 25 installed next to Java 21 and put first on `PATH` only when starting the app.

## Five-sentence summary

1. **What I changed:** I got Izumi running on my computer, fixed a retired model name and an empty-image bug, and added a product fidelity reviewer to the `creative_toolbox` agent. It compares a real scarf photo with an AI image on colour, pattern, shape and visible branding, and my Keep, Reject or Need more information choice is saved separately from its review.
2. **What I learned:** The AI model can't judge a small shift in neon pink just by looking, so adding measured colour differences as a hint, and never letting the reviewer be highly confident about colour, made it catch changes it had missed.
3. **What I tested:** I tested eight candidate images against one flash reference photo of a neon-pink scarf: two AI-generated (a close match and one with the corn removed) and six edited copies of the real photo (duller pink, slightly redder pink, blurry, partly hidden, warm light and a different background).
4. **What failed:** At first it called a visibly redder pink a match with high confidence, used wording that was too sure ("match precisely"), and didn't ask for a clearer photo when the scarf was partly hidden.
5. **What I will do next:** Next I'll test more AI-generated images from Izumi, including a strong colour change and an added or removed bird, check whether the reviewer gives the same answer when I repeat a test, and find out who made the design before sharing any images publicly.

Details of every test are in `test-results.md`. The plan asks for two cases to stay unseen until Day 5; all eight test images were used while tuning the reviewer, so two new cases were needed. Dewi prepared two new cases on 2026-11-12. They are kept in the private folder and have not been shown to the reviewer or to Claude.

## Still open

- Other places still hard-code `gemini-2.5-flash` and are likely to fail the same way: the `ads_codirector` and `elements_to_video` agents, and the creative writer tool in `demos/backend/creative_toolbox/tools/gemini_llm_tools.py`. `ads_x` already uses `gemini-3.7-flash`. None are needed for the minimum plan.
- Who made the scarf design is unknown, so the reference photo, the scarf images and the screenshots that show them stay out of this public repository.
- Evidence is listed in `evidence-index.md`.
