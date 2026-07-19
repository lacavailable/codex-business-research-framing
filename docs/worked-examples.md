# Synthetic worked examples

Every organization, number, and situation on this page is invented. These examples demonstrate reasoning structure; they are not evidence about any real market or company.

## OM: substitution under assortment capacity

### Weak framing

> A rapid-delivery retailer should show the most popular products because customers value convenience. Our model helps the retailer delight customers and grow revenue.

The prose names an appealing outcome but does not identify who chooses the display, when the choice occurs, what is known then, or how substitution enters the model. “Most popular” may even require demand information unavailable at decision time.

### Fidelity-first framing

A synthetic neighborhood fulfillment manager chooses at most 20 products to display before a two-hour demand window. The manager knows estimated arrival rates and substitution probabilities from an earlier calibration period, but not the identities or first choices of future arrivals. A customer whose preferred product is not displayed may select another displayed product according to the supplied capacity-constrained choice model. Adding a niche item can capture its direct demand while displacing an item that attracts more demand or receives more substitution. The model maximizes expected contribution over the window subject to display capacity; it does not represent replenishment, delivery routing, customer welfare, or estimation error.

The improvement is not merely stylistic: actor, timing, available information, trade-off, and mathematical objective are now explicit. The estimated behavior remains a model assumption unless supported by validation evidence.

## IS: review capacity and strategic submissions

### Weak framing

> An AI platform reviews dangerous messages and refuses malicious users, making the platform safer and fairer.

This wording collapses user intent, message risk, review decisions, and model outcomes. It also asserts safety and fairness effects that may not be optimized or measured.

### Fidelity-first framing

A synthetic platform operator allocates a fixed daily number of specialist reviews after an automated signal is observed and before a reply is released. Benign and malicious users may adapt whether to submit after learning the published screening rule. The operator chooses a review policy that trades the modeled loss from harmful released replies against review cost and the modeled loss from refusing benign requests. The formulation represents user types as latent states rather than operator choices. It supports claims about the specified loss function, not population-wide safety, fairness, or user welfare.

This version preserves the temporal order and strategic mechanism while labeling broader impact claims as unsupported.

## OR: faster exact optimization at a deadline

### Weak framing

> Our stronger MILP formulation transforms logistics by finding better schedules in real time.

A stronger formulation does not necessarily change the optimal solution, and “real time” has no meaning without a deadline. The statement confuses computational performance with operational outcome.

### Fidelity-first framing

A synthetic regional dispatcher must finalize a resource schedule within 15 minutes of receiving a fixed planning instance. Two exact MILP formulations have the same feasible schedules and objective. The strengthened formulation can improve bounds and may prove optimality sooner on the benchmark instances. Its operational value arises only when the existing formulation fails to return an acceptable incumbent or certificate by the decision deadline. Faster solve times do not by themselves imply better schedules, lower realized costs, or general performance beyond the tested instance distribution.

The business relevance is conditional on the deadline and incumbent-quality pathway; equivalence of objectives and feasible regions remains explicit.
