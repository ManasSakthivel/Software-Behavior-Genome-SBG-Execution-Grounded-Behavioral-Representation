# Power / CI-width scaling. Pure arithmetic; no data, no SBG. Assumptions are stated in the report.
import math
from statistics import NormalDist as N
z=N().inv_cdf
hw19=(0.068029+0.068992)/2   # V10 H4 CI [-0.068992, 0.068029], k=19 programs (V10_INDEPENDENT_EVALUATION.json)
sig=hw19*math.sqrt(19)/1.96
print('V10 half-width@k=19 =',round(hw19,4),' implied sigma_eff = hw*sqrt(k)/1.96 =',round(sig,3))
print('\nk needed for a 95% CI half-width h  (hw = 1.96*sigma/sqrt(k)):')
for s in (0.152,0.20,0.25):
    print(' sigma',s,{h:math.ceil((1.96*s/h)**2) for h in (0.07,0.05,0.04,0.03)})
m=4; a_holm=0.05/m
print(f'\nplanning table (two-sided, 80 pct power; Holm worst-case alpha=0.05/{m})')
print('sigma   k   hw95   MDE(a=.05)  MDE(Holm)')
for s in (0.152,0.20,0.25):
    for k in (36,60,88,97,188):
        print(f'{s:5.3f} {k:4d} {1.96*s/math.sqrt(k):6.3f} {(z(.975)+z(.8))*s/math.sqrt(k):10.3f} {(z(1-a_holm/2)+z(.8))*s/math.sqrt(k):10.3f}')
