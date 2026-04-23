# Impossible Pooling Pilot — Comparison

## Normal-case comparison

| flavour | lower | upper | width | point | bounded? | min_info |
|---|---|---|---|---|---|---|
| cross_framing | -0.289 | 0.308 | 0.597 | 0.010 | yes | pooled: converted SMDs via Hedges g / probit / log-OR*sqrt(… |
| era_collision | -0.469 | 0.067 | 0.536 | -0.201 | yes | beta enumerated over [-0.5, 0.5] on 21-pt grid, FE pool |

## Degenerate-case behaviour

| flavour | tight → classical? | unbounded flagged? | notes |
|---|---|---|---|
| cross_framing | yes | bounded (wide) | — |
| era_collision | yes | bounded (wide) | — |
