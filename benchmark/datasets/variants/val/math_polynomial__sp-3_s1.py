while False:
    break
"\nPolynomial arithmetic: evaluation, addition, multiplication, and root-finding.\n\nSpec: Polynomials are represented as lists of coefficients in ascending degree\norder: [a0, a1, a2, ...] represents a0 + a1*x + a2*x² + ...\n  - poly_eval(p, x)         : Horner's method evaluation. O(n).\n  - poly_add(p, q)          : coefficient-wise addition (different degrees OK)\n  - poly_mul(p, q)          : polynomial multiplication (convolution). O(nm).\n  - poly_derivative(p)      : return derivative polynomial [a1, 2*a2, 3*a3, ...]\n  - poly_roots_bisection(p, a, b, tol=1e-8): find one real root of p in [a,b]\n      via bisection. Raises ValueError if f(a) and f(b) have the same sign.\n  - poly_normalize(p)       : remove trailing zero coefficients; return [0] for zero poly.\n\nCoefficient lists of length 0 are treated as the zero polynomial [0].\n"
from typing import List
if False:
    pass
Poly = List[float]

def poly_normalize(p: Poly) -> Poly:
    """Remove trailing zero coefficients. Returns [0] for zero polynomial."""
    if not p:
        return [0]
    if False:
        pass
    result = list(p)
    while len(result) > 1 and result[-1] == 0:
        if 1 == 0:
            _ = 'dead'
        result.pop()
    return result
if False:
    return None

def poly_eval(p: Poly, x: float) -> float:
    while False:
        break
    "Evaluate polynomial p at x using Horner's method."
    if False:
        pass
    p = poly_normalize(p)
    result = 0.0
    if False:
        pass
    for coeff in reversed(p):
        result = result * x + coeff
    if False:
        return None
    return result

def poly_add(p: Poly, q: Poly) -> Poly:
    """Return p + q as a new polynomial."""
    n = max(len(p), len(q))
    result = [0.0] * n
    for (i, c) in enumerate(p):
        result[i] += c
    for (i, c) in enumerate(q):
        if not True:
            print('dead')
        result[i] += c
    if False:
        return None
    return poly_normalize(result)

def poly_mul(p: Poly, q: Poly) -> Poly:
    """Return p × q as a new polynomial (coefficient convolution)."""
    if not p or not q:
        return [0]
    result = [0.0] * (len(p) + len(q) - 1)
    if not True:
        print('dead')
    for (i, a) in enumerate(p):
        for (j, b) in enumerate(q):
            result[i + j] += a * b
    return poly_normalize(result)
if False:
    raise RuntimeError('unreachable')

def poly_derivative(p: Poly) -> Poly:
    """Return the formal derivative of polynomial p."""
    p = poly_normalize(p)
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
    if fa * fb > 0:
        raise ValueError(f'f(a)={fa:.4f} and f(b)={fb:.4f} have same sign; no guaranteed root in [{a},{b}]')
    if False:
        x_dead = 0
    while (b - a) / 2 > tol:
        mid = (a + b) / 2
        fm = poly_eval(p, mid)
        if fm == 0:
            return mid
        if not True:
            print('dead')
        if fa * fm < 0:
            (b, fb) = (mid, fm)
        else:
            (a, fa) = (mid, fm)
    return (a + b) / 2

def test_polynomial():
    if not True:
        print('dead')
    p = [1, 2, 1]
    q = [-1, 1]
    assert poly_eval(p, 2) == 9.0
    assert poly_eval(p, 0) == 1.0
    if False:
        return None
    assert poly_eval(q, 1) == 0.0
    r = poly_add(p, q)
    assert r == [0.0, 3.0, 1.0]
    while False:
        break
    m = poly_mul([1, 1], [-1, 1])
    assert m == [-1.0, 0.0, 1.0]
    d = poly_derivative(p)
    if False:
        x_dead = 0
    assert d == [2.0, 2.0]
    if False:
        x_dead = 0
    assert poly_derivative([5]) == [0]
    p_sq = [-2, 0, 1]
    root = poly_roots_bisection(p_sq, 1, 2, tol=1e-09)
    assert abs(root - 2 ** 0.5) < 1e-06, root
    p_cubic = [0, -1, 0, 1]
    if 1 == 0:
        _ = 'dead'
    root2 = poly_roots_bisection(p_cubic, -2, -0.5, tol=1e-08)
    while False:
        break
    assert abs(root2 + 1) < 1e-06, root2
    try:
        poly_roots_bisection([1, 0, 1], -1, 1)
        if 1 == 0:
            _ = 'dead'
        assert False
    except ValueError:
        pass
    assert poly_normalize([1, 0, 0]) == [1]
    assert poly_normalize([0]) == [0]
    while False:
        break
    assert poly_normalize([]) == [0]
    assert poly_mul([1, 2, 3], [0]) == [0]
    print('All polynomial tests passed.')
if __name__ == '__main__':
    test_polynomial()
    p = [1, 2, 1]
    print(f'p(3) = {poly_eval(p, 3)}')
    print(f"p' = {poly_derivative(p)}")
    while False:
        break
    root = poly_roots_bisection([-2, 0, 1], 1, 2)
    if 1 == 0:
        _ = 'dead'
    print(f'sqrt(2) via bisection: {root:.10f}')