import sys, pathlib, re
HERE = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent/"_ws"))
from experiments.final import external_java as J
src=(HERE.parent/"programs/COUNTVOWELS.java").read_text()
sp=re.sub(r"\bcount\b","n",src); sp=re.sub(r"\bi\b","k",sp)
sig=J.entry_signature("COUNTVOWELS",src); inp=J.canonical_inputs(sig); jin=J.inputs_to_java(sig,inp)
a=J.oracle_outputs("COUNTVOWELS",src,sig,jin); b=J.oracle_outputs("COUNTVOWELS",sp,sig,jin)
for i,(x,y,z) in enumerate(zip(inp,a,b)): print(i,repr(x)[:60],x and '',y,z, '<<DIFF' if y!=z else '')
print(sp)
