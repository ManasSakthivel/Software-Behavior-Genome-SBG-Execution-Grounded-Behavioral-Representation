| variant | n | pos/neg | clusters | AUROC | 95% CI (cluster bootstrap) | P(pos>neg) / P(tie) |
|---|---|---|---|---|---|---|
| bugsinpy ; v7 committed ; all pairs ; evaluated only | 147 | 41/106 | 39 | 0.409917 | [0.326232, 0.493946] (repo) | 0.33387 / 0.152094 |
| bugsinpy ; v7 committed ; all pairs ; unevaluated=0 | 200 | 55/145 | 51 | 0.433981 | [0.374132, 0.489897] (repo) | 0.279749 / 0.308464 |
| bugsinpy ; v7 committed ; SP-2 excluded ; evaluated only | 107 | 41/66 | 39 | 0.471545 | [0.380863, 0.561661] (repo) | 0.362528 / 0.218034 |
| bugsinpy ; v7 committed ; SP-2 excluded ; unevaluated=0 | 150 | 55/95 | 51 | 0.489856 | [0.427821, 0.548678] (repo) | 0.298756 / 0.382201 |
| quixbugs_canonical ; v7 committed ; all pairs ; evaluated only | 152 | 40/112 | 40 | 0.387723 | [0.284659, 0.503378] (repo) | 0.191295 / 0.392857 |
| quixbugs_canonical ; v7 committed ; all pairs ; unevaluated=0 | 152 | 40/112 | 40 | 0.387723 | [0.284659, 0.503378] (repo) | 0.191295 / 0.392857 |
| quixbugs_canonical ; v7 committed ; SP-2 excluded ; evaluated only | 112 | 40/72 | 40 | 0.450694 | [0.360069, 0.547297] (repo) | 0.195139 / 0.511111 |
| quixbugs_canonical ; v7 committed ; SP-2 excluded ; unevaluated=0 | 112 | 40/72 | 40 | 0.450694 | [0.360069, 0.547297] (repo) | 0.195139 / 0.511111 |
| quixbugs_declared ; v7 committed ; all pairs ; evaluated only | 99 | 24/75 | 28 | 0.702222 | [0.583636, 0.816576] (repo) | 0.6 / 0.204444 |
| quixbugs_declared ; v7 committed ; all pairs ; unevaluated=0 | 152 | 40/112 | 40 | 0.595536 | [0.513938, 0.681364] (repo) | 0.373214 / 0.444643 |
| quixbugs_declared ; v7 committed ; SP-2 excluded ; evaluated only | 72 | 24/48 | 28 | 0.668403 | [0.531556, 0.796875] (repo) | 0.588542 / 0.159722 |
| quixbugs_declared ; v7 committed ; SP-2 excluded ; unevaluated=0 | 112 | 40/72 | 40 | 0.564583 | [0.477113, 0.655921] (repo) | 0.36875 / 0.391667 |
| bugsinpy ; v8 rescore ; all pairs ; evaluated only | 147 | 41/106 | 39 | 0.4159 | [0.3223, 0.5144] (rescore) | 0.301427 / 0.228946 |
| bugsinpy ; v8 rescore ; all pairs ; unevaluated=0 (v8 dump rows only) | 147 | 41/106 | 39 | 0.4159 | [0.3223, 0.5144] (rescore) | 0.301427 / 0.228946 |
| bugsinpy ; v7 committed scores on the v8-dump pair set ; all pairs ; evaluated only | 147 | 41/106 | 39 | 0.409917 | [0.3262, 0.4939] (rescore) | 0.33387 / 0.152094 |
| bugsinpy ; v8 rescore ; SP-2 excluded ; evaluated only | 107 | 41/66 | 39 | 0.497044 | [0.4023, 0.5956] (rescore) | 0.333703 / 0.326681 |
| bugsinpy ; v8 rescore ; SP-2 excluded ; unevaluated=0 (v8 dump rows only) | 107 | 41/66 | 39 | 0.497044 | [0.4023, 0.5956] (rescore) | 0.333703 / 0.326681 |
| bugsinpy ; v7 committed scores on the v8-dump pair set ; SP-2 excluded ; evaluated only | 107 | 41/66 | 39 | 0.471545 | [0.3809, 0.5617] (rescore) | 0.362528 / 0.218034 |
| quixbugs_canonical ; v8 rescore ; all pairs ; evaluated only | 151 | 39/112 | 40 | 0.384158 | [0.2847, 0.4899] (rescore) | 0.171703 / 0.424908 |
| quixbugs_canonical ; v8 rescore ; all pairs ; unevaluated=0 (v8 dump rows only) | 152 | 40/112 | 40 | 0.381027 | [0.2846, 0.4832] (rescore) | 0.167411 / 0.427232 |
| quixbugs_canonical ; v7 committed scores on the v8-dump pair set ; all pairs ; evaluated only | 151 | 39/112 | 40 | 0.372024 | [0.2743, 0.4799] (rescore) | 0.170559 / 0.40293 |
| quixbugs_canonical ; v8 rescore ; SP-2 excluded ; evaluated only | 111 | 39/72 | 40 | 0.444444 | [0.3553, 0.5385] (rescore) | 0.176638 / 0.535613 |
| quixbugs_canonical ; v8 rescore ; SP-2 excluded ; unevaluated=0 (v8 dump rows only) | 112 | 40/72 | 40 | 0.441493 | [0.3549, 0.5329] (rescore) | 0.172222 / 0.538542 |
| quixbugs_canonical ; v7 committed scores on the v8-dump pair set ; SP-2 excluded ; evaluated only | 111 | 39/72 | 40 | 0.43661 | [0.3496, 0.528] (rescore) | 0.174501 / 0.524217 |
| bugsinpy ; v8 rescore + 53 v7-unevaluated rows scored 0 (200-pair population) ; all pairs ; unevaluated=0 | 200 | 55/145 | 51 | 0.43116 | [0.3629, 0.502] (rescore) | 0.237618 / 0.387085 |
| bugsinpy ; v8 rescore + 53 v7-unevaluated rows scored 0 (200-pair population) ; SP-2 excluded ; unevaluated=0 | 150 | 55/95 | 51 | 0.497225 | [0.4294, 0.5672] (rescore) | 0.256077 / 0.482297 |
