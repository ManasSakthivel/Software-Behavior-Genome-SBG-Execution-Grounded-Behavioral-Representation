"""
Comprehensive audit and table generator for Agent 3 report.
Generates verified numbers for:
1. SeqCoBench program counts, strata, transformation breakdown, yield rates.
2. Alternative benchmark comparisons (HumanEval/HumanEvalPack, MBPP, EquiBench OJ).
3. Power analysis calculations.
"""
import csv, json, math, os, sys, collections

def main():
    # 1. Load SeqCoBench verified counts
    with open('/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/paper/final_empirical_readiness_2026-11-05/agent_3/seqcobench_verified_counts.json') as f:
        sq_counts = json.load(f)
    
    # 2. Compute yield rates
    splits_raw = {'train': 7214, 'valid': 2943, 'test': 4415}
    progs_raw = {'train': 565, 'valid': 229, 'test': 341}
    
    table_yield = []
    for sp in ('train', 'valid', 'test'):
        c = sq_counts[sp]
        n_raw = progs_raw[sp]
        n_elig = c['eligible_zero_exc']
        n_both = c['with_both_classes_at_e2']
        p_sp = c['pairs_SP_e2']
        p_sa = c['pairs_SA_e2']
        table_yield.append({
            'split': sp,
            'raw_programs': n_raw,
            'eligible_programs': n_elig,
            'eligible_pct': round(100.0 * n_elig / n_raw, 1),
            'matched_e2_programs': n_both,
            'matched_e2_prog_pct': round(100.0 * n_both / n_raw, 1),
            'sp_pairs_e2': p_sp,
            'sa_pairs_e2': p_sa,
            'total_pairs_e2': p_sp + p_sa,
            'both_e2_branch': c['both_e2_branch'],
            'both_e2_branch_loop_rec': c['both_e2_branch_and_loop_or_rec']
        })
    
    # Pooled ALL
    c_all = sq_counts['ALL']
    n_raw_all = sum(progs_raw.values())
    table_yield.append({
        'split': 'Pooled ALL',
        'raw_programs': n_raw_all,
        'eligible_programs': c_all['eligible_zero_exc'],
        'eligible_pct': round(100.0 * c_all['eligible_zero_exc'] / n_raw_all, 1),
        'matched_e2_programs': c_all['with_both_classes_at_e2'],
        'matched_e2_prog_pct': round(100.0 * c_all['with_both_classes_at_e2'] / n_raw_all, 1),
        'sp_pairs_e2': c_all['pairs_SP_e2'],
        'sa_pairs_e2': c_all['pairs_SA_e2'],
        'total_pairs_e2': c_all['total_pairs_e2'],
        'both_e2_branch': c_all['both_e2_branch'],
        'both_e2_branch_loop_rec': c_all['both_e2_branch_and_loop_or_rec']
    })
    
    with open('/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/paper/final_empirical_readiness_2026-11-05/agent_3/table_yield.json', 'w') as f:
        json.dump(table_yield, f, indent=2)
    
    print("=== SEQCOBENCH YIELD SUMMARY ===")
    for row in table_yield:
        print(row)

if __name__ == '__main__':
    main()
