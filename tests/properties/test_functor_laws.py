"""Property-based tests for functor laws.

These tests verify that Result and Maybe types satisfy the functor laws:
1. Identity: map(id) == id
2. Composition: map(f ∘ g) == map(f) ∘ map(g)
"""

from hypothesis import given, strategies as st
import pytest
from excel_toolkit.fp import ok, err, some, nothing


class TestResultFunctorLaws:
    """Functor law tests for Result type."""

    @given(st.integers(), st.text())
    def test_result_functor_identity(self, x, error):
        """map(id) == id"""
        # Ok should preserve value
        result_ok = ok(x)
        assert result_ok.map(lambda y: y) == result_ok

        # Err should preserve error
        result_err = err(error)
        assert result_err.map(lambda y: y) == result_err

    @given(st.integers(), st.integers(), st.integers())
    def test_result_functor_composition_ok(self, x, y, z):
        """map(f ∘ g) == map(f) ∘ map(g) for Ok"""
        result = ok(x)

        # Compose f(g(x))
        f = lambda n: n + y
        g = lambda n: n * z
        compose_f_g = lambda n: f(g(n))

        # Left side: map(f ∘ g)
        left = result.map(compose_f_g)

        # Right side: map(f) ∘ map(g)
        right = result.map(g).map(f)

        assert left == right

    @given(st.integers(), st.integers(), st.text())
    def test_result_functor_composition_err(self, x, y, error):
        """map(f) preserves Err state"""
        result = err(error)

        # Any map on Err should return the same Err
        mapped1 = result.map(lambda n: n + x)
        mapped2 = result.map(lambda n: n * y)
        assert mapped1 == result
        assert mapped2 == result


class TestMaybeFunctorLaws:
    """Functor law tests for Maybe type."""

    @given(st.integers())
    def test_maybe_functor_identity(self, x):
        """map(id) == id"""
        # Some should preserve value
        maybe_some = some(x)
        assert maybe_some.map(lambda y: y) == maybe_some

        # Nothing should preserve Nothing
        maybe_nothing = nothing()
        assert maybe_nothing.map(lambda y: y) == maybe_nothing

    @given(st.integers(), st.integers(), st.integers())
    def test_maybe_functor_composition_some(self, x, y, z):
        """map(f ∘ g) == map(f) ∘ map(g) for Some"""
        maybe = some(x)

        # Compose f(g(x))
        f = lambda n: n + y
        g = lambda n: n * z
        compose_f_g = lambda n: f(g(n))

        # Left side: map(f ∘ g)
        left = maybe.map(compose_f_g)

        # Right side: map(f) ∘ map(g)
        right = maybe.map(g).map(f)

        assert left == right

    @given(st.integers(), st.integers())
    def test_maybe_functor_composition_nothing(self, x, y):
        """map(f) preserves Nothing state"""
        maybe = nothing()

        # Any map on Nothing should return Nothing
        mapped1 = maybe.map(lambda n: n + x)
        mapped2 = maybe.map(lambda n: n * y)
        assert mapped1 == maybe
        assert mapped2 == maybe
