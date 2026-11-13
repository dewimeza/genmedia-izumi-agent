# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Product fidelity review: compare a real reference photo with an AI image.

The reviewer gives a second opinion on colour, pattern, shape and visible
branding. It never makes the decision. The human's Keep / Reject / Need more
information choice is stored under a separate key from the AI result.
"""

import io
import json
import logging
import re
import uuid

from google import genai
from google.adk.tools import ToolContext
from google.genai import types

import mediagent_kit
from utils.adk import get_user_id_from_context

from ..instructions import product_reviewer

logger = logging.getLogger(__name__)

try:  # Optional: only used for the colour hint. Reviews work without them.
    import numpy as np
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover
    np = None
    Image = None
    ImageOps = None

CRITERIA = ("colour", "pattern", "shape", "visible_branding")
STATUSES = ("match", "mismatch", "unclear")
CONFIDENCES = ("low", "medium", "high")
ASSESSMENTS = ("no_obvious_issue", "issues_found", "cannot_assess")
# Criteria that must all be "match" before the reviewer may say no_obvious_issue.
_REQUIRED_FOR_NO_ISSUE = ("colour", "pattern", "shape")
DECISIONS = {
    "keep": "Keep",
    "reject": "Reject",
    "need more information": "Need more information",
}

# A next step may only ask for a check or a better image. These words mean it
# says how to fix the image or what to decide, so it is replaced in code.
# A word list is blunt: it can also catch harmless wording, and the neutral
# replacement is safe in that case.
_NEXT_STEP_NOT_ALLOWED = re.compile(
    r"\b(keep|keeping|reject|rejecting|discard|accept|approve)\b"
    r"|\b(adjust|correct|fix|edit|tweak|tune|increase|decrease|reduce|boost"
    r"|darken|lighten|brighten|saturate|desaturate|recolou?r)\w*"
    r"|\b(better|more closely|closer) match"
    r"|\bmatch(es|ing)? the (original|reference)"
    r"|\bcloser to\b"
    r"|\bmake (it|the|them)\b",
    re.IGNORECASE,
)
_NEUTRAL_NEXT_STEP = (
    "Compare the two images side by side, or generate a new image and run "
    "the review again."
)

_RESULT_KEY = "review_result:{}"
_DECISION_KEY = "review_decision:{}"


def parse_review(raw_text: str) -> dict:
    """Validates the model's JSON and enforces the reviewer's rules.

    Raises ValueError if the text is not usable. On success the returned review
    always has one finding for each of the four criteria, in a fixed order, and
    an assessment that agrees with those findings.
    """
    text = (raw_text or "").strip()
    # Models sometimes wrap JSON in a code fence even when told not to.
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"The review was not valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("The review was not a JSON object.")

    by_criterion: dict[str, dict] = {}
    for item in data.get("findings") or []:
        if not isinstance(item, dict):
            continue
        criterion = str(item.get("criterion", "")).strip().lower()
        status = str(item.get("status", "")).strip().lower()
        confidence = str(item.get("confidence", "")).strip().lower()
        if criterion not in CRITERIA or criterion in by_criterion:
            continue
        if status not in STATUSES:
            status = "unclear"
        if confidence not in CONFIDENCES:
            confidence = "low"
        # A colour judgement from a photo is never "high": small differences in
        # neon colours depend on the camera and the light.
        if criterion == "colour" and confidence == "high":
            confidence = "medium"
        # An "unclear" finding is by definition not a confident one.
        if status == "unclear":
            confidence = "low"
        by_criterion[criterion] = {
            "criterion": criterion,
            "status": status,
            "evidence": str(item.get("evidence", "")).strip(),
            "confidence": confidence,
        }

    findings = []
    for criterion in CRITERIA:
        findings.append(
            by_criterion.get(
                criterion,
                {
                    "criterion": criterion,
                    "status": "unclear",
                    "evidence": "The reviewer did not report on this criterion.",
                    "confidence": "low",
                },
            )
        )

    statuses = {f["criterion"]: f["status"] for f in findings}
    if any(s == "mismatch" for s in statuses.values()):
        assessment = "issues_found"
    elif all(statuses[c] == "match" for c in _REQUIRED_FOR_NO_ISSUE) and (
        str(data.get("assessment", "")).strip().lower() == "no_obvious_issue"
    ):
        assessment = "no_obvious_issue"
    else:
        # No mismatch was found, but something could not be confirmed, or the
        # model did not clearly say there is no issue. Do not claim a match.
        assessment = "cannot_assess"

    next_step = str(data.get("next_step", "")).strip()
    if next_step and _NEXT_STEP_NOT_ALLOWED.search(next_step):
        # The model told the user what to fix, or whether to keep or reject.
        # That decision is the user's, so replace it with a neutral check.
        next_step = "" if assessment == "cannot_assess" else _NEUTRAL_NEXT_STEP
    if assessment == "cannot_assess" and not next_step:
        next_step = (
            "Please upload a clearer photo where the whole scarf is visible and "
            "evenly lit, then run the review again."
        )
    return {
        "assessment": assessment,
        "findings": findings,
        "summary": str(data.get("summary", "")).strip(),
        "next_step": next_step,
    }


def measure_print_colour(data: bytes) -> dict | None:
    """Measures the colour of the pink/red print and of the light ground cloth.

    This is a hint for the reviewer, not proof: lighting and cameras change
    these numbers. Returns None if the image cannot be read or the measurement
    libraries are not installed. 'print_found' is False when no print colour is
    present (for example a fully blurred or covered image).
    """
    if np is None or Image is None:
        return None
    try:
        with Image.open(io.BytesIO(data)) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((400, 400))
            rgb = np.asarray(im, dtype=np.float32) / 255.0
    except Exception:
        return None

    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(axis=2)
    delta = mx - rgb.min(axis=2)
    sat = np.where(mx > 0, delta / np.maximum(mx, 1e-6), 0.0)
    hue = np.zeros_like(mx)
    has_hue = delta > 1e-6
    is_r = has_hue & (mx == r)
    is_g = has_hue & ~is_r & (mx == g)
    is_b = has_hue & ~is_r & ~is_g
    hue[is_r] = ((g - b)[is_r] / delta[is_r]) % 6
    hue[is_g] = (b - r)[is_g] / delta[is_g] + 2
    hue[is_b] = (r - g)[is_b] / delta[is_b] + 4
    hue *= 60.0  # degrees, 0-360

    # Pink to red (about 290 to 15 degrees). Brown backgrounds start near 20.
    print_mask = (sat > 0.27) & (mx > 0.35) & ((hue >= 290) | (hue <= 15))
    # Light cloth, including cloth with a warm or cool cast; excludes the print.
    ground_mask = (sat < 0.40) & (mx > 0.60) & ~print_mask

    result = {
        "print_found": False,
        "coverage_pct": round(float(print_mask.mean()) * 100, 1),
        "ground_rgb": None,
    }
    if ground_mask.mean() > 0.05:
        result["ground_rgb"] = [
            int(round(float(c[ground_mask].mean()) * 255)) for c in (r, g, b)
        ]
    if print_mask.mean() >= 0.01:
        # Shift so pink (about 336) and red (about 4) are on one side of the
        # wrap-around before averaging.
        shifted = (hue[print_mask] + 60.0) % 360.0
        result.update(
            {
                "print_found": True,
                "hue_deg": round(float((shifted.mean() - 60.0) % 360.0), 1),
                "saturation_pct": round(float(sat[print_mask].mean()) * 100, 1),
                "brightness_pct": round(float(mx[print_mask].mean()) * 100, 1),
            }
        )
    return result


def describe_colour_measurements(reference: dict | None, candidate: dict | None) -> str:
    """Turns two measurements into a short hint for the reviewer, or ''."""
    if not reference or not candidate:
        return ""

    def line(name, m):
        if not m["print_found"]:
            return f"{name}: no clear pink/red print colour found."
        text = (
            f"{name}: print hue {m['hue_deg']} degrees, saturation "
            f"{m['saturation_pct']}%, brightness {m['brightness_pct']}%, "
            f"print covers {m['coverage_pct']}% of the picture"
        )
        if m["ground_rgb"]:
            text += f"; ground cloth RGB {tuple(m['ground_rgb'])}"
        return text + "."

    lines = [
        "Automatic colour measurements (a hint only; lighting and cameras also "
        "change these numbers):",
        line("Reference", reference),
        line("Candidate", candidate),
    ]
    if reference["print_found"] and not candidate["print_found"]:
        lines.append(
            "The candidate has far less saturated pink/red than the reference "
            "(the print may be much paler, hidden or missing)."
        )
    if reference["print_found"] and candidate["print_found"]:
        hue_gap = (candidate["hue_deg"] - reference["hue_deg"] + 180) % 360 - 180
        lines.append(
            f"Difference (candidate minus reference): print hue {hue_gap:+.1f} "
            f"degrees (positive is toward red/orange; negative is toward "
            f"purple), saturation "
            f"{candidate['saturation_pct'] - reference['saturation_pct']:+.1f} "
            f"points, brightness "
            f"{candidate['brightness_pct'] - reference['brightness_pct']:+.1f} "
            f"points, print area {candidate['coverage_pct'] - reference['coverage_pct']:+.1f} "
            f"points of the picture (a large drop means the pink became paler)."
        )
        if reference["ground_rgb"] and candidate["ground_rgb"]:
            shift = [
                c - r for c, r in zip(candidate["ground_rgb"], reference["ground_rgb"])
            ]
            lines.append(f"Ground cloth RGB change: {tuple(shift)}.")
    return "\n".join(lines)


async def _load_image(asset_service, user_id: str, file_name: str):
    """Returns (Part, raw bytes) for an image asset."""
    asset = await asset_service.get_asset_by_file_name(
        user_id=user_id, file_name=file_name
    )
    if not asset:
        raise ValueError(f"Could not find an image named '{file_name}'.")
    blob = await asset_service.get_asset_blob(asset_id=asset.id)
    if not blob or not blob.content:
        raise ValueError(f"The image '{file_name}' is empty.")
    if not str(blob.mime_type).startswith("image/"):
        raise ValueError(f"'{file_name}' is not an image ({blob.mime_type}).")
    part = types.Part.from_bytes(data=blob.content, mime_type=blob.mime_type)
    return part, blob.content


async def review_product_fidelity(
    tool_context: ToolContext,
    *,
    reference_file: str,
    candidate_file: str,
    brief: str = "",
) -> str:
    """Compares an AI-generated image against a real photo of a textile product.

    Use this when the user wants to check whether an AI-generated image still
    shows the same product as their real reference photo. It reports on colour,
    pattern, shape and visible branding. It does NOT decide whether the image
    is acceptable; only the user decides.

    Args:
        tool_context: The tool context, used to load assets.
        reference_file: File name of the uploaded real photo of the product.
        candidate_file: File name of the AI-generated image to check.
        brief: Optional short note on what the candidate image is for.

    Returns:
        A JSON string. On success it has 'status': 'success', a 'review_id',
        and a 'review' with 'assessment', 'findings', 'summary' and
        'next_step'. 'human_decision' is always null here. On failure it has
        'status': 'failure' and an 'error_message'.
    """
    logger.info(
        json.dumps(
            {
                "message": "Starting review_product_fidelity",
                "reference_file": reference_file,
                "candidate_file": candidate_file,
            }
        )
    )
    try:
        asset_service = mediagent_kit.services.aio.get_asset_service()
        user_id = get_user_id_from_context(tool_context)
        reference_part, reference_bytes = await _load_image(
            asset_service, user_id, (reference_file or "").strip()
        )
        candidate_part, candidate_bytes = await _load_image(
            asset_service, user_id, (candidate_file or "").strip()
        )

        config = mediagent_kit.services.aio.get_config()
        client = genai.Client(
            vertexai=True,
            project=config.google_cloud_project,
            # Gemini text models are served from "global".
            location=config.google_cloud_location or "global",
        )
        model = config.models.get("text", {}).get("default", "gemini-3.7-flash")

        contents = [
            "REFERENCE: a real photo of the product.",
            reference_part,
            "CANDIDATE: the AI-generated image to check.",
            candidate_part,
        ]
        if brief and brief.strip():
            contents.append(f"What the candidate image is for: {brief.strip()}")
        colour_hint = describe_colour_measurements(
            measure_print_colour(reference_bytes),
            measure_print_colour(candidate_bytes),
        )
        if colour_hint:
            contents.append(colour_hint)

        response = await client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=product_reviewer.INSTRUCTION,
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        review = parse_review(response.text)
    except Exception as e:
        logger.error(f"review_product_fidelity failed: {e}")
        return json.dumps({"status": "failure", "error_message": str(e)})

    review_id = uuid.uuid4().hex[:8]
    record = {
        "reference_file": reference_file,
        "candidate_file": candidate_file,
        "review": review,
    }
    tool_context.state[_RESULT_KEY.format(review_id)] = record
    logger.info(f"Stored review {review_id}: {review['assessment']}")
    return json.dumps(
        {
            "status": "success",
            "review_id": review_id,
            "review": review,
            "human_decision": None,
        }
    )


async def record_review_decision(
    tool_context: ToolContext,
    *,
    review_id: str,
    decision: str,
    note: str = "",
) -> str:
    """Records the user's own decision about a reviewed image.

    Call this ONLY after the user has said, in their own words, whether to
    keep the image, reject it, or that they need more information. Never choose
    for them and never infer the decision from the AI review. The decision is
    stored separately from the review and does not change it.

    Args:
        tool_context: The tool context, used to store the decision.
        review_id: The 'review_id' returned by review_product_fidelity.
        decision: One of "Keep", "Reject" or "Need more information".
        note: Optional reason, in the user's words.

    Returns:
        A JSON string with 'status' 'success' and the stored 'human_decision',
        or 'status' 'failure' and an 'error_message'.
    """
    normalized = DECISIONS.get((decision or "").strip().lower())
    if not normalized:
        return json.dumps(
            {
                "status": "failure",
                "error_message": (
                    "Decision must be one of: Keep, Reject, Need more information."
                ),
            }
        )
    review_id = (review_id or "").strip()
    if _RESULT_KEY.format(review_id) not in tool_context.state:
        return json.dumps(
            {
                "status": "failure",
                "error_message": f"No review found with id '{review_id}'.",
            }
        )
    stored = {"decision": normalized, "note": (note or "").strip()}
    tool_context.state[_DECISION_KEY.format(review_id)] = stored
    logger.info(f"Recorded decision for review {review_id}: {normalized}")
    return json.dumps(
        {"status": "success", "review_id": review_id, "human_decision": stored}
    )
