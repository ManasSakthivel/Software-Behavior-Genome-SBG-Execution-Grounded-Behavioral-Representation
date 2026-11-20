import csv,sys,collections,warnings
warnings.filterwarnings('ignore'); sys.dont_write_bytecode=True; csv.field_size_limit(10**8)
sys.path.insert(0,'/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')
from experiments.final.entry_policy import select_entry_structural, EntryPointError
from feas import go
if __name__=='__main__':
    out={}
    for sp in ('train','valid','test'):
        R=list(csv.DictReader(open(f'sq_{sp}.csv')))
        progs={}
        for r in R: progs.setdefault(r['original_code'],[]).append(r)
        c=collections.Counter(); ann=0
        elig=[]
        for src,rows in progs.items():
            try: d=select_entry_structural(src)
            except EntryPointError as e: c['no_entry:'+e.kind]+=1; continue
            a=go(src,d.name,d.inputs)
            if a[0]!='ok': c['fail']+=1; continue
            if any(x[0]=='exc' for x in a[1]): c['exceptions']+=1; continue
            c['eligible']+=1; elig.append(src)
        n_pairs=sum(len(progs[s]) for s in elig)
        print(sp,'programs',len(progs),'rows',len(R),dict(c),'rows_of_eligible_programs',n_pairs, flush=True)
