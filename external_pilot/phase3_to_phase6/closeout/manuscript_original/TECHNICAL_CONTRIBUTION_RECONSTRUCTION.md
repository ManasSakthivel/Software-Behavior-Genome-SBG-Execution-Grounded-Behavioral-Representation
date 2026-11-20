# Technical contribution reconstruction
Supersedes nothing; linked from README.md.
- System model: `problem.tex` (notation Table 4, Definitions, Remarks 1-2, Propositions 1-4).
- ERS: formal Definition (`ers.tex`) transcribes `sbgv8/ers.py:_eval` (tol 1e-6 monotone, 0.02 invariance; P8 needs integrity_ok=0 and INS).
- Algorithms 1-6 checked against code in round 2 (hash chain at record level; integrity before witness in `calibrate.Model.decide`). Pre/postconditions are only partly stated; this remains an editorial gap.
- Architecture: Fig. 2, 3, Table 5. Trust boundaries: Fig. 6, Table 10.
- Complexity (Table 7): derived from code; only wall time is measured (median 2.8 s, p90 3.6 s, max 20.3 s per pair, 932 s for 312; shared host, load 5.9-9.0, not a performance experiment, no overhead claim).
- Not shown: predictive benefit of CEC/ERS (RQ4 negative, underpowered).
