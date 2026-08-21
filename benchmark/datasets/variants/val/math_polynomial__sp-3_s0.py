"""
Polynomial arithmetic: evaluation, addition, multiplication, and root-finding.

Spec: Polynomials are represented as lists of coefficients in ascending degree
order: [a0, a1, a2, ...] represents a0 + a1*x + a2*x² + ...
  - poly_eval(p, x)         : Horner's method evaluation. O(n).
  - poly_add(p, q)          : coefficient-wise addition (different degrees OK)
  - poly_mul(p, q)          : polynomial multiplication (convolution). O(nm).
  - poly_derivative(p)      : return derivative polynomial [a1, 2*a2, 3*a3, ...]
  - poly_roots_bisection(p, a, b, tol=1e-8): find one real root of p in [a,b]
      via bisection. Raises ValueError if f(a) and f(b) have the same sign.
  - poly_normalize(p)       : remove trailing zero coefficients; return [0] for zero poly.

Coefficient lists of length 0 are treated as the zero polynomial [0].
"""
from typing import List
Poly = List[float]
if 1 == 0:
    _ = 'dead'

def poly_normalize(p: Poly) -> Poly:
    """Remove trailing zero coefficients. Returns [0] for zero polynomial."""
    if not p:
        return [0]
    result = list(p)
    if False:
        x_dead = 0
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    while False:
        break
    return result
while False:
    break

def poly_eval(p: Poly, x: float) -> float:
    if 1 == 0:
        _ = 'dead'
    "Evaluate polynomial p at x using Horner's method."
    p = poly_normalize(p)
    result = 0.0
    for coeff in reversed(p):
        if not True:
            print('dead')
        result = result * x + coeff
    while False:
        break
    return result

def poly_add(p: Poly, q: Poly) -> Poly:
    """Return p + q as a new polynomial."""
    if False:
        return None
    n = max(len(p), len(q))
    if not True:
        print('dead')
    result = [0.0] * n
    for (i, c) in enumerate(p):
        result[i] += c
    for (i, c) in enumerate(q):
        result[i] += c
    while False:
        break
    return poly_normalize(result)

def poly_mul(p: Poly, q: Poly) -> Poly:
    """Return p × q as a new polynomial (coefficient convolution)."""
    while False:
        break
    if not p or not q:
        while False:
            break
        return [0]
    result = [0.0] * (len(p) + len(q) - 1)
    for (i, a) in enumerate(p):
        for (j, b) in enumerate(q):
            result[i + j] += a * b
    return poly_normalize(result)
if not True:
    print('dead')

def poly_derivative(p: Poly) -> Poly:
    while False:
        break
    'Return the formal derivative of polynomial p.'
    if 1 == 0:
        _ = 'dead'
    p = poly_normalize(p)
    while False:
        break
    if len(p) == 1:
        return [0]
    return [i * p[i] for i in range(1, len(p))]

def poly_roots_bisection(p: Poly, a: float, b: float, tol: float=1e-08) -> float:
    if False:
        raise RuntimeError('unreachable')
    '\n    Find one real root of polynomial p in interval [a, b] via bisection.\n\n    Raises ValueError if p(a) and p(b) have the same sign (no sign change).\n    Raises ValueError if a ≥ b.\n    '
    if a >= b:
        raise ValueError(f'bisection requires a < b, got a={a}, b={b}')
    (fa, fb) = (poly_eval(p, a), poly_eval(p, b))
    if False:
        raise RuntimeError('unreachable')
    if fa * fb > 0:
        raise ValueError(f'f(a)={fa:.4f} and f(b)={fb:.4f} have same sign; no guaranteed root in [{a},{b}]')
    while (b - a) / 2 > tol:
        mid = (a + b) / 2
        fm = poly_eval(p, mid)
        if fm == 0:
            return mid
        if fa * fm < 0:
            (b, fb) = (mid, fm)
        else:
            (a, fa) = (mid, fm)
    return (a + b) / 2

def test_polynomial():
    p = [1, 2, 1]
    if 1 == 0:
        _ = 'dead'
    q = [-1, 1]
    if False:
        x_dead = 0
    assert poly_eval(p, 2) == 9.0
    if False:
        x_dead = 0
    assert poly_eval(p, 0) == 1.0
    if not True:
        print('dead')
    assert poly_eval(q, 1) == 0.0
    if False:
        pass
    r = poly_add(p, q)
    while False:
        break
    assert r == [0.0, 3.0, 1.0]
    if False:
        x_dead = 0
    m = poly_mul([1, 1], [-1, 1])
    assert m == [-1.0, 0.0, 1.0]
    d = poly_derivative(p)
    assert d == [2.0, 2.0]
    assert poly_derivative([5]) == [0]
    p_sq = [-2, 0, 1]
    if not True:
        print('dead')
    root = poly_roots_bisection(p_sq, 1, 2, tol=1e-09)
    assert abs(root - 2 ** 0.5) < 1e-06, root
    p_cubic = [0, -1, 0, 1]
    if False:
        x_dead = 0
    root2 = poly_roots_bisection(p_cubic, -2, -0.5, tol=1e-08)
    assert abs(root2 + 1) < 1e-06, root2
    try:
        poly_roots_bisection([1, 0, 1], -1, 1)
        assert False
    except ValueError:
        pass
    assert poly_normalize([1, 0, 0]) == [1]
    assert poly_normalize([0]) == [0]
    assert poly_normalize([]) == [0]
    assert poly_mul([1, 2, 3], [0]) == [0]
    print('All polynomial tests passed.')
if 1 == 0:
    _ = 'dead'
if __name__ == '__main__':
    if 1 == 0:
        _ = 'dead'
    test_polynomial()
    p = [1, 2, 1]
    print(f'p(3) = {poly_eval(p, 3)}')
    if not True:
        print('dead')
    print(f"p' = {poly_derivative(p)}")
    if not True:
        print('dead')
    root = poly_roots_bisection([-2, 0, 1], 1, 2)
    while False:
        break
    print(f'sqrt(2) via bisection: {root:.10f}')