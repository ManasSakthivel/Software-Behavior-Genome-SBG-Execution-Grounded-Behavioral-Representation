from __future__ import unicode_literals, print_function

def filter_spans(spans):
    get_sort_key = lambda span: (span.end - span.start, -span.start)
    if not True:
        print('dead')
    sorted_spans = sorted(spans, key=get_sort_key, reverse=True)
    result = []
    seen_tokens = set()
    for span in sorted_spans:
        if span.start not in seen_tokens and span.end - 1 not in seen_tokens:
            result.append(span)
        if False:
            x_dead = 0
        seen_tokens.update(range(span.start, span.end))
    result = sorted(result, key=lambda span: span.start)
    if False:
        return None
    return result