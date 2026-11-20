"""
Check exact and structural overlap between SeqCoBench and V8/V9/V10/BugsInPy/QuixBugs.
"""
import ast, csv, json, os

def get_ast_dump(src):
    try:
        return ast.dump(ast.parse(src))
    except Exception:
        return None

def main():
    seqco_progs = {}
    for sp in ('train', 'valid', 'test'):
        with open(f'/tmp/a5/sq_{sp}.csv') as f:
            for r in csv.DictReader(f):
                code = r['original_code']
                if code not in seqco_progs:
                    seqco_progs[code] = (sp, r['dataset'])
    
    print(f"Loaded {len(seqco_progs)} unique original programs from SeqCoBench.")

    # Check V10 test dataset sources if available
    v10_file = '/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/benchmark/datasets/v10_independent/programs_test.json'
    if not os.path.exists(v10_file):
        # find programs json
        for root, dirs, files in os.walk('/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG'):
            for f in files:
                if 'v10' in f and f.endswith('.json') and 'program' in f:
                    print('Found potential V10 programs file:', os.path.join(root, f))
    
    # Check all python files in benchmark/
    bm_progs = {}
    for root, dirs, files in os.walk('/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/benchmark'):
        for f in files:
            if f.endswith('.py') and not f.startswith('__'):
                p = os.path.join(root, f)
                try:
                    with open(p) as fh:
                        bm_progs[p] = fh.read()
                except Exception:
                    pass
    print(f"Loaded {len(bm_progs)} files from benchmark/")

    # Compare code dumps
    seqco_dumps = {code: get_ast_dump(code) for code in seqco_progs}
    
    overlaps = []
    for bp, bcode in bm_progs.items():
        bdump = get_ast_dump(bcode)
        if not bdump: continue
        for scode, sdump in seqco_dumps.items():
            if sdump and bdump == sdump:
                overlaps.append((bp, scode[:50]))
    
    print(f"Exact AST matches between benchmark code and SeqCoBench: {len(overlaps)}")
    if overlaps:
        for bp, sc in overlaps[:5]:
            print(f"  {bp} <-> {sc}")

if __name__ == '__main__':
    main()
