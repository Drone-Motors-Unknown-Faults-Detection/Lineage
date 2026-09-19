# Fault type data requirements

## Current decision

The formal dataset can support a binary known/unknown Open Set decision and a
relative health index. It cannot support a trustworthy physical fault-cause
classifier. The existing labels identify screw configurations (`8screws`,
`1screws`, and so on); they do not identify bearing wear, winding damage, ESC
fault, imbalance, or any other cause. A configuration name is therefore not
renamed into a physical fault type.

Until the data contract is extended, the output policy is:

- `fault_type="unknown"` when the Open Set score is above the calibrated
  threshold or the detector rejects the known class.
- `fault_type="uncertain"` when a future classifier is unavailable or below a
  documented confidence/coverage requirement.
- A named fault type is allowed only when it is present in a versioned label
  taxonomy and the training/validation split contains that label.

## Required extension for supervised fault types

Each window needs a stable `motor_id`, `session_id`, timestamp or ordered
sample index, operating condition, and an operator-confirmed `fault_type`.
The label must be attached after the prediction split is fixed so that unknown
windows cannot leak into training or threshold calibration. Recommended
minimum fields are:

| field | requirement |
| --- | --- |
| `motor_id` | non-reused physical motor identifier |
| `session_id` | one acquisition/run identifier |
| `timestamp` | UTC timestamp or monotone sample index |
| `condition` | motor, RPM, load, voltage and temperature |
| `fault_type` | versioned cause taxonomy, including `unknown` and `uncertain` |
| `severity_stage` | operator/maintenance-confirmed ordinal stage |
| `failure_endpoint` | run-to-failure marker if RUL is ever enabled |

At least two independent sessions per motor and multiple motors per class are
needed before reporting cross-motor generalisation. A single screw setting is
not sufficient evidence for a physical cause.

## Evaluation rule

Until those labels exist, reports must show Open Set metrics (unknown recall,
false-positive rate, AUROC/AUPR) and relative health metrics separately from
any future fault-cause metrics. No physical fault type, damage percentage or
RUL value may be inferred from the current configuration label.

