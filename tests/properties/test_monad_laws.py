"""Property-based tests for monad laws.

These tests verify that Result type satisfies the monad laws:
1. Left identity: return(x).and_then(f) == f(x)
2. Right identity: m.and_then(return) == m
3. Associativity: m.and_then(f).and_then(g) == m.and_then(lambda x: f(x).and_then(g))
"""

from hypothesis import given, strategies as st
import pytest
from excel_toolkit.fp import ok, err


class TestResultMonadLaws:
    """Monad law tests for Result type."""

    @given(st.integers(), st.integers())
    def test_result_left_identity(self, x, y):
        """return(x).and_then(f) == f(x)"""
        # Define function f
        f = lambda n: ok(n + y)

        # Left side: return(x).and_then(f)
        left = ok(x).and_then(f)

        # Right side: f(x)
        right = f(x)

        assert left == right

    @given(st.integers())
    def test_result_right_identity_ok(self, x):
        """m.and_then(return) == m for Ok"""
        m = ok(x)

        # m.and_then(return) should equal m
        result = m.and_then(ok)

        assert result == m

    def test_result_right_identity_err(self):
        """m.and_then(return) == m for Err"""
        m = err("error")

        # m.and_then(return) should equal m
        result = m.and_then(ok)

        assert result == m

    @given(st.integers(), st.integers(), st.integers())
    def test_result_associativity(self, x, y, z):
        """m.and_then(f).and_then(g) == m.and_then(lambda x: f(x).and_then(g))"""
        m = ok(x)

        # Define functions
        f = lambda n: ok(n + y)
        g = lambda n: ok(n * z)

        # Left side: (m.and_then(f)).and_then(g)
        left = m.and_then(f).and_then(g)

        # Right side: m.and_then(lambda x: f(x).and_then(g))
        right = m.and_then(lambda x: f(x).and_then(g))

        assert left == right

    @given(st.integers(), st.integers())
    def test_result_short_circuit(self, x, y):
        """Err should short-circuit through and_then"""
        m = err("error")

        f = lambda n: ok(n + x)
        g = lambda n: ok(n * y)

        # and_then on Err should always return Err
        assert m.and_then(f) == m
        assert m.and_then(f).and_then(g) == m


class TestResultPracticalUsage:
    """Practical usage patterns for Result."""

    @given(st.integers(min_value=0, max_value=100))
    def test_chain_successful_operations(self, x):
        """Chain multiple successful operations."""
        result = (
            ok(x)
            .and_then(lambda n: ok(n * 2))
            .and_then(lambda n: ok(n + 10))
            .and_then(lambda n: ok(n // 3))
        )

        from excel_toolkit.fp import is_ok, unwrap

        assert is_ok(result)
        # (((x * 2) + 10) // 3)
        assert unwrap(result) == ((x * 2) + 10) // 3

    @given(st.integers(min_value=0, max_value=50))
    def test_early_exit_on_error(self, x):
        """Chain should exit on first Err."""
        result = (
            ok(x)
            .and_then(lambda n: ok(n * 2) if n < 25 else err("too large"))
            .and_then(lambda n: ok(n + 10))
        )

        from excel_toolkit.fp import is_ok, is_err

        if x < 25:
            assert is_ok(result)
        else:
            assert is_err(result)
            from excel_toolkit.fp import unwrap_err
            assert unwrap_err(result) == "too large"

    @given(st.integers(), st.integers())
    def test_map_vs_and_then(self, x, y):
        """map preserves Err, and_then can change it."""
        result = err("error")

        # map preserves Err
        mapped = result.map(lambda n: n + x)
        from excel_toolkit.fp import is_err
        assert is_err(mapped)

        # and_then preserves Err
        chained = result.and_then(lambda n: ok(n + y))
        assert is_err(chained)

    @given(st.integers(), st.integers())
    def test_or_else_provides_fallback(self, x, y):
        """or_else provides fallback value."""
        result = ok(x)

        # Ok ignores or_else
        from excel_toolkit.fp import unwrap_or
        assert unwrap_or(result, y) == x

        result_err = err("error")
        assert unwrap_or(result_err, y) == y

    @given(st.integers(), st.integers())
    def test_or_else_try_lazy_evaluation(self, x, y):
        """or_else_try should evaluate lazily."""
        result = ok(x)

        counter = [0]

        def expensive_computation():
            counter[0] += 1
            return y

        # Ok should not evaluate the function
        from excel_toolkit.fp import unwrap_or_else
        assert unwrap_or_else(result, expensive_computation) == x
        assert counter[0] == 0

        # Err should evaluate the function
        result_err = err("error")
        assert unwrap_or_else(result_err, expensive_computation) == y
        assert counter[0] == 1
