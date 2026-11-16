#!/usr/bin/env python3
"""Extract text from a PDF with pypdf (installed to /tmp/pdfenv; analysis tool only). Usage: pdf2txt.py in.pdf out.txt"""
import sys; sys.path.insert(0,'/tmp/pdfenv')
from pypdf import PdfReader
r=PdfReader(sys.argv[1]); out=[]
for i,p in enumerate(r.pages):
    try: t=p.extract_text() or ''
    except Exception as e: t=f'[extract error {e}]'
    out.append(f'\n\n=== PAGE {i+1} ===\n'+t)
open(sys.argv[2],'w').write(''.join(out)); print(len(r.pages),'pages',sum(map(len,out)),'chars')
