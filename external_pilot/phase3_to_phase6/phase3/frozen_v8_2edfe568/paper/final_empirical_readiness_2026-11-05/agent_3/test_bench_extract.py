"""
Test extraction on a small subset of SeqCoBench to benchmark execution time.
"""
import sys, os, csv, time

sys.path.insert(0, '/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')

from experiments.final.extraction import ProgramExecutor, extract_pair
from experiments.final.entry_policy import select_entry_structural

def test_extract():
    executor = ProgramExecutor()
    with open('/tmp/a5/sq_test.csv') as f:
        rows = list(csv.DictReader(f))
    
    t0 = time.time()
    count = 0
    for r in rows:
        if 'dissimilar' in r['transformation']: continue
        orig = r['original_code']
        trans = r['transformed_code']
        try:
            do = select_entry_structural(orig)
            dt = select_entry_structural(trans)
        except Exception:
            continue
        
        # Execute base and variant
        eb = executor.run_source(orig, 'test_base', do.name, do.inputs)
        ev = executor.run_source(trans, 'test_var', dt.name, dt.inputs)
        
        scores = extract_pair(eb, ev)
        print(f"Program {do.name}: scores={scores}")
        count += 1
        if count >= 3: break
    
    t1 = time.time()
    print(f"Processed {count} pairs in {t1 - t0:.2f} seconds ({ (t1-t0)/count:.2f} s/pair)")

if __name__ == '__main__':
    test_extract()
