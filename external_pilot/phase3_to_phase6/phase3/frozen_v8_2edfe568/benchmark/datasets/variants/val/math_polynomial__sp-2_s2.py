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

def fn_poly_normalize(p: Poly) -> Poly:
    """Remove trailing zero coefficients. Returns [0] for zero polynomial."""
    if not p:
        return [0]
    result = list(p)
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return result

def fn_poly_eval(p: Poly, x: float) -> float:
    """Evaluate polynomial p at x using Horner's method."""
    p = fn_poly_normalize(p)
    result = 0.0
    for coeff in reversed(p):
        result = result * x + coeff
    return result

def fn_poly_add(p: Poly, q: Poly) -> Poly:
    """Return p + q as a new polynomial."""
    n = max(len(p), len(q))
    result = [0.0] * n
    for (i, c) in enumerate(p):
        result[i] += c
    for (i, c) in enumerate(q):
        result[i] += c
    return fn_poly_normalize(result)

def fn_poly_mul(p: Poly, q: Poly) -> Poly:
    """Return p × q as a new polynomial (coefficient convolution)."""
    if not p or not q:
        return [0]
    result = [0.0] * (len(p) + len(q) - 1)
    for (i, a) in enumerate(p):
        for (j, b) in enumerate(q):
            result[i + j] += a * b
    return fn_poly_normalize(result)

def fn_poly_derivative(p: Poly) -> Poly:
    """Return the formal derivative of polynomial p."""
    p = fn_poly_normalize(p)
    if len(p) == 1:
        return [0]
    return [i * p[i] for i in range(1, len(p))]

def fn_poly_roots_bisection(p: Poly, a: float, b: float, tol: float=1e-08) -> float:
    """
    Find one real root of polynomial p in interval [a, b] via bisection.

    Raises ValueError if p(a) and p(b) have the same sign (no sign change).
    Raises ValueError if a ≥ b.
    """
    if a >= b:
        raise ValueError(f'bisection requires a < b, got a={a}, b={b}')
    (fa, fb) = (fn_poly_eval(p, a), fn_poly_eval(p, b))
    if fa * fb > 0:
        raise ValueError(f'f(a)={fa:.4f} and f(b)={fb:.4f} have same sign; no guaranteed root in [{a},{b}]')
    while (b - a) / 2 > tol:
        mid = (a + b) / 2
        fm = fn_poly_eval(p, mid)
        if fm == 0:
            return mid
        if fa * fm < 0:
            (b, fb) = (mid, fm)
        else:
            (a, fa) = (mid, fm)
    return (a + b) / 2

def fn_test_polynomial():
    p = [1, 2, 1]
    q = [-1, 1]
    assert fn_poly_eval(p, 2) == 9.0
    assert fn_poly_eval(p, 0) == 1.0
    assert fn_poly_eval(q, 1) == 0.0
    r = fn_poly_add(p, q)
    assert r == [0.0, 3.0, 1.0]
    m = fn_poly_mul([1, 1], [-1, 1])
    assert m == [-1.0, 0.0, 1.0]
    d = fn_poly_derivative(p)
    assert d == [2.0, 2.0]
    assert fn_poly_derivative([5]) == [0]
    p_sq = [-2, 0, 1]
    root = fn_poly_roots_bisection(p_sq, 1, 2, tol=1e-09)
    assert abs(root - 2 ** 0.5) < 1e-06, root
    p_cubic = [0, -1, 0, 1]
    root2 = fn_poly_roots_bisection(p_cubic, -2, -0.5, tol=1e-08)
    assert abs(root2 + 1) < 1e-06, root2
    try:
        fn_poly_roots_bisection([1, 0, 1], -1, 1)
        assert False
    except ValueError:
        pass
    assert fn_poly_normalize([1, 0, 0]) == [1]
    assert fn_poly_normalize([0]) == [0]
    assert fn_poly_normalize([]) == [0]
    assert fn_poly_mul([1, 2, 3], [0]) == [0]
    print('All polynomial tests passed.')
if __name__ == '__main__':
    fn_test_polynomial()
    p = [1, 2, 1]
    print(f'p(3) = {fn_poly_eval(p, 3)}')
    print(f"p' = {fn_poly_derivative(p)}")
    root = fn_poly_roots_bisection([-2, 0, 1], 1, 2)
    print(f'sqrt(2) via bisection: {root:.10f}')