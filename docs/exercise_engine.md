# Exercise Engine Deep Dive

The exercise engine translates raw movement logs into structured performance and consistency signals used by the dashboard and metabolic advisor.

## Supported categories

- `WALK`
- `BODYWEIGHT`
- `MONKEY_BAR`
- `STRENGTH`

Each category supports movement-specific metadata and validation constraints.

## Core objectives

- Score movement quality and training consistency.
- Reward metabolically valuable behavior (e.g., post-meal movement).
- Generate progression indicators that can feed recommendations.

## Key outputs

- **Strength score**: aggregated representation of resistance training quality.
- **Grip improvement %**: trend metric used for monkey-bar/bodyweight progression context.
- **Monkey-bar progression index**: specialized progression signal for skill-based upper-body movement.
- **Weekly strength trend**: rolling trend for dashboard/analytics visualizations.

## Processing flow

1. Validate payload shape and required fields.
2. Verify category ↔ movement compatibility.
3. Normalize duration/intensity/set-rep values.
4. Compute category-level derived metrics.
5. Apply bonuses (for example, qualifying post-meal walk signals).
6. Persist results and expose summary endpoints.

## Rule integrations

- Post-meal walk logic influences metabolic coaching signals.
- Movement quality signals are consumed by advisory services.
- Exercise summaries combine with vitals and nutrition trends for broader recommendations.

## Data capture recommendations

- Prefer explicit `duration_minutes` and `perceived_intensity`.
- Use consistent movement naming to improve trend continuity.
- Capture `calories_estimate` and step metadata when available.
- For strength/bodyweight: include sets/reps whenever possible.

## Validation examples

- A `WALK` entry with very high perceived intensity but near-zero duration is flagged/normalized.
- A monkey-bar movement without matching category metadata is rejected.
- Missing required identifiers (user/date/activity) returns schema validation errors.
