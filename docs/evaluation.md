# Evaluation

This file is a placeholder to be filled in after running:

```bash
python -m tests.run_eval
```

Once `tests/test_results.md` is generated, use it to fill in:

## What worked

(e.g. which guardrail had the cleanest recall/FPR trade-off, and why)

## What didn't / surprises

(e.g. which adversarial cases slipped through, whether the small judge
model's classifications were noisy compared to a larger model, whether the
grounding guardrail's combined classify+rewrite call held up)

## Limitations

(link back to [DESIGN.md](../DESIGN.md#trade-offs--limitations) and add
anything discovered only while running real evaluations)

## What's next

(e.g. separate the grounding classify/rewrite steps, expand the KB,
multi-turn injection resistance)
