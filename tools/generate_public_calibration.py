#!/usr/bin/env python3
"""Generate the public synthetic v3 calibration suite deterministically."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evals" / "calibration"
ANALOGUES = BASE / "synthetic-analogues"
CONTRASTS = BASE / "contrast-cases"
MANIFEST = BASE / "public-metadata" / "synthetic-suite-manifest.json"
SCHEMA_VERSION = "3.0.0"

CONSTRUCTS = (
    "actor",
    "timing",
    "information",
    "objective",
    "mechanism",
    "trade_off",
    "unsupported_hype",
    "contribution",
    "boundaries",
    "verbosity",
)

BASES: tuple[dict[str, Any], ...] = (
    {"key":"om-dev","domain":"OM","split":"development","function":"business_problem","actor":"a regional inventory planner","trigger":"before the weekly allocation cutoff","decision":"allocates a fixed stock across service zones","info":"current stock, zone cost coefficients, and demand distributions","uncertainty":"regional orders","objective":"minimize expected shortage and leftover cost","constraint":"stock cannot be transferred after orders arrive","mechanism":"Pre-positioning determines which realized orders can be served in each zone","tradeoff":"Concentration pools scarce stock, while broader coverage protects more zones","boundary":"The claim concerns one-period allocation under the supplied distributions, not live deployment","contribution":"The study clarifies when pre-positioning coverage is worth the loss of inventory concentration"},
    {"key":"is-dev","domain":"IS","split":"development","function":"business_problem","actor":"a platform access manager","trigger":"when a new account requests admission","decision":"sets one threshold on a noisy risk score","info":"the score distribution and payoff weights","uncertainty":"the account's latent benign or malicious type","objective":"maximize expected platform value net of malicious harm and rejection loss","constraint":"true account type is not observed at admission","mechanism":"The threshold changes false rejection and harmful admission rates through the score distributions","tradeoff":"A stricter threshold blocks more harmful accounts but rejects more benign participants","boundary":"The result is conditional on the assumed score distributions and does not establish field effectiveness","contribution":"The analysis identifies when a common score rule should become more selective"},
    {"key":"or-dev","domain":"OR","split":"development","function":"model_setting","actor":"a dispatch planner","trigger":"when same-day routes must be released","decision":"selects a feasible routing plan before the dispatch deadline","info":"orders, travel times, vehicle capacities, and the release deadline","uncertainty":"none in the stated deterministic instance","objective":"minimize routing cost while meeting service constraints","constraint":"an optimality certificate arriving after release cannot guide the decision","mechanism":"The algorithm trades additional search time for better incumbents and stronger bounds","tradeoff":"Longer search may improve cost but can make the certified plan operationally late","boundary":"Computational value is limited to tested instances, hardware, and the specified deadline","contribution":"The study connects solution quality and certificate timing to the actual release decision"},
    {"key":"mgmt-dev","domain":"MGMT","split":"development","function":"phenomenon_motivation","actor":"a business-unit leader","trigger":"when a proven practice is transferred to a different unit","decision":"chooses whether and how to adapt the practice","info":"local routines, resource limits, and observed prior outcomes","uncertainty":"whether the practice's mechanism survives the new context","objective":"improve unit performance without disrupting complementary routines","constraint":"the leader cannot assume that surface similarity preserves the causal mechanism","mechanism":"Transfer succeeds when the receiving unit recreates the complementary routines that produced the original effect","tradeoff":"Closer imitation preserves tested elements but may fit the receiving unit poorly","boundary":"The argument applies to transfers with observable routines and does not establish universal causality","contribution":"The study shifts attention from copying practices to preserving their enabling mechanism"},
    {"key":"om-val","domain":"OM","split":"validation","function":"model_setting","actor":"an assortment planner","trigger":"before products are displayed for the next selling period","decision":"selects products under a fixed display-slot limit","info":"product margins and a specified Markov substitution matrix","uncertainty":"the arriving customer's initial product and subsequent substitution path","objective":"maximize expected assortment revenue","constraint":"display capacity is distinct from inventory and fulfillment capacity","mechanism":"When a preferred product is absent, the stated transition matrix redirects demand among displayed alternatives or to exit","tradeoff":"Adding variety captures more first choices but consumes slots that could support stronger substitution paths","boundary":"The model represents within-assortment Markov substitution, not nearest-store search or stockout dynamics","contribution":"The analysis identifies which transition patterns make a scarce slot most valuable"},
    {"key":"is-val","domain":"IS","split":"validation","function":"research_opportunity","actor":"a moderation policy owner","trigger":"before classifying a new content item","decision":"sets a review threshold using privacy-permitted signals","info":"approved signal features, error costs, and reviewer capacity","uncertainty":"the item's harmfulness and classifier error","objective":"minimize expected moderation harm and review cost","constraint":"privacy-restricted attributes are unavailable unless consent and policy permit their use","mechanism":"The threshold routes uncertain items to review and changes false-positive and false-negative exposure","tradeoff":"More review reduces classification harm but consumes scarce reviewer attention","boundary":"The proposal does not treat revenue as welfare or assume unrestricted access to sensitive data","contribution":"The study asks how privacy limits alter the value of selective human review"},
    {"key":"or-val","domain":"OR","split":"validation","function":"model_setting","actor":"a capacity planner","trigger":"before uncertain demand is realized","decision":"chooses first-stage capacity and a recourse policy","info":"capacity costs and the demand distribution","uncertainty":"future demand by market","objective":"minimize capacity, recourse, and unmet-demand cost","constraint":"recourse actions occur only after demand is observed and must respect installed capacity","mechanism":"First-stage capacity changes the feasible and costly adjustments available after demand realization","tradeoff":"More advance capacity is expensive but reduces shortage and emergency recourse exposure","boundary":"The findings depend on the modeled distribution and recourse set rather than perfect demand foresight","contribution":"The analysis isolates when flexible recourse substitutes for advance capacity"},
    {"key":"mgmt-val","domain":"MGMT","split":"validation","function":"contribution","actor":"a multiunit firm's senior team","trigger":"when local units propose exceptions to a common policy","decision":"chooses how much discretion to delegate","info":"unit conditions, coordination needs, and observable performance signals","uncertainty":"whether local adaptation improves fit or conceals self-serving behavior","objective":"balance local responsiveness with cross-unit coordination","constraint":"headquarters cannot directly observe every local motive or consequence","mechanism":"Delegation improves local fit while common rules limit coordination and agency losses","tradeoff":"Greater discretion supports adaptation but weakens consistency and oversight","boundary":"The theory concerns multiunit settings with partial observability and does not imply that decentralization always improves performance","contribution":"The study explains delegation as a response to joint adaptation and observability conditions rather than as a generic best practice"},
    {"key":"om-hold","domain":"OM","split":"holdout","function":"managerial_implications","actor":"a service-operations manager","trigger":"before staffing a time-limited service window","decision":"sets staffing for the window","info":"arrival-rate estimates, service-time estimates, wage cost, and delay penalties","uncertainty":"customer arrivals and service durations","objective":"minimize expected staffing and delay cost","constraint":"staff cannot be added after the cutoff in the stated model","mechanism":"Staffing changes congestion, waiting, and abandonment through available service capacity","tradeoff":"Extra staff raises labor cost but reduces delay and abandonment exposure","boundary":"The implication applies near the studied demand and service ranges, not to unobserved demand shocks","contribution":"The study identifies the conditions under which one additional server has the greatest operational value"},
    {"key":"is-hold","domain":"IS","split":"holdout","function":"managerial_implications","actor":"a ranking-system owner","trigger":"before publishing a recommendation list","decision":"selects a ranking rule subject to an exposure constraint","info":"predicted relevance, the approved group indicator, and the exposure requirement","uncertainty":"future engagement and prediction error","objective":"maximize expected relevance subject to the stated exposure constraint","constraint":"the system cannot use attributes that are unavailable or prohibited at ranking time","mechanism":"The constraint reallocates exposure across eligible items and can displace higher predicted-relevance positions","tradeoff":"Tighter exposure balance can improve representation while reducing predicted relevance under the model","boundary":"The result concerns the specified exposure metric and does not establish broader social welfare","contribution":"The study shows when the operational cost of the exposure requirement is concentrated in a few ranking positions"},
    {"key":"or-hold","domain":"OR","split":"holdout","function":"managerial_implications","actor":"a production scheduler","trigger":"when a schedule must be released for the next shift","decision":"chooses between an exact solver incumbent and a heuristic schedule","info":"jobs, processing times, machine availability, costs, and the release deadline","uncertainty":"none in the scheduling model","objective":"minimize tardiness and setup cost","constraint":"only solutions available before release can affect operations","mechanism":"The exact method may improve bounds and incumbents with time, while the heuristic returns feasible schedules quickly without a certificate","tradeoff":"Waiting can improve objective quality but risks missing the release time","boundary":"Operational value requires a documented pathway from timely schedules to the stated planning outcomes","contribution":"The study distinguishes mathematical solution quality from the value of having a usable schedule on time"},
    {"key":"mgmt-hold","domain":"MGMT","split":"holdout","function":"research_opportunity","actor":"a project portfolio committee","trigger":"when several uncertain initiatives compete for funding","decision":"selects projects and review milestones","info":"current forecasts, strategic dependencies, and available budget","uncertainty":"technical progress and later commercial evidence","objective":"build a valuable portfolio while limiting irreversible exposure","constraint":"the committee cannot use later milestone evidence in the initial selection","mechanism":"Staged commitments preserve the option to stop weak projects after informative milestones","tradeoff":"Early commitment accelerates promising projects but reduces the ability to redirect funds after learning","boundary":"The argument concerns settings with informative milestones and partially reversible commitments","contribution":"The study reframes portfolio selection as the joint design of initial commitments and later learning opportunities"}
)


def case_id(label: str) -> str:
    return "C" + hashlib.sha256(label.encode("utf-8")).hexdigest()[:16]


def applicability(function: str, domain: str) -> dict[str, str]:
    scholarly = "required" if function in {"research_opportunity", "contribution"} else (
        "not_applicable" if function in {"model_setting", "managerial_implications"} else "optional"
    )
    managerial = "required" if function in {"business_problem", "model_setting", "managerial_implications"} else "optional"
    return {
        "fidelity": "optional" if domain == "MGMT" else "required",
        "managerial_framing": managerial,
        "scholarly_positioning": scholarly,
        "evidence_discipline": "required",
        "prose_clarity": "required",
    }


def render(base: dict[str, str], variant: str | None = None, quality: str = "positive") -> str:
    actor = base["actor"]
    timing = f"{base['trigger']}, before {base['uncertainty']} is known"
    info = base["info"]
    objective = base["objective"]
    mechanism = base["mechanism"] + "."
    tradeoff = base["tradeoff"] + "."
    boundary = base["boundary"] + "."
    contribution = base["contribution"] + "."
    if quality == "intermediate":
        mechanism = "Several operational considerations connect the decision to later outcomes, but their relationship is not specified."
        tradeoff = "The decision is important and involves competing considerations that require further analysis."
        boundary = "The scope of the resulting claim remains to be established."
    if variant == "actor":
        actor = "an outside observer who does not control the decision"
    elif variant == "timing":
        timing = f"after {base['uncertainty']} has been fully observed"
    elif variant == "information":
        info = info + ", the future realized outcome, and any latent type"
    elif variant == "objective":
        objective = "maximize a different social-welfare objective that the model does not measure"
    elif variant == "mechanism":
        mechanism = "The setting contains several relevant operational details, but the passage does not connect the choice to the outcome."
    elif variant == "trade_off":
        tradeoff = "The decision should improve every relevant outcome without a meaningful sacrifice."
    elif variant == "unsupported_hype":
        boundary = "The approach will transform the industry, guarantee profit growth, and work in every market."
    elif variant == "contribution":
        contribution = "The contribution is that the same topic has not previously been studied in this particular context."
    elif variant == "boundaries":
        boundary = "The analysis therefore provides a broadly useful conclusion for managers."
    opening = f"{timing}, {actor} {base['decision']} using {info}."
    passage = " ".join([
        opening,
        f"The stated objective is to {objective}, subject to the condition that {base['constraint']}.",
        mechanism,
        tradeoff,
        boundary,
        contribution,
    ])
    if quality == "negative_actor":
        passage = passage.replace(base["actor"], "an outside observer who cannot make the decision", 1)
    elif quality == "negative_hype":
        passage = passage.replace(boundary, "The universally superior policy will transform the market and guarantee better performance.")
    if variant == "verbosity":
        passage += " " + " ".join([
            "This decision is important for organizations because organizations routinely face decisions of this general kind.",
            "The issue has practical relevance, managerial relevance, and broader relevance for decision makers.",
            "Careful attention to the decision can therefore help managers think carefully about making the decision.",
        ])
    return passage


def generator_record(base: dict[str, str], identifier: str, passage: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": identifier,
        "domain": base["domain"],
        "anonymized_passage": passage,
        "passage_function": base["function"],
        "context": {
            "model_or_study_facts": [base["constraint"], base["uncertainty"]],
            "actor": base["actor"],
            "decisions": [base["decision"]],
            "objective": base["objective"],
            "timing": base["trigger"],
            "decision_time_information": [base["info"]],
            "constraints": [base["constraint"]],
            "mechanism": base["mechanism"],
            "supplied_evidence": ["Synthetic illustration; no external empirical evidence supplied."]
        },
        "intended_audience": "business and research readers",
        "requested_evaluation_profile": "standard"
    }


def contrast_expectation(construct: str) -> tuple[dict[str, int], dict[str, int], str | None, int]:
    if construct in {"actor", "timing", "information", "objective"}:
        failure = {
            "actor": "actor_gate_failure", "timing": "timing_gate_failure",
            "information": "information_gate_failure", "objective": "objective_gate_failure",
        }[construct]
        return {"fidelity": 9}, {"prose_clarity": 1}, failure, 9
    mapping = {
        "mechanism": ({"managerial_framing": 5}, {"evidence_discipline": 1, "prose_clarity": 1}, None, 5),
        "trade_off": ({"managerial_framing": 4}, {"fidelity": 1, "evidence_discipline": 1}, None, 4),
        "unsupported_hype": ({"evidence_discipline": 4}, {"fidelity": 1}, None, 4),
        "contribution": ({"scholarly_positioning": 5}, {"fidelity": 1, "evidence_discipline": 1}, None, 5),
        "boundaries": ({"evidence_discipline": 3}, {"fidelity": 1, "prose_clarity": 1}, None, 3),
        "verbosity": ({"prose_clarity": 2}, {"fidelity": 1, "evidence_discipline": 1}, None, 2),
    }
    return mapping[construct]


def judge_record(
    base: dict[str, str], identifier: str, group: str, origin: str,
    quality: str, contrast: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": identifier,
        "domain": base["domain"],
        "passage_function": base["function"],
        "group": group,
        "control_origin": origin,
        "split": base["split"],
        "applicable_categories": applicability(base["function"], base["domain"]),
        "gold_fidelity_facts": [base["actor"], base["decision"], base["objective"], base["constraint"]],
        "acceptable_interpretations": ["Equivalent concise wording is acceptable.", "Explicit rubric labels are unnecessary."],
        "prohibited_model_changes": ["Do not add unavailable future facts.", "Do not replace the stated objective."],
        "evidence_boundaries": ["Synthetic case only.", "No field outcome is supplied."],
        "expected_strengths": ["Concrete decision structure.", "Bounded claim."],
        "expected_weaknesses": [] if quality == "high" else ["Incomplete mechanism and scope."],
        "case_specific_anchors": {"high": "Faithful and functionally complete.", "medium": "Competent but incomplete.", "low": "Material defect or generic framing."},
        "expert_quality_level": quality,
        "expert_review_status": "pending",
        "contrast": contrast,
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def build_records() -> tuple[list[tuple[Path, dict[str, Any]]], dict[str, Any]]:
    files: list[tuple[Path, dict[str, Any]]] = []
    manifest_records: list[dict[str, Any]] = []
    for base in BASES:
        positive_id = case_id(base["key"] + ":positive")
        positive = generator_record(base, positive_id, render(base))
        positive_judge = judge_record(base, positive_id, "positive", "synthetic_analogue", "high")
        intermediate_id = case_id(base["key"] + ":intermediate")
        intermediate = generator_record(base, intermediate_id, render(base, quality="intermediate"))
        intermediate_judge = judge_record(base, intermediate_id, "intermediate", "synthetic_analogue", "medium")
        for identifier, generator, judge in (
            (positive_id, positive, positive_judge),
            (intermediate_id, intermediate, intermediate_judge),
        ):
            files.extend([
                (ANALOGUES / f"{identifier}.generator.json", generator),
                (ANALOGUES / f"{identifier}.judge.json", judge),
            ])
            manifest_records.append({"case_id": identifier, "domain": base["domain"], "split": base["split"], "group": judge["group"], "control_origin": judge["control_origin"], "passage_function": base["function"]})
        for negative_kind in ("negative_actor", "negative_hype"):
            identifier = case_id(base["key"] + ":" + negative_kind)
            generator = generator_record(base, identifier, render(base, quality=negative_kind))
            judge = judge_record(base, identifier, "negative", "original_negative", "low")
            files.extend([
                (ANALOGUES / f"{identifier}.generator.json", generator),
                (ANALOGUES / f"{identifier}.judge.json", judge),
            ])
            manifest_records.append({"case_id": identifier, "domain": base["domain"], "split": base["split"], "group": "negative", "control_origin": "original_negative", "passage_function": base["function"]})
        for construct in CONSTRUCTS:
            identifier = case_id(base["key"] + ":contrast:" + construct)
            declines, stable, failure, minimum = contrast_expectation(construct)
            contrast = {
                "original_case_id": positive_id,
                "changed_construct": construct,
                "expected_declines": declines,
                "expected_stable": stable,
                "expected_hard_failure": failure,
                "minimum_total_reduction": minimum,
                "acceptable_alternatives": ["A stricter deduction is acceptable when specifically justified."]
            }
            generator = generator_record(base, identifier, render(base, variant=construct))
            judge = judge_record(base, identifier, "contrast", "derived_contrast", "low", contrast)
            files.extend([
                (CONTRASTS / f"{identifier}.generator.json", generator),
                (CONTRASTS / f"{identifier}.judge.json", judge),
            ])
            manifest_records.append({"case_id": identifier, "domain": base["domain"], "split": base["split"], "group": "contrast", "control_origin": "derived_contrast", "passage_function": base["function"], "original_case_id": positive_id, "changed_construct": construct})
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "suite": "public-synthetic-calibration-v3",
        "status": "synthetic_only_not_expert_validated",
        "records": sorted(manifest_records, key=lambda item: item["case_id"]),
    }
    files.append((MANIFEST, manifest))
    return files, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, manifest = build_records()
    stale: list[str] = []
    expected_paths = {path.resolve() for path, _ in files}
    for directory in (ANALOGUES, CONTRASTS):
        if directory.exists():
            for path in directory.glob("*.json"):
                if path.resolve() not in expected_paths:
                    stale.append(str(path.relative_to(ROOT)))
    for path, value in files:
        expected = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(str(path.relative_to(ROOT)))
        else:
            write_json(path, value)
    if stale:
        print("Generated public calibration suite is stale:")
        for item in sorted(set(stale)):
            print(f"- {item}")
        return 1
    counts: dict[str, int] = {}
    for record in manifest["records"]:
        counts[record["group"]] = counts.get(record["group"], 0) + 1
    print(json.dumps({"cases": len(manifest["records"]), "groups": counts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
