# Problem brief: product fidelity reviewer for a scarf

Status: DRAFT for Dewi to review and edit. Written from the Day 1 conversation; not yet committed.

## User (fictional persona)

Lena Marchetti, 38, owns a small boutique on a neighbourhood shopping street in San Francisco. It carries a curated mix of apparel, home goods, bags and accessories from independent makers, including a small line of scarves and bandanas. The shop has about 600 sq ft of shelf space and two part-time staff. About a third of her sales come from her website and Instagram. She has no photographer or designer, so she uses AI image tools to make campaign pictures quickly. She is comfortable with Instagram, Shopify and Canva, but does not want to write prompts or read code.

The persona is an assumption, not research. It should be tested with real shop owners in week two.

## Problem

AI-generated campaign images can quietly change the product. A colour drifts, a print loses part of its design, the border changes, or extra text appears. Lena catches some of this by eye, but she is busy and posts often. A wrong image can mislead shoppers and lead to disappointment or returns. Independent makers also care that their print is shown as made.

Izumi generates campaign images but does not check them against the real product. The gap is a second opinion that compares the AI image to the real photo and explains what changed.

## Product in scope

One scarf, shown in Dewi's own reference photo. It is a square, matte, plain-woven off-white cloth printed in a single bright neon pink. The design is symmetrical:
- a paisley and scrollwork border with small stars and hearts in the corners
- a large flower at the centre
- four swallows around the centre, each facing inward
- four corn cobs and scattered seeds between the birds

The border also has larger bird-like figures in each corner. The cloth has a stitched white hem. The reference photo is taken with flash on a plain brown background, so the cloth is flat and evenly lit and the fold creases barely show. No label, logo or text is visible.

## Inputs

- Reference: Dewi's photo of the real scarf
- Candidate: an AI-generated campaign image of the scarf
- A short brief describing what the image is for

## Outputs

- Findings for each criterion, each marked match, mismatch or unclear, with what was seen in the images and how sure the reviewer is
- One assessment: no_obvious_issue, issues_found or cannot_assess (a favourable assessment is still provisional)
- A human decision recorded by Lena: Keep, Reject or Need more information, stored separately from the AI recommendation

## What the reviewer compares

| Criterion | What to look for on this scarf |
| --- | --- |
| Colour | The neon pink drifting toward red, magenta, salmon or a dull pink; the off-white ground turning grey, yellow or darker |
| Pattern | A missing, added or redrawn motif (for example, three or five birds instead of four); the symmetry breaking; the border design changing; seeds, stars or hearts disappearing |
| Shape | Square proportions, the border width, the corners and hemmed edges |
| Visible branding | Not applicable to this scarf as photographed. The reviewer should still flag any text, logo or label that appears in the candidate but not in the reference. |

Texture is reported only as "looks different from the reference" with low confidence. Scene styling, such as the model, background or how the scarf is draped, is not a product change. Fold creases in the reference are not a design feature and should not be reported as a defect.

## Acceptance criteria

1. **It finds a real change and names it.** With a changed colour, pattern or shape, it says which criterion changed and describes what it sees.
2. **It does not invent problems or approvals.** With only a lighting or background change it does not call the product changed. With a blurry, hidden or missing scarf it says cannot_assess and asks for a clearer view.
3. **It never makes the decision.** Its recommendation and Lena's Keep, Reject or Need more information choice are stored separately, and only Lena can change hers.

## Test ideas for this scarf

These are ideas for the five labelled cases, not results.
- A clear match under similar lighting
- The neon pink changed to a duller or redder pink
- A bird removed, added or redrawn
- A blurred or partly hidden scarf
- The same scarf on a different background or under warmer light

## What the reviewer must never claim from a photo

- Fabric composition or material (for example, cotton or silk)
- Fit or exact size
- Authenticity, or who made the scarf
- Damage or a manufacturing defect, based on colour difference alone
- Environmental impact

## Assumptions and open questions for Dewi

1. Neon colours are hard to judge from photos. Fluorescent pink looks different depending on the camera, the exposure and the light. In the flash photo the colour looked close to the earlier photo, which is encouraging but not proof. The reviewer should still treat small colour differences as uncertain unless both images were taken under similar conditions.
2. Whose design is it? The artist is unknown (the scarf is believed to be by a Mexican artist), so permission to show the print publicly cannot be confirmed. Until it is, the reference photo and any AI-generated scarf images stay out of this public repository, in a private folder outside the repo. Public write-ups should describe the scarf in words and should not credit or name a maker. If the artist is found, ask before sharing images.
3. Reference photo: the flash photo is flatter and more even, so use it as the reference. Optional: keep the earlier no-flash photo privately as a "different light" test case.
