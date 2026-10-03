from __future__ import unicode_literals, print_function

def filter_spans(spans):
    get_sort_key = lambda span: (span.end - span.start, -span.start)
    sorted_spans = sorted(spans, key=get_sort_key, reverse=True)
    output = []
    seen_tokens = set()
    for span in sorted_spans:
        if span.start not in seen_tokens and span.end - 1 not in seen_tokens:
            output.append(span)
        seen_tokens.update(range(span.start, span.end))
    output = sorted(output, key=lambda span: span.start)
    return output