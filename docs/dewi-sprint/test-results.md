# Reviewer test results (Day 1)

Dewi ran these by hand in the Izumi chat (`creative_toolbox` agent), comparing a reference photo with a candidate image. The photos and generated scarf images are kept in a private folder outside this repository; only file names appear here.

Reference photo for every test: `scarfwflash.jpeg` (flash, flat, evenly lit).

## Versions of the reviewer

- **v1:** first working version. Findings per criterion, assessment, human decision recorded separately.
- **v2:** cautious wording ("appears to match", never "precisely"), a confidence level on each line.
- **v3:** colour confidence capped below "high"; automatic colour measurements (print hue, saturation, brightness, print area, ground cloth colour) passed to the reviewer as a hint; "unclear" findings explain why; a cannot_assess review always asks for a clearer photo.
- **v4:** the next step may only ask for a better or clearer image or a side-by-side check. It must not tell the user how to edit the image or whether to keep or reject it. Covered by tests and run by hand once (test 5, v4).
- **v5:** after test 10, the prompt's example next step is "generate a new image and run the review again", with no word on what to change. The code now replaces any next step that says how to fix the image or whether to keep or reject it (a word list) with a neutral side-by-side or regenerate-and-review step. The chat agent must pass the next step on as written, without adding its own advice. Covered by tests and run by hand once (test 10, v5).

## Results

| # | Candidate | Expected | Version | What the reviewer said | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | `genscarf.png` (AI-generated) | no obvious issue | v1 | No obvious issue; all four criteria matched. Wording was too strong ("match precisely", petal count). | Pass; wording fixed in v2 |
| 2 | `nomaiz.png` (AI-generated, four corn ears removed) | pattern mismatch | v1, then v2 in a new chat | Issues found. Pattern: the four ears of corn in the reference are missing in the candidate. Colour, shape, branding not flagged. Same finding both times. | Pass |
| 3 | `scarf_test_4b_partly_hidden.jpg` | cannot assess | v2 | Cannot fully assess; lower right covered. Pattern and shape unclear; did not guess. Did not ask for a clearer photo. "Confidence: High" next to "Unclear" was confusing. | Pass with two gaps; fixed in v3 |
| 4 | `scarf_test_2b_duller_pink.jpg` | colour mismatch (duller) | v2 | Issues found. Colour differs: paler, desaturated pink. Pattern, shape, branding matched. | Pass |
| 5 | `scarf_test_2c_slightly_redder_pink.jpg` | colour difference (redder) | v2 | "Appears to match", confidence High. | **Miss** (Dewi confirmed the colours differ) |
| 5 | same image | colour difference (redder) | v3 | Issues found. Colour appears to differ, about 8.6 degrees redder, ground cloth steady, confidence Medium. | Pass. Next step advised adjusting the colour, which is why v4 limits next steps. |
| 5 | same image | colour difference (redder); next step only a check or better image | v4 | Issues found. Pink print appears slightly redder, off-white ground unchanged, confidence Medium. Pattern, shape, branding matched (High). Next step: compare the print colours side by side under consistent lighting. Then asked Keep / Reject / Need more information without choosing. No editing advice. | Pass |
| 6 | `scarf_test_5b_different_background.jpg` | no product change | v2 (old code still running), then v3 | No obvious issue both times; background noted as the only difference. v2 showed colour confidence High (the v3 cap was not yet running); v3 showed Medium and mentioned the measurements. | Pass |
| 7 | `scarf_test_5a_warm_light.jpg` | lighting, not product change | v3 | Cannot fully assess. Colour unclear because the candidate is lit much warmer. Pattern, shape, branding matched. Suggested retaking in neutral light. | Pass |
| 8 | `scarf_test_4a_blurry.jpg` | cannot assess | v3 | Cannot assess. All four criteria unclear, each with a reason. Asked for a sharper, fully visible, evenly lit image. | Pass |
| 9 | Decision step | stored separately, only after the user chooses | v1 | After "Reject, the corn is missing" the decision was recorded for that review (`7d664f44`) with the note. The review itself was unchanged. In every later review the agent asked for Keep / Reject / Need more information and did not choose. | Pass |
| 10 | `scarf_test_2a_redder_pink.jpg` | colour mismatch (strong, redder) | v4 | Issues found. Print appears shifted from cool magenta-pink to orange-red or coral, ground cloth unchanged, confidence Medium. Pattern, shape, branding matched (High). Next step: "Regenerate the image to better match the original pink print colour." Then asked Keep / Reject / Need more information without choosing. | Pass with one gap: regenerating is an allowed next step, but "to better match the pink" points at what to fix, and suggesting a regenerate leans towards rejecting. The rule is only in the prompt, not checked in code. |
| 10 | same image | colour mismatch (strong, redder); next step only a check or new image | v5 | Issues found. Print appears shifted from bright cool pink to warm coral-red, about 25 degrees redder by the measurement, ground cloth unchanged, confidence Medium. Pattern, shape, branding matched (High). Next step: "Generate a new image and run the review again to verify the print colour." Then listed Keep / Reject / Need more information without choosing. | Pass. The next step names what to check, not what to change. It is the model's own wording, so the prompt change was enough here and the code check did not need to step in. |

Not run: an added or removed bird.

## What failed, and what changed because of it

- **Overconfident wording** (test 1): fixed with cautious wording and confidence levels (v2).
- **Missed subtle colour change** (test 5, v2): the model compared the images by eye. v3 adds measured colour differences as a hint, tells the reviewer how to read them (a real change in the print versus a lighting change), and caps colour confidence below high in code.
- **No request for a clearer photo** and **confusing "High" on unclear findings** (test 3): v3 adds a default next step in code and makes unclear findings low confidence.
- **Next step told the user how to fix the image** (test 5, v3): v4 restricts next steps to checking or getting a better image. Rerun with v4: the next step was a side-by-side check only.
- **Next step still pointed at the fix** (test 10, v4: "regenerate to better match the original pink"): v5 checks the next step in code, not only in the prompt.

## Limits

- One scarf. Results say nothing about other products.
- Tests 3 to 8 use edited copies of the real photo, not AI-generated images, so they test how the reviewer reads colour, blur, covering and background, not how Izumi's own images drift.
- Each case was run once or twice. A language model can answer differently on a repeat run.
- The colour measurements are a hint. Lighting and cameras change them, and they were checked on only these seven edited images.
- Tests were judged by one person looking at the images.
