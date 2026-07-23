# Original Rendering Examples

All examples are synthetic. Use them as structural demonstrations, not as
empirical evidence or prose to copy mechanically.

## 1. One model in three profiles

**Supplied model.** A retailer chooses an assortment of at most six products
before demand. Customers transition among offered alternatives under a
Markov-chain choice model. The objective is expected margin.

### Compact

The retailer must choose a limited assortment before demand is realized, knowing
that removing one product can redirect rather than eliminate customer demand.
Because only six products can be offered, adding an item creates a trade-off:
it may capture direct demand while displacing an item that attracts profitable
substitution. The Markov-chain choice model represents these transitions and
lets the retailer compare feasible assortments by expected margin. The business
problem is therefore not simply which products are popular, but which
capacity-constrained set best manages substitution across the offered
portfolio.

Boundary: the framing assumes the supplied transition parameters describe
choice among offered products; it does not establish that individual customer
paths are observed.

### Standard

The retailer chooses which products to offer before demand is realized, subject
to a six-product capacity limit. Demand for an omitted item may move to another
offered item, so product values are interdependent rather than separable. The
Markov-chain choice model captures that substitution mechanism, and the
objective compares feasible assortments by expected margin.

This creates a concrete operating tension. Expanding variety can retain demand,
but every slot devoted to one item excludes another item whose direct demand or
substitution role may be more valuable. A faithful research question is:
which capacity-feasible assortment maximizes expected margin when customer
substitution depends on the complete offered set?

The decision variable maps to product availability, not display prominence or
inventory after demand. The essential evidence need is support for the
transition parameters in the intended setting. The principal boundary is that
the model represents aggregate substitution; it does not show that managers
observe each customer's transition path.

### Full audit

- **Actor:** retailer.
- **Timing:** assortment selected before demand.
- **Choice:** binary product inclusion, with at most six included products.
- **Information:** supplied demand and transition parameters, not realized
  customer paths.
- **Mechanism:** omitted or unavailable alternatives redirect choice according
  to the Markov chain.
- **Objective:** expected margin.
- **Trade-off:** direct demand and substitution value versus scarce assortment
  capacity.
- **Eligibility:** supported if the mathematical formulation has these
  variables, constraint, timing, transitions, and objective.
- **Evidence:** transition estimates are `not_supplied` unless a source or
  estimation design is provided.
- **Boundary:** display, inventory, and fulfillment effects are
  `not_applicable` unless modeled.

The manuscript-ready framing is the compact paragraph above. The full audit
does not authorize individual-path observability or empirical performance
claims.

## 2. OM business-problem framing

A service operator schedules agents before uncertain requests arrive. Higher
staffing reduces delay but raises labor cost and may leave paid capacity idle.
The research problem is to choose a schedule that balances service and cost
under the supplied arrival and service assumptions. Realized waiting time is an
outcome of staffing and demand, not a decision the operator directly chooses.

## 3. IS platform-governance framing

A platform allocates a fixed review budget using noisy risk signals, then takes
action after review. Stricter targeting can concentrate scarce review on risky
cases but may exclude benign users when signals are imperfect. The model can
study the platform's allocation rule and induced user response; it cannot treat
latent malicious type as already observed or call platform revenue social
welfare.

## 4. OR computational-contribution framing

The operational problem requires a feasible routing plan before a dispatch
deadline. The proposed formulation preserves the same feasible routes and true
optimum but yields stronger relaxation bounds on the tested instances. Its
potential operational value depends on whether those bounds produce a better
incumbent or a useful certificate before dispatch. Benchmark improvement alone
does not establish realized service or financial value.

## 5. Runtime-versus-profit correction

**Unsupported:** “The algorithm is 30% faster, so profit rises 30%.”

**Repair:** “The algorithm reduced runtime by 30% on the tested instances. This
could matter if the reduction enables a better feasible plan before the
decision deadline, more frequent reoptimization, or larger scenario sets.
Realized profit effects are `not_supplied` and require a modeled or empirical
link from computation to executed decisions.”

## 6. Post-deadline certificate correction

An incumbent available at minute eight can affect a decision executed at minute
ten. A proof of optimality arriving at minute thirty cannot improve that
already executed decision. The later certificate can support retrospective
assessment or future method development, but current operational value must be
based on the pre-deadline incumbent and information.

## 7. Rejecting an unsuitable commercial setting

If a regulator chooses inspections to minimize system harm, a story about a
vendor choosing price to maximize profit is `contradicted`: it changes the
actor, decision, and objective. Do not repair it with more persuasive prose.
Either retain the regulator-inspection setting or declare a new commercial
extension and modify the model explicitly.

## 8. Refusing to invent empirical facts

**Request:** “Explain that online fraud is rapidly increasing and costs firms
billions.”

**Response:** Those prevalence and magnitude claims are `not_supplied`. Frame
the decision problem without them, or provide traceable evidence specifying the
population, period, measure, and source. Do not turn the model's motivation into
an empirical fact.

## 9. Scholarly positioning when applicable

For an introduction or contribution paragraph, position the work around the
specific relation the model clarifies: a capacity constraint and delayed
information jointly change the optimal allocation rule. State the mechanism,
the bounded theoretical contrast, and the conditions under which it holds.
Literature novelty remains `not_assessed` until relevant prior work is supplied
or reviewed.

## 10. Scholarly positioning when not applicable

For a request to explain what a state variable means, answer the mapping
directly. Describe whether it is observed, when it is realized, and how it
affects feasible decisions or outcomes. A literature gap, managerial
implication, and contribution claim are `not_applicable` to that narrow task
unless the user asks for them.
