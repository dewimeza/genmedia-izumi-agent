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
| Google Cloud CLI | 591.0.0 |
| Java (Firestore emulator) | Temurin 21.0.13 |
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

## Still open

- Other agents (`ads_x`, `ads_codirector`, `elements_to_video`) still hard-code `gemini-2.5-flash` and are likely to fail the same way. They are not needed for the minimum plan.
- Evidence still to add by Dewi: one-page problem brief, initial flow map, two screenshots, the downloaded image, and the five-sentence summary (what I changed; what I learned; what I tested; what failed; what I will do next).
