# BugsInPy spacy/7 | https://github.com/explosion/spaCy | examples/information_extraction/entity_relations.py | unit filter_spans
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit 6f54e59fe7ccb3bacce896ed33d36b39f11cbfaf (fixed)
from __future__ import unicode_literals, print_function

def filter_spans(spans):
    # Filter a sequence of spans so they don't contain overlaps
    # For spaCy 2.1.4+: this function is available as spacy.util.filter_spans()
    get_sort_key = lambda span: (span.end - span.start, -span.start)
    sorted_spans = sorted(spans, key=get_sort_key, reverse=True)
    result = []
    seen_tokens = set()
    for span in sorted_spans:
        # Check for end - 1 here because boundaries are inclusive
        if span.start not in seen_tokens and span.end - 1 not in seen_tokens:
            result.append(span)
        seen_tokens.update(range(span.start, span.end))
    result = sorted(result, key=lambda span: span.start)
    return result
