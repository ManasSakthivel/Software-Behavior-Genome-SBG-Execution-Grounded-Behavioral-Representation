"""
Independent verification script for Agent 3: SeqCoBench analysis, counts, and strata.
"""
import csv, sys, json, ast, difflib, copy, signal, collections, warnings, multiprocessing as mp

warnings.filterwarnings('ignore')
sys.dont_write_bytecode = True
csv.field_size_limit(10**8)
sys.path.insert(0, '/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')

from experiments.final.entry_policy import select_entry_structural, EntryPointError, interfaces_correspond

def canon(s):
    try:
        return ast.unparse(ast.parse(s)).splitlines()
    except SyntaxError:
        return None

def esize(a, b):
    A, B = canon(a), canon(b)
    if A is None or B is None:
        return None
    return sum(1 for l in difflib.unified_diff(A, B, lineterm='', n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---'))

class TO(Exception):
    pass

def _h(*a):
    raise TO()

def oracle(src, name, inputs):
    ns = {}
    signal.signal(signal.SIGALRM, _h)
    signal.setitimer(signal.ITIMER_REAL, 2.0)
    try:
        exec(compile(src, '<m>', 'exec'), ns)
    except BaseException as e:
        return ('load_error',)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    fn = ns.get(name)
    if fn is None:
        return ('no_fn',)
    outs = []
    for x in copy.deepcopy(inputs):
        signal.setitimer(signal.ITIMER_REAL, 1.0)
        try:
            a = x if isinstance(x, tuple) else (x,)
            outs.append(('ok', repr(fn(*a))[:300]))
        except BaseException as e:
            outs.append(('exc', type(e).__name__))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
    return ('ok', outs)

def shape(src, name):
    try:
        t = ast.parse(src)
        f = [n for n in t.body if isinstance(n, ast.FunctionDef) and n.name == name]
        if not f:
            return (False, False)
        f = f[0]
        br = any(isinstance(n, (ast.If, ast.IfExp)) for n in ast.walk(f))
        lp = any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(f)) or any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == name for n in ast.walk(f)
        )
        return (br, lp)
    except Exception:
        return (False, False)

def evaluate_program(args):
    split, orig, rows = args
    try:
        do = select_entry_structural(orig)
    except EntryPointError as e:
        return (split, orig[:0], 'no_entry', [])
    ro = oracle(orig, do.name, do.inputs)
    if ro[0] != 'ok':
        return (split, '', 'orig_fail', [])
    if any(x[0] == 'exc' for x in ro[1]):
        return (split, '', 'orig_exc', [])
    out = []
    for r in rows:
        t = r['transformed_code']
        lab = r['label']
        tr = r['transformation']
        e = esize(orig, t)
        try:
            dt = select_entry_structural(t)
        except EntryPointError:
            out.append((lab, tr, e, 'variant_no_entry', False))
            continue
        ok_iface = interfaces_correspond(do, dt) and dt.name == do.name
        rt = oracle(t, do.name, do.inputs) if dt.name == do.name else ('name_changed',)
        if rt[0] != 'ok':
            out.append((lab, tr, e, 'variant_' + rt[0], ok_iface))
            continue
        out.append((lab, tr, e, 'same' if rt[1] == ro[1] else 'diff', ok_iface))
    return (split, shape(orig, do.name), 'eligible', out)

if __name__ == '__main__':
    jobs = []
    splits = {
        'train': '/tmp/a5/sq_train.csv',
        'valid': '/tmp/a5/sq_valid.csv',
        'test': '/tmp/a5/sq_test.csv'
    }
    for sp, path in splits.items():
        with open(path) as f:
            R = list(csv.DictReader(f))
        P = collections.OrderedDict()
        for r in R:
            if 'dissimilar' in r['transformation']:
                continue
            P.setdefault(r['original_code'], []).append(r)
        for o, rows in P.items():
            jobs.append((sp, o, rows))
    
    prog_counts = collections.Counter()
    PER = []
    
    with mp.Pool(8, maxtasksperchild=25) as pool:
        for sp, sh, status, out in pool.imap_unordered(evaluate_program, jobs, chunksize=2):
            prog_counts[(sp, status)] += 1
            if status != 'eligible':
                continue
            c = collections.Counter()
            for t in out:
                lab, tr, e, res, iface = t[0], t[1], t[2], t[3], t[4]
                cls = 'SP' if lab == '1' else 'SA'
                if res in ('same', 'diff') and iface is False:
                    c['iface_excluded'] += 1
                    continue
                # Matched stratum definition: edit size == 2 AND (SP preserves oracle output OR SA alters oracle output)
                if e == 2:
                    if cls == 'SP' and res == 'same':
                        c['SP_in_stratum'] += 1
                    elif cls == 'SA' and res == 'diff':
                        c['SA_in_stratum'] += 1
                    elif cls == 'SA' and res == 'same':
                        c['SA_unwitnessed_at_e2'] += 1
                    elif cls == 'SP' and res == 'diff':
                        c['SP_violates_oracle_at_e2'] += 1
                if res in ('same', 'diff'):
                    c[f'{cls}_{res}_all'] += 1
            c['_split'] = sp
            c['_br'] = sh[0]
            c['_lp'] = sh[1]
            PER.append(dict(c))
    
    print('=== PROGRAM LEVEL STATUS ===')
    for k, v in sorted(prog_counts.items()):
        print(f'  {k[0]:6s} {k[1]:10s}: {v}')
    
    print('\n=== SPLIT LEVEL COUNTS ===')
    summary = {}
    for sp in ('train', 'valid', 'test', 'ALL'):
        P = [c for c in PER if sp == 'ALL' or c['_split'] == sp]
        both_e2 = [c for c in P if c.get('SP_in_stratum', 0) > 0 and c.get('SA_in_stratum', 0) > 0]
        any_e2 = [c for c in P if c.get('SP_in_stratum', 0) > 0 or c.get('SA_in_stratum', 0) > 0]
        sp_pairs = sum(c.get('SP_in_stratum', 0) for c in P)
        sa_pairs = sum(c.get('SA_in_stratum', 0) for c in P)
        summary[sp] = {
            'eligible_zero_exc': len(P),
            'with_both_classes_at_e2': len(both_e2),
            'with_any_class_at_e2': len(any_e2),
            'pairs_SP_e2': sp_pairs,
            'pairs_SA_e2': sa_pairs,
            'total_pairs_e2': sp_pairs + sa_pairs,
            'both_e2_branch': sum(1 for c in both_e2 if c['_br']),
            'both_e2_branch_and_loop_or_rec': sum(1 for c in both_e2 if c['_br'] and c['_lp']),
            'eligible_branch_and_loop_or_rec': sum(1 for c in P if c['_br'] and c['_lp']),
            'unwitnessed_mutations_at_e2': sum(c.get('SA_unwitnessed_at_e2', 0) for c in P),
            'corrupted_preserving_at_e2': sum(c.get('SP_violates_oracle_at_e2', 0) for c in P),
        }
        print(f"Split {sp:5s}: Eligible={summary[sp]['eligible_zero_exc']}, Both-at-e2={summary[sp]['with_both_classes_at_e2']}, SP_e2_pairs={summary[sp]['pairs_SP_e2']}, SA_e2_pairs={summary[sp]['pairs_SA_e2']}, Total_e2={summary[sp]['total_pairs_e2']}")
    
    with open('/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/paper/final_empirical_readiness_2026-11-05/agent_3/seqcobench_verified_counts.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print('\nWrote verified counts to seqcobench_verified_counts.json')
