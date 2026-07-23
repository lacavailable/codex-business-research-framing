# Codex Business Research Framing

`frame-business-research-problem` is an open-source Codex Agent Skill that helps Operations Management (OM), Information Systems (IS), and Operations Research (OR) researchers turn models and early ideas into concrete, defensible business-research problems.

> **Skill 2.2 is a failed experimental candidate, not a release.** Its bounded
> routing canary passed the frozen profile, answer-first, non-repetition,
> empirical-fact, and computational-overclaim gates, but a full-audit output
> introduced one material fidelity regression by treating unsupplied model
> semantics as stated. The branch is not merge-authorized. Skill 2.1 also
> remains a failed, unmerged experimental record. Evaluator validation, both
> holdouts, a release tag, and performance claims remain unavailable. See the
> [development authorization](docs/skill-development-without-evaluator-freeze.md)
> and the candid [Skill 2.1](docs/skill-2.1-direct-experimental-results.md) and
> [Skill 2.2](docs/skill-2.2-routing-canary-results.md) results.

## Contents

1. [Project summary](#1-project-summary)
2. [Who this is for](#2-who-this-is-for)
3. [Typical use cases](#3-typical-use-cases)
4. [When the Skill can be used](#4-when-the-skill-can-be-used)
5. [Minimum viable input](#5-minimum-viable-input)
6. [Recommended input](#6-recommended-input)
7. [Can I use this Skill?](#7-can-i-use-this-skill-decision-guide)
8. [The eight modes](#8-the-eight-modes)
9. [How the Skill works](#9-how-the-skill-works)
10. [Primary worked example](#10-primary-worked-example-model-plus-rough-setting)
11. [Additional worked examples](#11-additional-worked-examples)
12. [Understanding the output](#12-understanding-the-output)
13. [Installation](#13-installation)
14. [Invocation examples](#14-invocation-examples)
15. [Literature foundation](#15-literature-foundation)
16. [What the Skill cannot do](#16-what-the-skill-cannot-do)
17. [Evaluation](#17-evaluation)
18. [Copyright and affiliation](#18-copyright-and-affiliation)
19. [Contributing and citation](#19-contributing-and-citation)

## 1. Project summary

Analytical research often has a strong model but a weak, vague, or inconsistent business story. A commercially attractive narrative can silently assign a decision to the wrong actor, use information that is unavailable at decision time, turn an uncertain state into a choice, change a constraint, or claim an objective the model does not optimize.

This Skill puts fidelity before storytelling. It freezes model invariants, completes the twelve-element Decision-Fidelity Canvas (DFC-12), and applies six noncompensatory gates: actor, timing, information, behavior, constraints, and objective. A failed gate makes a scenario ineligible regardless of prose quality. Only an eligible interpretation proceeds to managerial framing, scholarly positioning, evidence auditing, and final prose.

The Skill is not an HBR imitation tool. Practitioner sources inform bounded observations about useful execution; they do not supply a voice, template, scientific guarantee, or permission to copy expression.

## 2. Who this is for

The Skill is designed for OM, IS, OR, and adjacent analytical-modeling researchers; PhD students learning to connect formal work to managerial decisions; and authors revising introductions, business-setting sections, or managerial implications. It is most valuable when mathematical or conceptual precision matters more than generic persuasive writing.

## 3. Typical use cases

- You have a model and a rough business-setting idea.
- You have a model but no convincing setting.
- You suspect an existing setting contradicts the model.
- You have an introduction that needs a fidelity-aware rewrite.
- You need to interpret numerical or analytical results managerially.
- You want to compare several candidate settings.
- You need an assumptions audit that separates tractability from realism.

## 4. When the Skill can be used

Missing information lowers the maturity of the output; it does not prevent all useful work and never licenses invention.

| Input maturity | What the Skill can produce | What it cannot establish |
|---|---|---|
| Stage 1 — exploratory | Candidate decision structures, provisional scenarios, missing-information diagnosis, research-question candidates | Model fit, final academic claims, or empirical importance |
| Stage 2 — model-grounded | Full DFC-12, six-gate audit, model mapping, eligible narrative, scenario comparison | Empirical truth or external validity without evidence |
| Stage 3 — evidence-grounded | Evidence-aware motivation, stronger significance claims, claim checklist, introduction draft | Causality or generality beyond supplied evidence |
| Stage 4 — manuscript-ready | Introduction, setting, implications, rewrite, and full framing audit | Publication success or correctness of the model itself |

Stage 2 is the primary intended use. Exploratory work uses `unknown` and `not_assessed`; it must not pretend that an untestable gate passed.

## 5. Minimum viable input

Model-grounded framing requires a responsible actor, the controlled decision, the model objective, major constraints, decision timing, decision-time information, the behavioral or operational mechanism, and a rough business concept. Formal equations are strongly recommended, but a precise conceptual model can be sufficient when it unambiguously defines roles, sequence, feasible choices, and outcomes.

If one of these essentials is unknown, use exploratory framing. The Skill should identify the missing item and its consequence rather than filling it with a plausible fact.

## 6. Recommended input

For stronger results, supply the research objective; objective function; decision variables; states; parameters; uncertainty and revelation timing; constraints; decision sequence; decision-time observations; mechanism; principal results; proposed contribution; candidate setting and doubts; credible evidence; intended mode; target manuscript section; target outlet or reader; and length and language requirements.

Copy the [Markdown input template](skills/frame-business-research-problem/assets/research-framing-input-template.md) or its [JSON equivalent](skills/frame-business-research-problem/assets/research-framing-input-template.json). The JSON format is checked by the bundled [JSON Schema](skills/frame-business-research-problem/assets/research-framing-input.schema.json).

## 7. Can I use this Skill? decision guide

1. **Do you have a precise model?** If no, use `create` or `diagnose` at Stage 1 for candidate structures and missing information. Expect `not_assessed`, not an eligible finding.
2. **Do you have a model but no setting?** Use `map-model-to-business`, then `create` or `compare-scenarios` at Stage 2.
3. **Do you have a candidate setting?** Use `diagnose` first. Use `rewrite` only after failed gates are repaired or explicitly bounded.
4. **Do you have credible evidence?** If yes, Stage 3 can support evidence-aware significance and claims. If no, keep institutional and trend claims labeled unsupported.
5. **Do you have results and literature positioning?** If yes, Stage 4 can support `draft-introduction` or `draft-managerial-implications`. Otherwise use the narrower diagnostic mode.

## 8. The eight modes

### `create`

Purpose: construct one fidelity-tested setting. Required input: Stage 1 for provisional candidates or Stage 2 for eligibility. Output: readiness, setting, managerial question, significance, mechanism, structural tension, evidence needs, and counterconditions. Do not use it to declare fit from an underspecified idea.

```text
Use $frame-business-research-problem in create mode. Build one setting for this
capacity-allocation model and mark unknown information explicitly.
```

### `diagnose`

Purpose: audit an existing setting separately for model fidelity, managerial framing, scholarly positioning, evidence, and prose. Required input: the setting plus the most precise available model description. Output: five-part diagnosis and repair priorities. Do not use prose weakness as evidence of fidelity failure.

```text
Diagnose this platform-moderation story against the supplied timing and latent-user model.
```

### `rewrite`

Purpose: revise existing text after auditing it. Required input: source text, model invariants, and desired audience. Output: rewritten text plus changes categorized as fidelity, evidence, scholarly positioning, managerial framing, or prose only. Do not use it to silently change the model.

```text
Rewrite this introduction and list every fidelity correction separately from prose edits.
```

### `compare-scenarios`

Purpose: test alternative business settings. Required input: a stable model and two or more candidates. Output: gate results for all candidates and rankings only for eligible ones. Eligible scenarios are compared by model fit, managerial significance, structural tension, evidence plausibility, scholarly contribution potential, and boundary transparency—in that order. Do not rank a failed scenario.

```text
Compare these three settings, reject any that use future demand information, and rank the rest.
```

### `map-model-to-business`

Purpose: make semantic commitments visible. Required input: equations or a precise conceptual specification. Output: mappings for variables, parameters, states, uncertainty, observations, constraints, objectives, outcomes, derived variables, timing, units, and horizon. Do not treat a mapping as empirical validation.

```text
Map every object in this stochastic program to the proposed staffing decision.
```

### `audit-assumptions`

Purpose: test each assumption's role and interpretive risk. Required input: assumptions and the proposed setting. Output: type, necessity, business meaning, tractability role, evidence need, sensitivity, boundary, and whether a change alters the model or only the narrative. Do not recommend changing a model under the label of narrative repair.

```text
Audit these demand and observability assumptions and identify which ones create business boundaries.
```

### `draft-introduction`

Purpose: draft a flexible, literature-aware introduction. Required input: fidelity-eligible Stage 3 material; Stage 4 is recommended. Output: decision or phenomenon, stakes, tension, limitation, opportunity, question, method, contribution, and bounded relevance. Do not use it to invent novelty or evidence.

```text
Draft an introduction from this eligible brief and supplied literature map; flag every unsupported claim.
```

### `draft-managerial-implications`

Purpose: convert results into conditional, actor-specific implications. Required input: eligible mapping, established results, and an operational pathway. Output: actor, decision, condition, mechanism, model-supported consequence, evidence status, implementation requirement, excluded claim, and boundary. Do not translate runtime directly into profit.

```text
Draft implications for these comparative statics and identify the data and authority needed to act.
```

## 9. How the Skill works

Internally, the mandatory order remains: extract model invariants; classify decisions, states, parameters, observations, uncertainty, outcomes, and derived variables; complete DFC-12; run all six gates; reject or repair inconsistent scenarios; apply managerial framing; apply scholarly positioning when appropriate; draft; and audit evidence and boundaries.

Visible output uses one of three profiles. `compact` produces a 120–220-word usable answer with at most three material caveats. `standard` produces a 250–500-word diagnosis and manuscript-ready framing with only the essential evidence need and principal boundary. `full-audit` exposes the complete framework only for an explicit audit, comparison, mapping, review, or machine-readable request. Ordinary writing begins with usable prose rather than internal scaffolding, suppresses nonapplicable layers, and states each substantive issue once.

Later layers cannot compensate for earlier failures. A clear introduction cannot rescue hidden future information, and an important practical topic cannot rescue the wrong objective.

## 10. Primary worked example: model plus rough setting

Consider a synthetic capacity-constrained assortment model with a Markov substitution mechanism. The rough idea is: “Consumers search for products, select a nearby store, and the platform chooses what products appear online.” That idea sounds commercially plausible but leaves material semantic choices unresolved.

### Before

> Online grocers increasingly need intelligent assortments. Customers search for the products they want and choose a nearby store, so our platform optimizes the products shown online to improve convenience and profit.

This paragraph asserts a trend, confuses store selection with within-store choice, leaves the assortment owner and decision time unclear, and does not say whether capacity is display, inventory, or fulfillment.

### Audit

**Frozen invariants.** A binary assortment is selected before arrivals; at most (K) products are offered; an arriving customer has an initial product state and may transition among offered alternatives according to fixed Markov probabilities; purchases yield modeled contribution; store choice, inventory replenishment, picking capacity, and routing are absent.

**DFC-12 summary.** The candidate actor is a synthetic retailer's digital merchandising manager; the trigger is assortment publication for a planning window; choices are product inclusion decisions; decision-time information consists of previously estimated arrival and transition parameters; stakes are modeled expected contribution; friction is a distinct online-display capacity; the mechanism is within-assortment substitution; the trade-off is direct demand versus capacity and substitution capture; the counterfactual is another feasible assortment; mapping and evidence remain explicit; boundaries exclude store choice and physical fulfillment.

| Gate | Status | Reason |
|---|---|---|
| Actor | uncertain | “Platform” does not identify who owns the assortment. |
| Timing | uncertain | The rough text does not say when products are fixed. |
| Information | fail if interpreted literally | Knowing each future customer's desired product would exceed the model's advance information. |
| Behavior | fail under nearest-store-only behavior | A customer who searches for one fixed item and mechanically selects the nearest store does not exhibit the modeled within-store Markov substitution. |
| Constraints | uncertain | Display, inventory, and fulfillment capacity are not interchangeable. |
| Objective | uncertain | “Convenience and profit” may differ from expected contribution. |

**Repair questions.** Who controls the online assortment? Is it fixed before the demand window? Do customers browse within one retailer after an initial preference, or only locate a fixed product across stores? Which single resource does (K) represent? Is store selection outside the model? What evidence supports the proposed substitution interpretation?

Until these questions are answered, eligibility is `not_assessed` or `ineligible`, depending on whether the conflicting interpretation is asserted. Missing evidence includes validation of the substitution process, institutional authority over assortment, and calibration of transition probabilities.

### After

A synthetic online-grocery retailer's digital merchandising manager selects, before a weekly planning window, at most (K) products to display in one category. The manager uses arrival and substitution parameters estimated from an earlier calibration period but does not observe future customers' initial preferences. When an initially preferred item is unavailable, a customer may move among displayed alternatives according to the supplied Markov transition model. Including a niche product can capture its direct demand while consuming display capacity that could support a product receiving more initial or substituted demand. The manager therefore maximizes modeled expected contribution subject to online-display capacity. The interpretation does not represent consumers choosing among stores, physical inventory availability, fulfillment workload, replenishment, or empirically validated substitution unless separate evidence is supplied.

This repair is synthetic and fidelity-eligible only under the stated interpretation; it is not empirical validation of an online grocer.

### Model-to-reality mapping

| Model object | Role | Business meaning | Timing/information | Boundary |
|---|---|---|---|---|
| (x_i) | decision | Whether product (i) is displayed | Chosen before the weekly window | Not an inventory quantity |
| (K) | constraint parameter | Maximum display slots | Known before choice | Not picking or fulfillment capacity |
| Initial state | uncertain state | Customer's initially preferred item | Unobserved for future arrivals | Not chosen by manager |
| Transition matrix | parameter | Conditional within-category substitution | Estimated before choice | Requires behavioral validation |
| Expected contribution | objective | Modeled margin-weighted expected purchases | Evaluated over the window | Not customer welfare or realized profit |

### Claims requiring evidence

- That the retailer fixes the display for the stated window: institutional evidence needed.
- That customers substitute in a Markov-consistent way: behavioral and calibration evidence needed.
- That display capacity is binding or consequential: operational evidence needed.
- Any market trend, prevalence, or realized-profit claim: external evidence needed.

### Proposed introduction opening

Digital category managers can face an advance assortment choice when limited interface space prevents every product from being displayed simultaneously. The difficulty is not only which products attract initial demand: when unavailable items induce substitution, one product can create value through its own demand while another attracts transitions from several initial preferences. We study a capacity-constrained assortment problem with a Markov substitution mechanism and ask how a manager should allocate display slots when future initial preferences are unobserved. The model isolates this within-category display decision; it does not represent store search, physical fulfillment capacity, or empirical substitution validity.

### Managerial implication

For a category manager choosing display slots before demand, a product's modeled value depends on both direct arrivals and substitution pathways. If transition estimates are stable and display capacity is the actual scarce resource, removing a low-direct-demand item can still reduce modeled contribution when it receives substantial transitions. Implementation requires calibrated transitions and authority to fix the display. The result does not establish realized profit, customer welfare, or an inventory policy.

**Primary remaining weakness:** the Markov substitution interpretation and its stability have not been empirically validated for the proposed setting.

## 11. Additional worked examples

### IS: latent benign and malicious users

Weak: “The platform observes malicious users, reviews risky replies, and refuses them to maximize safety.” Repair: benign or malicious type is a latent state, not an observation; the operator sees only the modeled signal, allocates review before release, and optimizes the specified private loss or revenue objective. Safety, fairness, and welfare remain excluded unless modeled and evidenced.

### OR: exact MILP and operational value

Weak: “A faster exact formulation increases logistics profit.” Repair: two formulations may share the same feasible set and objective while differing in bounds or time to a certificate. Managerial value exists only through an explicit pathway—such as returning a better incumbent or required certificate before a scheduling deadline—and still does not establish realized profit.

### Insufficient input

Input: “AI improves operations.” Appropriate response: Stage 1, `not_assessed`. Ask who acts, what is controlled, the objective, constraints, timing, available information, mechanism, evidence, and boundary. Do not manufacture a final research problem or declare AI important.

### Unsupported trend rewrite

Weak: “AI is increasingly important, yet little research has studied it in warehouses.” Repair: remove the unsupported trend and generic context gap. Open with a specific warehouse decision, explain the operational mechanism or tension, identify what current understanding cannot explain, and state a bounded contribution supported by the supplied literature.

See [additional synthetic examples](docs/worked-examples.md).

## 12. Understanding the output

- `eligible`: all six fidelity gates pass on supplied information.
- `ineligible`: at least one fidelity gate demonstrably fails.
- `not_assessed`: information is insufficient to test every gate.
- **Model mapping**: explicit semantic commitments between model objects and reality; not empirical validation.
- **Evidence labels**: empirical fact, model assumption, simplifying assumption, inference, or unsupported claim.
- **Boundaries**: conditions, systems, outcomes, actors, or claims outside the interpretation.
- **Primary remaining weakness**: the single unresolved issue most likely to limit use.

An exploratory or provisional output is a structured hypothesis, not manuscript-ready prose. Maturity depends on input quality, not confidence of wording.

## 13. Installation

Download `frame-business-research-problem-v0.2.0-beta.zip` from the prerelease and verify its adjacent SHA-256 checksum. Extract it so your Codex skills directory contains one top-level `frame-business-research-problem/` folder. On Windows:

```powershell
Expand-Archive frame-business-research-problem-v0.2.0-beta.zip -DestinationPath "$env:USERPROFILE\.agents\skills"
```

On macOS or Linux:

```bash
unzip frame-business-research-problem-v0.2.0-beta.zip -d "$HOME/.agents/skills"
```

When GitHub Skill installation is supported, install from this repository's `skills/frame-business-research-problem` path. For development:

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python tools/check_links.py
python tools/validate_literature.py
python skills/frame-business-research-problem/scripts/validate_brief.py BRIEF.json
```

Restart Codex or begin a new task after installation. Verify that the Skill appears by asking Codex to use `$frame-business-research-problem` in `diagnose` mode.

## 14. Invocation examples

Natural language, English:

```text
Audit whether this inventory-allocation setting preserves my model's actor,
timing, information, constraints, and objective. Do not invent missing facts.
```

Explicit, English:

```text
Use $frame-business-research-problem in compare-scenarios mode. Gate all three
settings first and rank only eligible settings using model fit as the first criterion.
```

自然语言，中文：

```text
请检查这个平台治理场景是否与模型中的决策者、时序、可用信息、约束和目标一致。
缺失信息请标为 unknown，不要虚构事实。
```

显式调用，中文：

```text
请使用 $frame-business-research-problem 的 diagnose 模式，分别诊断模型忠实度、
管理问题框架、学术定位、证据和表达，并指出最重要的剩余缺陷。
```

## 15. Literature foundation

v0.2 uses a focused 20-source corpus selected for authority, relevance, and complementarity. [`literature/manifest.yaml`](literature/manifest.yaml) is canonical metadata. Every included source has an original source card with separate fresh-context extraction and audit records. Sources are classified as official guidance/editorial, peer-reviewed foundational scholarship, or exemplar execution.

Audited principles enter the canonical rule registry only with explicit support, counterconditions, limitations, anti-patterns, and affected criteria. The [source-to-rule matrix](skills/frame-business-research-problem/references/source-to-rule-matrix.md) is generated rather than hand-maintained.

Verification is scope-specific, not a claim of full-text review. The audited corpus currently admits one triangulated scholarly-positioning rule, one provisional problematization rule, bounded official outlet guidance, and practitioner execution observations. DFC-12, the six gates, domain fidelity tests, implication fields, and introduction sequence remain explicitly original framework rules rather than literature consensus.

Read the [review protocol](docs/literature-review-protocol.md), [synthesis](docs/literature-synthesis.md), [selection and exclusion log](docs/source-selection-and-exclusion-log.md), [design explanation](docs/literature-grounded-skill-design.md), and [third-party notices](THIRD_PARTY_NOTICES.md). No HBR article, journal PDF, HTML snapshot, screenshot, book chapter, or other third-party full text is publicly bundled in v0.2.

## 16. What the Skill cannot do

The Skill cannot establish empirical truth without evidence; prove market importance; repair an invalid model; guarantee external validity; establish causality absent from the research design; convert runtime improvement directly into realized profit; replace a literature review; guarantee journal acceptance; or replace human scholarly judgment. It also cannot make an unavailable signal observable, a state controllable, or a private objective equivalent to social welfare.

## 17. Evaluation

The v0.2 benchmark has 42 synthetic cases—14 each for OM, IS, and OR—and compares a normal no-Skill request, the tagged `v0.1.0-alpha` Skill, and `v0.2.0-beta`. The design calls for 126 outputs, two condition-blind judges per output, and limited third-judge adjudication for material disagreement.

The canonical 100-point rubric scores fidelity (30), managerial framing (25), scholarly positioning (20), evidence discipline (15), and prose clarity (10). Success requires 70 points, all applicable layer minima, and no fidelity hard failure; raw scores remain visible and hard failures cap totals at 69.

Read the [methodology](docs/v0.2-evaluation-methodology.md), [report](docs/v0.2-evaluation-report.md), committed synthetic artifacts under `evals/`, and [limitations](docs/limitations.md). Language-model evaluation is not rerun in required CI; deterministic CI validates artifact completeness and integrity.

Skill 2.1 direct development used a separate eight-task, 24-call synthetic
canary. The candidate failed its frozen acceptance policy and is not
merge-authorized. Even a passing result could have authorized only an
experimental development merge, not evaluator validity, expert validation,
general superiority, or release eligibility.

## 18. Copyright and affiliation

The repository's code and original prose use the MIT License. Third-party materials retain their own copyrights and licenses. Nonredistributable sources and substantial local annotations belong only under ignored `research-private/literature/`. Public source files require explicit redistribution permission, checksum, attribution, license documentation, manifest agreement, and notice coverage.

This project is not sponsored, endorsed by, or affiliated with Harvard Business Review, Harvard Business Publishing, INFORMS, AIS, Management Science, MIS Quarterly, the Academy of Management, or any other publisher or association. It does not claim to imitate a publisher's style.

## 19. Contributing and citation

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), the [MIT License](LICENSE), and collective authorship metadata in [CITATION.cff](CITATION.cff). Contributions must preserve DFC-12, the noncompensatory fidelity policy, evidence traceability, copyright boundaries, and generated-document consistency.
