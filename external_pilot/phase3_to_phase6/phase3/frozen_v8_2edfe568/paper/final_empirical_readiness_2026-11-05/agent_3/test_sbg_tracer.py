"""
Test isolated SBG execution on a few SeqCoBench programs to check tracer compatibility.
"""
import sys, os, csv, json

sys.path.insert(0, '/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')

from sbg.tracer import trace_execution
from sbg.features import featurize_trace
from sbg.distance import compute_sbg_v3_distance, compute_temporal_distance, compute_state_distance, compute_v5_composite

def test_sbg():
    with open('/tmp/a5/sq_test.csv') as f:
        rows = list(csv.DictReader(f))
    
    # Pick first eligible program
    from experiments.final.entry_policy import select_entry_structural
    
    for r in rows:
        if 'dissimilar' in r['transformation']: continue
        orig = r['original_code']
        trans = r['transformed_code']
        try:
            do = select_entry_structural(orig)
            dt = select_entry_structural(trans)
        except Exception:
            continue
        
        print('Testing program:', do.name)
        # Trace original
        trace_a = trace_execution(orig, do.name, do.inputs)
        trace_b = trace_execution(trans, dt.name, dt.inputs)
        print('Trace A events:', len(trace_a), 'Trace B events:', len(trace_b))
        
        feat_a = featurize_trace(trace_a)
        feat_b = featurize_trace(trace_b)
        
        d_v3 = compute_sbg_v3_distance(feat_a, feat_b)
        d_temp = compute_temporal_distance(feat_a, feat_b)
        d_state = compute_state_distance(feat_a, feat_b)
        v5 = compute_v5_composite(d_v3, d_temp, d_state)
        print(f"Distances: V3={d_v3:.4f}, Temp={d_temp:.4f}, State={d_state:.4f}, V5={v5:.4f}")
        print("Transformation:", r['transformation'], "Label:", r['label'])
        break

if __name__ == '__main__':
    test_sbg()
