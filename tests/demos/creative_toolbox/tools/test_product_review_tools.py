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
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from demos.backend.creative_toolbox.tools import product_review_tools as prt


def _finding(criterion, status="match", confidence="high", evidence="ok"):
    return {
        "criterion": criterion,
        "status": status,
        "evidence": evidence,
        "confidence": confidence,
    }


def _model_json(statuses=None, assessment="no_obvious_issue", **extra):
    statuses = statuses or {}
    data = {
        "assessment": assessment,
        "findings": [
            _finding(c, statuses.get(c, "match")) for c in prt.CRITERIA
        ],
        "summary": "Looks the same.",
        "next_step": "",
    }
    data.update(extra)
    return json.dumps(data)


# ---- parse_review: the rules the reviewer must follow ---------------------


def test_clean_match_is_no_obvious_issue():
    review = prt.parse_review(_model_json())
    assert review["assessment"] == "no_obvious_issue"
    assert [f["criterion"] for f in review["findings"]] == list(prt.CRITERIA)


def test_any_mismatch_forces_issues_found_even_if_model_says_ok():
    raw = _model_json({"pattern": "mismatch"}, assessment="no_obvious_issue")
    assert prt.parse_review(raw)["assessment"] == "issues_found"


def test_unclear_core_criterion_never_counts_as_no_issue():
    raw = _model_json({"colour": "unclear"}, assessment="no_obvious_issue")
    assert prt.parse_review(raw)["assessment"] == "cannot_assess"


def test_unclear_branding_alone_does_not_block_no_issue():
    raw = _model_json({"visible_branding": "unclear"})
    assert prt.parse_review(raw)["assessment"] == "no_obvious_issue"


def test_issues_found_without_any_mismatch_is_not_trusted():
    raw = _model_json(assessment="issues_found")
    assert prt.parse_review(raw)["assessment"] == "cannot_assess"


def test_model_cannot_assess_is_kept():
    raw = _model_json(assessment="cannot_assess")
    assert prt.parse_review(raw)["assessment"] == "cannot_assess"


def test_missing_criteria_are_filled_as_unclear_low_confidence():
    raw = json.dumps(
        {"assessment": "no_obvious_issue", "findings": [_finding("colour")]}
    )
    review = prt.parse_review(raw)
    by = {f["criterion"]: f for f in review["findings"]}
    assert by["pattern"]["status"] == "unclear"
    assert by["pattern"]["confidence"] == "low"
    assert review["assessment"] == "cannot_assess"


def test_bad_values_are_normalised_and_duplicates_ignored():
    raw = json.dumps(
        {
            "assessment": "no_obvious_issue",
            "findings": [
                _finding("COLOUR", status="Match", confidence="HIGH"),
                _finding("colour", status="mismatch"),  # duplicate, ignored
                _finding("pattern", status="great", confidence="sure"),
                _finding("texture"),  # not a criterion, ignored
            ],
        }
    )
    by = {f["criterion"]: f for f in prt.parse_review(raw)["findings"]}
    assert by["colour"]["status"] == "match"
    assert by["colour"]["confidence"] == "medium"  # colour is capped below high
    assert by["pattern"]["status"] == "unclear"
    assert by["pattern"]["confidence"] == "low"
    assert "texture" not in by


def test_json_in_a_code_fence_is_accepted():
    fenced = "```json\n" + _model_json() + "\n```"
    assert prt.parse_review(fenced)["assessment"] == "no_obvious_issue"


@pytest.mark.parametrize("raw", ["", "not json", "[1, 2]", "null"])
def test_unusable_output_raises(raw):
    with pytest.raises(ValueError):
        prt.parse_review(raw)


# ---- the tools ------------------------------------------------------------


class _State(dict):
    """Stands in for ADK session state (supports `in`, get, item set)."""


@pytest.fixture
def tool_context():
    return SimpleNamespace(state=_State())


def _asset_service(files):
    """files: {file_name: (bytes, mime)} -> a mock asset service."""
    service = MagicMock()

    async def get_asset_by_file_name(user_id, file_name):
        if file_name not in files:
            return None
        return SimpleNamespace(id=file_name)

    async def get_asset_blob(asset_id):
        content, mime = files[asset_id]
        return SimpleNamespace(content=content, mime_type=mime)

    service.get_asset_by_file_name = AsyncMock(side_effect=get_asset_by_file_name)
    service.get_asset_blob = AsyncMock(side_effect=get_asset_blob)
    return service


def _patches(asset_service, model_text):
    client = MagicMock()
    client.aio.models.generate_content = AsyncMock(
        return_value=SimpleNamespace(text=model_text)
    )
    config = SimpleNamespace(
        google_cloud_project="test-project",
        google_cloud_location="global",
        models={"text": {"default": "test-model"}},
    )
    return client, [
        patch(
            "mediagent_kit.services.aio.get_asset_service",
            return_value=asset_service,
        ),
        patch("mediagent_kit.services.aio.get_config", return_value=config),
        patch.object(prt.genai, "Client", return_value=client),
        patch.object(prt, "get_user_id_from_context", return_value="user-1"),
    ]


async def _run_review(tool_context, files, model_text, **kwargs):
    client, patches = _patches(_asset_service(files), model_text)
    for p in patches:
        p.start()
    try:
        result = await prt.review_product_fidelity(
            tool_context,
            reference_file="ref.png",
            candidate_file="cand.png",
            **kwargs,
        )
    finally:
        for p in patches:
            p.stop()
    return json.loads(result), client


IMAGES = {
    "ref.png": (b"ref-bytes", "image/png"),
    "cand.png": (b"cand-bytes", "image/png"),
}


async def test_review_success_stores_result_and_leaves_decision_empty(tool_context):
    out, client = await _run_review(
        tool_context, IMAGES, _model_json({"pattern": "mismatch"}), brief="Spring post"
    )
    assert out["status"] == "success"
    assert out["human_decision"] is None
    assert out["review"]["assessment"] == "issues_found"

    key = f"review_result:{out['review_id']}"
    assert key in tool_context.state
    assert tool_context.state[key]["review"] == out["review"]
    # Nothing is decided for the user.
    assert not [k for k in tool_context.state if k.startswith("review_decision:")]

    call = client.aio.models.generate_content.call_args.kwargs
    assert call["model"] == "test-model"
    parts = call["contents"]
    assert sum(1 for p in parts if hasattr(p, "inline_data") and p.inline_data) == 2
    assert any(isinstance(p, str) and "Spring post" in p for p in parts)


async def test_review_fails_cleanly_when_an_image_is_missing(tool_context):
    out, client = await _run_review(
        tool_context, {"ref.png": IMAGES["ref.png"]}, _model_json()
    )
    assert out["status"] == "failure"
    assert "cand.png" in out["error_message"]
    assert not tool_context.state
    client.aio.models.generate_content.assert_not_called()


async def test_review_rejects_a_non_image_file(tool_context):
    files = {**IMAGES, "cand.png": (b"%PDF", "application/pdf")}
    out, _ = await _run_review(tool_context, files, _model_json())
    assert out["status"] == "failure"
    assert "not an image" in out["error_message"]


async def test_review_fails_cleanly_on_bad_model_output(tool_context):
    out, _ = await _run_review(tool_context, IMAGES, "I think it looks fine!")
    assert out["status"] == "failure"
    assert not tool_context.state


async def test_decision_is_stored_separately_and_review_is_unchanged(tool_context):
    out, _ = await _run_review(tool_context, IMAGES, _model_json())
    review_id = out["review_id"]
    before = json.dumps(tool_context.state[f"review_result:{review_id}"])

    result = json.loads(
        await prt.record_review_decision(
            tool_context,
            review_id=review_id,
            decision="  reject ",
            note="Pink is too dull",
        )
    )
    assert result["status"] == "success"
    assert result["human_decision"] == {
        "decision": "Reject",
        "note": "Pink is too dull",
    }
    assert tool_context.state[f"review_decision:{review_id}"]["decision"] == "Reject"
    assert json.dumps(tool_context.state[f"review_result:{review_id}"]) == before


@pytest.mark.parametrize("decision", ["", "approve", "maybe", "no_obvious_issue"])
async def test_invalid_decision_is_refused(tool_context, decision):
    tool_context.state["review_result:abc"] = {"review": {}}
    result = json.loads(
        await prt.record_review_decision(
            tool_context, review_id="abc", decision=decision
        )
    )
    assert result["status"] == "failure"
    assert "review_decision:abc" not in tool_context.state


async def test_decision_for_unknown_review_is_refused(tool_context):
    result = json.loads(
        await prt.record_review_decision(
            tool_context, review_id="nope", decision="Keep"
        )
    )
    assert result["status"] == "failure"
    assert not tool_context.state


def test_tools_are_registered_on_the_root_agent():
    from demos.backend.creative_toolbox.agent import root_agent

    names = {getattr(t, "name", None) or getattr(t, "__name__", "") for t in root_agent.tools}
    assert "review_product_fidelity" in names
    assert "record_review_decision" in names


def test_prompts_ask_for_cautious_wording_and_confidence():
    from demos.backend.creative_toolbox.instructions import product_reviewer, root

    assert "appears to match" in product_reviewer.INSTRUCTION
    assert "precisely" in product_reviewer.INSTRUCTION  # listed as a banned word
    assert "appears to match" in root.INSTRUCTION
    assert "confidence" in root.INSTRUCTION


# ---- confidence rules, default next step, colour measurement -------------


def _png(ground, print_rgb, print_share=0.3, size=120):
    """A plain 'cloth' with a block of print colour, as PNG bytes."""
    import io

    from PIL import Image

    im = Image.new("RGB", (size, size), ground)
    block = int(size * (print_share**0.5))
    for x in range(block):
        for y in range(block):
            im.putpixel((x + 10, y + 10), print_rgb)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


PINK = (255, 20, 147)
RED_PINK = (255, 40, 80)
GROUND = (225, 220, 223)


def test_colour_confidence_is_never_high():
    raw = json.dumps(
        {
            "assessment": "no_obvious_issue",
            "findings": [
                _finding("colour", confidence="high"),
                _finding("pattern", confidence="high"),
                _finding("shape"),
                _finding("visible_branding"),
            ],
        }
    )
    by = {f["criterion"]: f for f in prt.parse_review(raw)["findings"]}
    assert by["colour"]["confidence"] == "medium"
    assert by["pattern"]["confidence"] == "high"


def test_unclear_finding_has_low_confidence():
    raw = _model_json({"pattern": "unclear"})
    by = {f["criterion"]: f for f in prt.parse_review(raw)["findings"]}
    assert by["pattern"]["confidence"] == "low"


def test_cannot_assess_always_asks_for_a_clearer_photo():
    review = prt.parse_review(_model_json({"shape": "unclear"}, next_step=""))
    assert review["assessment"] == "cannot_assess"
    assert "clearer" in review["next_step"]


def test_a_given_next_step_is_kept():
    raw = _model_json({"shape": "unclear"}, next_step="Retake it in daylight.")
    assert prt.parse_review(raw)["next_step"] == "Retake it in daylight."


@pytest.mark.parametrize(
    "advice",
    [
        "Regenerate the image to better match the original pink print colour.",
        "Adjust the colour to match the reference.",
        "Make it less red.",
        "Reject this image.",
        "Keep this one.",
        "Shift the hue closer to the reference.",
    ],
)
def test_next_step_with_fix_or_decision_is_replaced(advice):
    raw = _model_json({"colour": "mismatch"}, next_step=advice)
    review = prt.parse_review(raw)
    assert review["next_step"] == prt._NEUTRAL_NEXT_STEP


def test_fix_advice_on_cannot_assess_becomes_clearer_photo_request():
    raw = _model_json({"shape": "unclear"}, next_step="Fix the colour first.")
    review = prt.parse_review(raw)
    assert review["assessment"] == "cannot_assess"
    assert "clearer" in review["next_step"]


@pytest.mark.parametrize(
    "check",
    [
        "Compare the print colours side by side under consistent lighting.",
        "Generate a new image and run the review again.",
        "Retake the photo in even daylight.",
        "Take a closer look at the lower right corner.",
    ],
)
def test_checking_next_steps_are_kept(check):
    raw = _model_json({"colour": "mismatch"}, next_step=check)
    assert prt.parse_review(raw)["next_step"] == check


def test_measure_finds_print_and_ground():
    m = prt.measure_print_colour(_png(GROUND, PINK))
    assert m["print_found"] is True
    assert 320 < m["hue_deg"] < 335
    assert m["saturation_pct"] > 80
    assert m["ground_rgb"] == list(GROUND)


def test_measure_sees_a_redder_print():
    pink = prt.measure_print_colour(_png(GROUND, PINK))
    red = prt.measure_print_colour(_png(GROUND, RED_PINK))
    gap = (red["hue_deg"] - pink["hue_deg"] + 180) % 360 - 180
    assert gap > 15  # positive means toward red


def test_measure_reports_no_print_on_a_plain_cloth():
    m = prt.measure_print_colour(_png(GROUND, GROUND))
    assert m["print_found"] is False


@pytest.mark.parametrize("data", [b"", b"not an image"])
def test_measure_returns_none_for_unreadable_data(data):
    assert prt.measure_print_colour(data) is None


def test_description_reports_differences_and_the_lighting_clue():
    ref = prt.measure_print_colour(_png(GROUND, PINK))
    warm_ground = (245, 212, 170)
    cand = prt.measure_print_colour(_png(warm_ground, RED_PINK))
    text = prt.describe_colour_measurements(ref, cand)
    assert "Difference (candidate minus reference)" in text
    assert "Ground cloth RGB change" in text
    assert "hint only" in text


def test_description_is_empty_without_both_measurements():
    ref = prt.measure_print_colour(_png(GROUND, PINK))
    assert prt.describe_colour_measurements(ref, None) == ""
    assert prt.describe_colour_measurements(None, ref) == ""


async def test_review_passes_the_colour_hint_to_the_model(tool_context):
    files = {
        "ref.png": (_png(GROUND, PINK), "image/png"),
        "cand.png": (_png(GROUND, RED_PINK), "image/png"),
    }
    out, client = await _run_review(tool_context, files, _model_json())
    assert out["status"] == "success"
    contents = client.aio.models.generate_content.call_args.kwargs["contents"]
    hints = [c for c in contents if isinstance(c, str) and "colour measurements" in c]
    assert len(hints) == 1
    assert "print hue" in hints[0]


def test_prompt_tells_the_reviewer_how_to_use_the_measurements():
    from demos.backend.creative_toolbox.instructions import product_reviewer

    text = product_reviewer.INSTRUCTION
    assert "Colour confidence is never" in text
    assert "ground cloth" in text
    assert "5 degrees" in text


def test_prompt_keeps_next_step_to_checking_not_fixing():
    from demos.backend.creative_toolbox.instructions import product_reviewer

    assert "Never tell the user how to edit" in product_reviewer.INSTRUCTION
    assert "never tell them to keep" in product_reviewer.INSTRUCTION
    assert "Do not say what the new image should change" in product_reviewer.INSTRUCTION
