# Impossible Pooling Pilot — Comparison

## Normal-case comparison

| flavour | lower | upper | width | point | bounded? | min_info |
|---|---|---|---|---|---|---|
| disconnected_nma | -0.533 | 0.635 | 1.168 | — | yes | delta_log_odds=0.3, bubble_pool=FE, grid=21 |
| extreme_het | -0.996 | 1.116 | 2.112 | — | yes | refused: I2=0.98, tau_ratio=57.10, study-level envelope |
| cross_framing | -0.289 | 0.308 | 0.597 | 0.010 | yes | pooled: converted SMDs via Hedges g / probit / log-OR*sqrt(… |
| era_collision | -0.469 | 0.067 | 0.536 | -0.201 | yes | beta enumerated over [-0.5, 0.5] on 21-pt grid, FE pool |

## Degenerate-case behaviour

| flavour | tight → classical? | unbounded flagged? | notes |
|---|---|---|---|
| disconnected_nma | yes | inf-flagged | — |
| extreme_het | yes | refused | — |
| cross_framing | yes | bounded (wide) | — |
| era_collision | yes | bounded (wide) | — |
