from __future__ import annotations

from copy import deepcopy

from conftest import import_file


def validator(skill):
    module = import_file("validate_brief_contracts", skill / "scripts" / "validate_brief.py")
    return module.BriefValidator()


def decision_structure():
    return {
        "actor": "Planner", "trigger": "A plan is due", "choices": "Allocation",
        "decision_time_information": "Known inputs", "stakes": "Modeled cost",
        "frictions": "Capacity", "mechanism": "Allocation changes service",
        "trade_off": "Cost versus coverage", "counterfactual": "Another feasible plan",
        "model_mapping_summary": "The allocation is a decision",
        "evidence_status_summary": "Inputs are assumptions",
        "boundaries_summary": "Synthetic setting",
    }


def gates(status="pass"):
    return {
        name: {"status": status, "reason": "The supplied specification supports this status."}
        for name in ("actor", "timing", "information", "behavior", "constraints", "objective")
    }


def audit(status="pass"):
    return {"status": status, "findings": ["Explicitly assessed."], "required_actions": []}


def valid_v1():
    return {
        "schema_version": "1.0", "mode": "create", "title": "Advance allocation",
        "domain": "OR", "model_supplied": False,
        "diagnosis_or_brief": "A bounded allocation problem.",
        "narrative": "A planner allocates capacity before demand.",
        "decision_structure": decision_structure(), "consistency_gates": gates(),
        "eligible": True, "model_mapping": [], "claims": [],
        "boundaries": ["Synthetic setting."],
        "primary_remaining_weakness": "Calibration is unavailable.",
        "mode_result": {"business_problem": "How should capacity be allocated?"},
    }


def valid_v2():
    return {
        "schema_version": "2.0", "mode": "create", "title": "Advance allocation",
        "domain": "OR", "model_supplied": True,
        "input_readiness": {"stage": 2, "basis": "A precise model is supplied.", "missing_information": [], "maturity_ceiling": 2},
        "diagnosis_or_brief": "A bounded allocation problem.",
        "narrative": "A planner allocates capacity before demand.",
        "decision_structure": decision_structure(), "consistency_gates": gates(),
        "eligibility_status": "eligible", "fidelity_audit": audit(),
        "managerial_framing_audit": audit(),
        "scholarly_positioning_audit": audit("not_assessed"),
        "evidence_audit": audit(), "prose_audit": audit(),
        "model_mapping": [{
            "model_object": "x", "model_role": "decision_variable",
            "business_meaning": "capacity allocated", "decision_time_status": "chosen",
            "timing": "before demand", "units": "units", "horizon": "one period",
            "fidelity_note": "Demand is not chosen.",
        }],
        "claims": [], "boundaries": ["Synthetic setting."],
        "primary_remaining_weakness": "Calibration is unavailable.",
        "mode_result": {
            "readiness": "Stage 2 model-grounded framing.", "setting": "Synthetic service network.",
            "managerial_question": "How should capacity be allocated?",
            "significance": "Capacity is scarce.", "mechanism": "Allocation limits service.",
            "structural_tension": "Coverage in one region reduces coverage elsewhere.",
            "evidence_needs": [], "counterconditions": ["Demand remains within modeled scope."],
        },
    }


def test_business_brief_v1_remains_valid(skill) -> None:
    assert validator(skill).validate(valid_v1()) == []


def test_business_brief_v2_validates(skill) -> None:
    assert validator(skill).validate(valid_v2()) == []


def test_business_brief_v2_gate_status_determines_eligibility(skill) -> None:
    brief = deepcopy(valid_v2())
    brief["consistency_gates"]["information"]["status"] = "unknown"
    errors = validator(skill).validate(brief)
    assert any("eligibility_status" in error and "not_assessed" in error for error in errors)


def test_business_brief_v2_rejects_v1_mode_contract(skill) -> None:
    brief = deepcopy(valid_v2())
    brief["mode_result"] = {"business_problem": "Legacy field."}
    assert any("mode_result" in error for error in validator(skill).validate(brief))
