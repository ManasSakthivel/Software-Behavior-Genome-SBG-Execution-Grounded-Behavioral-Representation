from typing import List
Poly = List[float]

def poly_normalize(p: Poly) -> Poly:
    if not p:
        return [0]
    result = list(p)
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return result

def poly_eval(p: Poly, x: float) -> float:
    p = poly_normalize(p)
    result = 0.0
    for coeff in reversed(p):
        result = result * x + coeff
    return result

def poly_add(p: Poly, q: Poly) -> Poly:
    n = max(len(p), len(q))
    result = [0.0] * n
    for (i, c) in enumerate(p):
        result[i] += c
    for (i, c) in enumerate(q):
        result[i] += c
    return poly_normalize(result)

def poly_mul(p: Poly, q: Poly) -> Poly:
    if not p or not q:
        return [0]
    result = [0.0] * (len(p) + len(q) - 1)
    for (i, a) in enumerate(p):
        for (j, b) in enumerate(q):
            result[i + j] += a * b
    return poly_normalize(result)

def poly_derivative(p: Poly) -> Poly:
    p = poly_normalize(p)
    if len(p) == 1:
        return [0]
    return [i * p[i] for i in range(1, len(p))]

def poly_roots_bisection(p: Poly, a: float, b: float, tol: float=1e-08) -> float:
    if a >= b:
        raise ValueError(f'bisection requires a < b, got a={a}, b={b}')
    (fa, fb) = (poly_eval(p, a), poly_eval(p, b))
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
    q = [-1, 1]
    assert poly_eval(p, 2) == 9.0
    assert poly_eval(p, 0) == 1.0
    assert poly_eval(q, 1) == 0.0
    r = poly_add(p, q)
    assert r == [0.0, 3.0, 1.0]
    m = poly_mul([1, 1], [-1, 1])
    assert m == [-1.0, 0.0, 1.0]
    d = poly_derivative(p)
    assert d == [2.0, 2.0]
    assert poly_derivative([5]) == [0]
    p_sq = [-2, 0, 1]
    root = poly_roots_bisection(p_sq, 1, 2, tol=1e-09)
    assert abs(root - 2 ** 0.5) < 1e-06, root
    p_cubic = [0, -1, 0, 1]
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
if __name__ == '__main__':
    test_polynomial()
    p = [1, 2, 1]
    print(f'p(3) = {poly_eval(p, 3)}')
    print(f"p' = {poly_derivative(p)}")
    root = poly_roots_bisection([-2, 0, 1], 1, 2)
    print(f'sqrt(2) via bisection: {root:.10f}')