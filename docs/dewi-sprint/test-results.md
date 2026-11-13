# Reviewer test results (Day 1)

Dewi ran these by hand in the Izumi chat (`creative_toolbox` agent), comparing a reference photo with a candidate image. The photos and generated scarf images are kept in a private folder outside this repository; only file names appear here.

Reference photo for every test: `scarfwflash.jpeg` (flash, flat, evenly lit).

## Versions of the reviewer

- **v1:** first working version. Findings per criterion, assessment, human decision recorded separately.
- **v2:** cautious wording ("appears to match", never "precisely"), a confidence level on each line.
- **v3:** colour confidence capped below "high"; automatic colour measurements (print hue, saturation, brightness, print area, ground cloth colour) passed to the reviewer as a hint; "unclear" findings explain why; a cannot_assess review always asks for a clearer photo.
- **v4:** the next step may only ask for a better or clearer image or a side-by-side check. It must not tell the user how to edit the image or whether to keep or reject it. Covered by tests and run by hand once (test 5, v4).
- **v5:** after test 10, the prompt's example next step is "generate a new image and run the review again", with no word on what to change. The code now replaces any next step that says how to fix the image or whether to keep or reject it (a word list) with a neutral side-by-side or regenerate-and-review step. The chat agent must pass the next step on as written, without adding its own advice. Covered by tests and run by hand once (test 10, v5).
- **v6:** after test 11, the code cuts three close-ups from the same parts of the print in both images (centre, top-left corner, halfway to the left edge), placed by finding the printed area so differently framed photos still line up. The reviewer compares each pair and reports a detail check for each. In code: a close-up that differs makes the pattern a mismatch, and pattern confidence can be High only when every close-up matches. Covered by tests; crops checked by eye on the reference and `scarf_generated_v3.png`; run by hand once (test 11, v6).

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
| 11 | `scarf_generated_v3.png` (generated by Izumi) | small colour shift (more purple) and a changed medallion centre (spiral in the reference, rings of dots in the candidate) | v5 | Issues found. Colour: print about 10.5 degrees more purple, ground cloth similar, confidence Medium. Pattern: "appears to match, including the central sun medallion", confidence High. Shape, branding matched. Next step was the neutral text set in code, so the code check replaced the model's own suggestion. Asked Keep / Reject / Need more information without choosing. | Partly: colour caught; **medallion centre missed**, and with High confidence. Code check worked. |
| 11 | same image | same | v6 | Issues found. Colour: more purple-magenta, Medium. Pattern: appears to differ, Medium: the medallion core shows concentric rings instead of a fine spiral, and the left swallow's body markings are redrawn. Shape, branding matched (High). Next step: generate a new image and run the review again. Asked Keep / Reject / Need more information without choosing. | Pass. Both changes caught. The swallow finding was new to Dewi too; checked by zooming in: the star on the swallow's body became a dot. The reviewer's "star and numeral" wording overstates the second mark, which looks more like a small cross. |

A removed motif is covered by test 2 (corn ears). Not run: an added motif, and test 2 with v6.

## What failed, and what changed because of it

- **Overconfident wording** (test 1): fixed with cautious wording and confidence levels (v2).
- **Missed subtle colour change** (test 5, v2): the model compared the images by eye. v3 adds measured colour differences as a hint, tells the reviewer how to read them (a real change in the print versus a lighting change), and caps colour confidence below high in code.
- **No request for a clearer photo** and **confusing "High" on unclear findings** (test 3): v3 adds a default next step in code and makes unclear findings low confidence.
- **Next step told the user how to fix the image** (test 5, v3): v4 restricts next steps to checking or getting a better image. Rerun with v4: the next step was a side-by-side check only.
- **Next step still pointed at the fix** (test 10, v4: "regenerate to better match the original pink"): v5 checks the next step in code, not only in the prompt.
- **Missed a small pattern change** (test 11, v5): the centre of the medallion changed from a spiral to rings of dots, and the reviewer said the pattern matched with High confidence. v6 adds close-ups and limits pattern confidence. The close-ups cover only three areas, so a change elsewhere in the print can still be missed.

## Limits

- One scarf. Results say nothing about other products.
- Tests 3 to 8 use edited copies of the real photo, not AI-generated images, so they test how the reviewer reads colour, blur, covering and background, not how Izumi's own images drift.
- Each case was run once or twice. A language model can answer differently on a repeat run.
- The colour measurements are a hint. Lighting and cameras change them, and they were checked on only these seven edited images.
- Tests were judged by one person looking at the images.
