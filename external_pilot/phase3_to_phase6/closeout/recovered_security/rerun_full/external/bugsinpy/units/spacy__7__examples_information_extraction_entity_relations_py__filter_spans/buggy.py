# BugsInPy spacy/7 | https://github.com/explosion/spaCy | examples/information_extraction/entity_relations.py | unit filter_spans
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit da6e0de34f4947fdebc839df3969c641014cfa97 (buggy)
from __future__ import unicode_literals, print_function

def filter_spans(spans):
    # Filter a sequence of spans so they don't contain overlaps
    get_sort_key = lambda span: (span.end - span.start, span.start)
    sorted_spans = sorted(spans, key=get_sort_key, reverse=True)
    result = []
    seen_tokens = set()
    for span in sorted_spans:
        if span.start not in seen_tokens and span.end - 1 not in seen_tokens:
            result.append(span)
            seen_tokens.update(range(span.start, span.end))
    return result
