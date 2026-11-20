"""
Check program overlap between SeqCoBench and SBG benchmarks (V10, V9c, V8, QuixBugs, BugsInPy).
"""
import json, ast, glob, os, sys, difflib

sys.path.insert(0, '/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')

def normalize_code(src):
    try:
        t = ast.parse(src)
        return ast.unparse(t).strip()
    except Exception:
        return src.strip()

def main():
    # Load SeqCoBench programs
    seqco_programs = set()
    import csv
    for sp in ('train', 'valid', 'test'):
        with open(f'/tmp/a5/sq_{sp}.csv') as f:
            for r in csv.DictReader(f):
                seqco_programs.add(r['original_code'])
    print(f"Total unique original programs in SeqCoBench: {len(seqco_programs)}")

    # Load V10 programs
    v10_programs = set()
    v10_pairs_file = '/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/benchmark/datasets/v10_independent/pairs_test.jsonl'
    if os.path.exists(v10_pairs_file):
        with open(v10_pairs_file) as f:
            for line in f:
                d = json.loads(line)
                v10_programs.add(d.get('program_id', ''))
                # also check source if available
    print(f"V10 program IDs: {sorted(v10_programs)}")

    # Check V8 / V9 programs
    v8_programs = set()
    v8_file = '/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/benchmark/datasets/v8_adversarial/pairs_val.jsonl'
    if os.path.exists(v8_file):
        with open(v8_file) as f:
            for line in f:
                d = json.loads(line)
                v8_programs.add(d.get('program_id', ''))
    print(f"V8 program IDs: {sorted(v8_programs)}")

    # Check QuixBugs programs
    qb_programs = set()
    qb_dir = '/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/external/quixbugs_python'
    if os.path.exists(qb_dir):
        for f in os.listdir(qb_dir):
            if f.endswith('.py') and not f.startswith('__'):
                qb_programs.add(f.replace('.py', ''))
    print(f"QuixBugs programs: {sorted(qb_programs)}")

    # Check function names in SeqCoBench
    seqco_fn_names = set()
    for src in seqco_programs:
        try:
            t = ast.parse(src)
            for n in t.body:
                if isinstance(n, ast.FunctionDef):
                    seqco_fn_names.add(n.name)
        except Exception:
            pass
    print(f"Total unique function names in SeqCoBench: {len(seqco_fn_names)}")

    # Overlaps
    qb_overlap = seqco_fn_names.intersection(qb_programs)
    print(f"Overlap between SeqCoBench function names and QuixBugs: {qb_overlap}")

    v10_prefix_overlap = set()
    for v in v10_programs:
        for s in seqco_fn_names:
            if s in v or v in s:
                v10_prefix_overlap.add((v, s))
    print(f"Potential name overlap with V10: {v10_prefix_overlap}")

if __name__ == '__main__':
    main()
