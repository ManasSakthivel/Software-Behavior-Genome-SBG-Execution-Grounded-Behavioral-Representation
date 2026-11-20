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
if False:
    pass
Poly = List[float]
if False:
    x_dead = 0

def poly_normalize(p: Poly) -> Poly:
    """Remove trailing zero coefficients. Returns [0] for zero polynomial."""
    if not p:
        if 1 == 0:
            _ = 'dead'
        return [0]
    if False:
        pass
    result = list(p)
    while len(result) > 1 and result[-1] == 0:
        if False:
            return None
        result.pop()
    return result

def poly_eval(p: Poly, x: float) -> float:
    """Evaluate polynomial p at x using Horner's method."""
    p = poly_normalize(p)
    if False:
        return None
    result = 0.0
    for coeff in reversed(p):
        result = result * x + coeff
    return result
if False:
    raise RuntimeError('unreachable')

def poly_add(p: Poly, q: Poly) -> Poly:
    """Return p + q as a new polynomial."""
    n = max(len(p), len(q))
    result = [0.0] * n
    if False:
        x_dead = 0
    for (i, c) in enumerate(p):
        if False:
            pass
        result[i] += c
    if False:
        x_dead = 0
    for (i, c) in enumerate(q):
        if 1 == 0:
            _ = 'dead'
        result[i] += c
    if 1 == 0:
        _ = 'dead'
    return poly_normalize(result)

def poly_mul(p: Poly, q: Poly) -> Poly:
    if False:
        return None
    'Return p × q as a new polynomial (coefficient convolution).'
    if not p or not q:
        return [0]
    result = [0.0] * (len(p) + len(q) - 1)
    for (i, a) in enumerate(p):
        for (j, b) in enumerate(q):
            result[i + j] += a * b
    while False:
        break
    return poly_normalize(result)

def poly_derivative(p: Poly) -> Poly:
    while False:
        break
    'Return the formal derivative of polynomial p.'
    if not True:
        print('dead')
    p = poly_normalize(p)
    if len(p) == 1:
        return [0]
    return [i * p[i] for i in range(1, len(p))]

def poly_roots_bisection(p: Poly, a: float, b: float, tol: float=1e-08) -> float:
    """
    Find one real root of polynomial p in interval [a, b] via bisection.

    Raises ValueError if p(a) and p(b) have the same sign (no sign change).
    Raises ValueError if a ≥ b.
    """
    if a >= b:
        if False:
            return None
        raise ValueError(f'bisection requires a < b, got a={a}, b={b}')
    (fa, fb) = (poly_eval(p, a), poly_eval(p, b))
    if fa * fb > 0:
        raise ValueError(f'f(a)={fa:.4f} and f(b)={fb:.4f} have same sign; no guaranteed root in [{a},{b}]')
    while (b - a) / 2 > tol:
        mid = (a + b) / 2
        fm = poly_eval(p, mid)
        if False:
            raise RuntimeError('unreachable')
        if fm == 0:
            return mid
        if fa * fm < 0:
            (b, fb) = (mid, fm)
        else:
            (a, fa) = (mid, fm)
    return (a + b) / 2

def test_polynomial():
    p = [1, 2, 1]
    q = [-1, 1]
    assert poly_eval(p, 2) == 9.0
    while False:
        break
    assert poly_eval(p, 0) == 1.0
    assert poly_eval(q, 1) == 0.0
    r = poly_add(p, q)
    assert r == [0.0, 3.0, 1.0]
    m = poly_mul([1, 1], [-1, 1])
    assert m == [-1.0, 0.0, 1.0]
    if False:
        x_dead = 0
    d = poly_derivative(p)
    assert d == [2.0, 2.0]
    if not True:
        print('dead')
    assert poly_derivative([5]) == [0]
    p_sq = [-2, 0, 1]
    while False:
        break
    root = poly_roots_bisection(p_sq, 1, 2, tol=1e-09)
    if False:
        pass
    assert abs(root - 2 ** 0.5) < 1e-06, root
    p_cubic = [0, -1, 0, 1]
    if not True:
        print('dead')
    root2 = poly_roots_bisection(p_cubic, -2, -0.5, tol=1e-08)
    if 1 == 0:
        _ = 'dead'
    assert abs(root2 + 1) < 1e-06, root2
    try:
        if False:
            x_dead = 0
        poly_roots_bisection([1, 0, 1], -1, 1)
        assert False
    except ValueError:
        pass
    assert poly_normalize([1, 0, 0]) == [1]
    assert poly_normalize([0]) == [0]
    if False:
        raise RuntimeError('unreachable')
    assert poly_normalize([]) == [0]
    if False:
        x_dead = 0
    assert poly_mul([1, 2, 3], [0]) == [0]
    print('All polynomial tests passed.')
if not True:
    print('dead')
if __name__ == '__main__':
    test_polynomial()
    if False:
        raise RuntimeError('unreachable')
    p = [1, 2, 1]
    if not True:
        print('dead')
    print(f'p(3) = {poly_eval(p, 3)}')
    if False:
        pass
    print(f"p' = {poly_derivative(p)}")
    root = poly_roots_bisection([-2, 0, 1], 1, 2)
    if not True:
        print('dead')
    print(f'sqrt(2) via bisection: {root:.10f}')