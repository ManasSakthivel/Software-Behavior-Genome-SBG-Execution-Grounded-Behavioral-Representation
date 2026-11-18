# Phase 2 consolidated tables (generated; exploratory, non-pristine data)

## E1
run1 vs run2 identical: 102/102

## E3 system metrics
| system | outcome | est | lo | hi | n | K |
|---|---|---|---|---|---|---|
| B1 | false_assurance | 0.2264150943 | 0.1194945086 | 0.3918918919 | 106 | 101 |
| B1 | detection | 0.7735849057 | 0.6086809636 | 0.8814442535 | 106 | 101 |
| B1 | abstention | 0.0 | 0.0 | 0.0 | 258 | 101 |
| B1 | false_alarm | 0.3026315789 | 0.1486486486 | 0.352460041 | 152 | 101 |
| B1+rep | false_assurance | 0.2264150943 | 0.1204819277 | 0.3896103896 | 106 | 101 |
| B1+rep | detection | 0.7735849057 | 0.6103896104 | 0.880209113 | 106 | 101 |
| B1+rep | abstention | 0.0 | 0.0 | 0.0 | 258 | 101 |
| B1+rep | false_alarm | 0.3026315789 | 0.1475409836 | 0.3519313305 | 152 | 101 |
| B3 | false_assurance | 0.1886792453 | 0.0970149254 | 0.337081918 | 106 | 101 |
| B3 | detection | 0.8113207547 | 0.6625 | 0.9044117647 | 106 | 101 |
| B3 | abstention | 0.0 | 0.0 | 0.0 | 258 | 101 |
| B3 | false_alarm | 0.3092105263 | 0.1470588235 | 0.3605150215 | 152 | 101 |
| B4 | false_assurance | 0.9905660377 | 0.9808917197 | 1.0 | 106 | 101 |
| B4 | detection | 0.0094339623 | 0.0 | 0.0191082803 | 106 | 101 |
| B4 | abstention | 0.0 | 0.0 | 0.0 | 258 | 101 |
| B4 | false_alarm | 0.0065789474 | 0.0 | 0.0095541401 | 152 | 101 |
| V7-B | false_assurance | 0.1226415094 | 0.0540540541 | 0.2361111111 | 106 | 101 |
| V7-B | detection | 0.7075471698 | 0.5454257768 | 0.8161764706 | 106 | 101 |
| V7-B | abstention | 0.4728682171 | 0.3533333333 | 0.5237291686 | 258 | 101 |
| V7-B | false_alarm | 0.0 | 0.0 | 0.0 | 152 | 101 |

## Derived gate counterfactual (NOT executed)
| variant | detection | false_assurance | n_div | false_alarm | abstention | false_assurance_rate |
|---|---|---|---|---|---|---|
| actual | 75 | 13 | 106 | 0 | 122 | 0.1226 |
| G_A_all_insufficient_to_NDO | 75 | 31 | 106 | 0 | 0 | 0.2925 |
| G_B_gate_reasons_only_to_NDO | 75 | 24 | 106 | 0 | 96 | 0.2264 |

## E4 variants
| variant | n | verdicts | levels |
|---|---|---|---|
| V0 | 321 | {'INSUFFICIENT': 157, 'DIVERGENT_OBSERVABLE': 84, 'NO_DIVERGENCE_OBSERVED': 71, 'NOT_DRIVEN': 9} | {'S1': 16, 'S2': 55} |
| V1 | 321 | {'INSUFFICIENT': 157, 'DIVERGENT_OBSERVABLE': 84, 'NO_DIVERGENCE_OBSERVED': 71, 'NOT_DRIVEN': 9} | {'S1': 16, 'S2': 55} |
| V2 | 321 | {'INSUFFICIENT': 157, 'DIVERGENT_OBSERVABLE': 84, 'NO_DIVERGENCE_OBSERVED': 71, 'NOT_DRIVEN': 9} | {'S1': 16, 'S2': 55} |
| V3 | 321 | {'INSUFFICIENT': 157, 'DIVERGENT_OBSERVABLE': 84, 'NO_DIVERGENCE_OBSERVED': 71, 'NOT_DRIVEN': 9} | {'S1': 16, 'S2': 55} |
| V4 | 321 | {'INSUFFICIENT': 157, 'DIVERGENT_OBSERVABLE': 84, 'NO_DIVERGENCE_OBSERVED': 71, 'NOT_DRIVEN': 9} | {'S1': 16, 'S2': 55} |
| V5 | 321 | {'INSUFFICIENT': 157, 'DIVERGENT_OBSERVABLE': 84, 'NO_DIVERGENCE_OBSERVED': 71, 'NOT_DRIVEN': 9} | {'S1': 16, 'S2': 55} |

## E5 variants
| variant | n | verdicts | levels |
|---|---|---|---|
| S2F06 | 321 | {'INSUFFICIENT': 157, 'DIVERGENT_OBSERVABLE': 84, 'NO_DIVERGENCE_OBSERVED': 71, 'NOT_DRIVEN': 9} | {'S2': 71} |
| S2F08 | 321 | {'INSUFFICIENT': 157, 'DIVERGENT_OBSERVABLE': 84, 'NO_DIVERGENCE_OBSERVED': 71, 'NOT_DRIVEN': 9} | {'S1': 16, 'S2': 55} |
| S2F09 | 321 | {'INSUFFICIENT': 157, 'DIVERGENT_OBSERVABLE': 84, 'NO_DIVERGENCE_OBSERVED': 71, 'NOT_DRIVEN': 9} | {'S1': 28, 'S2': 43} |

## E7 corruption suite
42/42 as expected
| source_class | case | expected | observed |
|---|---|---|---|
