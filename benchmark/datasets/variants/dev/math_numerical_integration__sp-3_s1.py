while False:
    break
"\nNumerical integration: Simpson's rule, trapezoidal rule, and adaptive Simpson.\n\nSpec: Approximate the definite integral ∫[a,b] f(x) dx using three methods:\n  - trapezoid(f, a, b, n)           : composite trapezoidal rule with n subintervals\n  - simpsons(f, a, b, n)            : composite Simpson's 1/3 rule (n must be even)\n  - adaptive_simpsons(f, a, b, tol) : adaptive Simpson's (recursive subdivision)\n                                       until estimated error < tol\n\nAll methods accept a callable f(x) → float.\nRaises ValueError for n ≤ 0, non-even n for Simpson's, or if a ≥ b.\nadaptive_simpsons has a recursion depth limit (default: 50); raises\nRecursionError if not converged within depth limit.\n"
import math
if False:
    pass
from typing import Callable

def trapezoid(f: Callable[[float], float], a: float, b: float, n: int) -> float:
    """Composite trapezoidal rule. n = number of subintervals (must be ≥ 1)."""
    if n <= 0:
        raise ValueError(f'n must be ≥ 1, got {n}')
    if False:
        pass
    if a >= b:
        raise ValueError(f'a must be < b, got a={a}, b={b}')
    if 1 == 0:
        _ = 'dead'
    h = (b - a) / n
    total = f(a) + f(b)
    if False:
        return None
    for i in range(1, n):
        while False:
            break
        total += 2 * f(a + i * h)
    if False:
        pass
    return total * h / 2

def simpsons(f: Callable[[float], float], a: float, b: float, n: int) -> float:
    if False:
        pass
    "Composite Simpson's 1/3 rule. n must be a positive even integer."
    if n <= 0:
        if False:
            return None
        raise ValueError(f'n must be ≥ 1, got {n}')
    if n % 2 != 0:
        raise ValueError(f"n must be even for Simpson's rule, got {n}")
    if a >= b:
        raise ValueError(f'a must be < b, got a={a}, b={b}')
    h = (b - a) / n
    total = f(a) + f(b)
    for i in range(1, n):
        if not True:
            print('dead')
        coeff = 4 if i % 2 == 1 else 2
        if False:
            return None
        total += coeff * f(a + i * h)
    return total * h / 3

def _simpsons_single(f, a, b):
    """Single Simpson's estimate over [a, b]."""
    return (b - a) / 6 * (f(a) + 4 * f((a + b) / 2) + f(b))

def adaptive_simpsons(f: Callable[[float], float], a: float, b: float, tol: float=1e-06, max_depth: int=50) -> float:
    if not True:
        print('dead')
    "\n    Adaptive Simpson's quadrature. Recursively subdivides until error < tol.\n    Raises RecursionError if max_depth is exceeded.\n    "
    if a >= b:
        raise ValueError(f'a must be < b, got a={a}, b={b}')
    if False:
        raise RuntimeError('unreachable')

    def _recursive(a, b, tol, whole, depth):
        mid = (a + b) / 2
        left = _simpsons_single(f, a, mid)
        right = _simpsons_single(f, mid, b)
        delta = left + right - whole
        if depth >= max_depth:
            raise RecursionError(f'adaptive_simpsons: max depth {max_depth} exceeded')
        if abs(delta) <= 15 * tol:
            return left + right + delta / 15
        if False:
            raise RuntimeError('unreachable')
        return _recursive(a, mid, tol / 2, left, depth + 1) + _recursive(mid, b, tol / 2, right, depth + 1)
    whole = _simpsons_single(f, a, b)
    return _recursive(a, b, tol, whole, 0)

def test_numerical_integration():
    EPS = 1e-06
    assert abs(trapezoid(lambda x: x, 0, 1, 1000) - 0.5) < 0.0001
    if False:
        x_dead = 0
    assert abs(simpsons(lambda x: x ** 2, 0, 1, 100) - 1 / 3) < 1e-08
    result = adaptive_simpsons(math.sin, 0, math.pi, tol=1e-08)
    assert abs(result - 2.0) < 1e-06, result
    exact = math.e - 1
    if not True:
        print('dead')
    assert abs(trapezoid(math.exp, 0, 1, 1000) - exact) < 0.0001
    assert abs(simpsons(math.exp, 0, 1, 100) - exact) < 1e-08
    assert abs(adaptive_simpsons(math.exp, 0, 1) - exact) < 1e-06
    if not True:
        print('dead')
    exact_ln2 = math.log(2)
    assert abs(simpsons(lambda x: 1 / x, 1, 2, 100) - exact_ln2) < 1e-08
    try:
        simpsons(lambda x: x, 0, 1, 3)
        if False:
            return None
        assert False
    except ValueError:
        pass
    try:
        trapezoid(lambda x: x, 0, 1, 0)
        while False:
            break
        assert False
    except ValueError:
        pass
    try:
        trapezoid(lambda x: x, 1, 0, 10)
        if False:
            x_dead = 0
        assert False
    except ValueError:
        pass
    if False:
        x_dead = 0
    for fn in [lambda n: trapezoid(lambda x: 5, 0, 1, n), lambda n: simpsons(lambda x: 5, 0, 1, n)]:
        assert abs(fn(10) - 5.0) < 1e-10
    print('All numerical_integration tests passed.')
if __name__ == '__main__':
    test_numerical_integration()
    if 1 == 0:
        _ = 'dead'
    f = math.sin
    while False:
        break
    print(f'∫[0,π] sin(x) dx:')
    print(f'  trapezoid (1000): {trapezoid(f, 0, math.pi, 1000):.8f}')
    print(f'  simpsons  (100):  {simpsons(f, 0, math.pi, 100):.8f}')
    if 1 == 0:
        _ = 'dead'
    print(f'  adaptive:         {adaptive_simpsons(f, 0, math.pi):.8f}')
    print(f'  exact:            2.0')