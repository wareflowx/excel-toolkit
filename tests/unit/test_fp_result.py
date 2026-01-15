"""Unit tests for Result type."""

import pytest
from excel_toolkit.fp import ok, err, is_ok, is_err, unwrap, unwrap_or, unwrap_or_else, unwrap_err


class TestResultConstruction:
    """Tests for Result construction."""

    def test_ok_creates_ok_instance(self):
        """ok() should create Ok instance."""
        result = ok(42)
        assert is_ok(result)
        assert not is_err(result)

    def test_err_creates_err_instance(self):
        """err() should create Err instance."""
        result = err("error")
        assert is_err(result)
        assert not is_ok(result)

    def test_ok_with_none(self):
        """ok(None) should create Ok with None value."""
        result = ok(None)
        assert is_ok(result)
        assert unwrap(result) is None

    def test_ok_with_dataframe(self):
        """ok() should work with complex types."""
        import pandas as pd

        df = pd.DataFrame({"a": [1, 2, 3]})
        result = ok(df)
        assert is_ok(result)
        assert unwrap(result).equals(df)


class TestResultPredicates:
    """Tests for Result predicates."""

    def test_is_ok_true_for_ok(self):
        """is_ok() should return True for Ok."""
        assert is_ok(ok(42))

    def test_is_ok_false_for_err(self):
        """is_ok() should return False for Err."""
        assert not is_ok(err("error"))

    def test_is_err_true_for_err(self):
        """is_err() should return True for Err."""
        assert is_err(err("error"))

    def test_is_err_false_for_ok(self):
        """is_err() should return False for Ok."""
        assert not is_err(ok(42))


class TestResultUnwrap:
    """Tests for Result unwrapping."""

    def test_unwrap_ok(self):
        """unwrap() should extract value from Ok."""
        result = ok(42)
        assert unwrap(result) == 42

    def test_unwrap_err_raises(self):
        """unwrap() should raise UnwrapError for Err."""
        result = err("error")
        with pytest.raises(Exception):  # UnwrapError
            unwrap(result)

    def test_unwrap_or_with_ok(self):
        """unwrap_or() should return value for Ok."""
        result = ok(42)
        assert unwrap_or(result, 0) == 42

    def test_unwrap_or_with_err(self):
        """unwrap_or() should return default for Err."""
        result = err("error")
        assert unwrap_or(result, 0) == 0

    def test_unwrap_or_else_with_ok(self):
        """unwrap_or_else() should return value for Ok."""
        result = ok(42)
        assert unwrap_or_else(result, lambda: 0) == 42

    def test_unwrap_or_else_with_err(self):
        """unwrap_or_else() should return computed default for Err."""
        result = err("error")
        assert unwrap_or_else(result, lambda: 100) == 100

    def test_unwrap_err_with_err(self):
        """unwrap_err() should extract error from Err."""
        error = ValueError("test error")
        result = err(error)
        assert unwrap_err(result) is error

    def test_unwrap_err_with_ok_raises(self):
        """unwrap_err() should raise UnwrapError for Ok."""
        result = ok(42)
        with pytest.raises(Exception):  # UnwrapError
            unwrap_err(result)


class TestResultMap:
    """Tests for Result.map()."""

    def test_map_on_ok(self):
        """map() should apply function to Ok value."""
        result = ok(5)
        mapped = result.map(lambda x: x * 2)
        assert is_ok(mapped)
        assert unwrap(mapped) == 10

    def test_map_on_err(self):
        """map() should be ignored on Err."""
        result = err("error")
        mapped = result.map(lambda x: x * 2)
        assert is_err(mapped)
        assert unwrap_err(mapped) == "error"

    def test_map_chain(self):
        """map() can be chained."""
        result = ok(5)
        mapped = result.map(lambda x: x * 2).map(lambda x: x + 1)
        assert unwrap(mapped) == 11

    def test_map_type_transformation(self):
        """map() can transform types."""
        result = ok(42)
        mapped = result.map(lambda x: str(x))
        assert is_ok(mapped)
        assert unwrap(mapped) == "42"


class TestResultAndThen:
    """Tests for Result.and_then()."""

    def test_and_then_on_ok(self):
        """and_then() should apply function to Ok value."""
        result = ok(5)
        chained = result.and_then(lambda x: ok(x * 2))
        assert is_ok(chained)
        assert unwrap(chained) == 10

    def test_and_then_on_err(self):
        """and_then() should be ignored on Err."""
        result = err("error")
        chained = result.and_then(lambda x: ok(x * 2))
        assert is_err(chained)
        assert unwrap_err(chained) == "error"

    def test_and_then_chain(self):
        """and_then() can be chained."""
        result = ok(5)
        chained = (
            result.and_then(lambda x: ok(x * 2))
            .and_then(lambda x: ok(x + 1))
            .and_then(lambda x: ok(x // 3))
        )
        assert unwrap(chained) == 3

    def test_and_then_short_circuit_on_err(self):
        """and_then() should short-circuit on first Err."""
        result = ok(5)
        chained = result.and_then(lambda x: err("error")).and_then(
            lambda x: ok(x * 2)
        )
        assert is_err(chained)
        assert unwrap_err(chained) == "error"


class TestResultOrElse:
    """Tests for Result.or_else()."""

    def test_or_else_on_ok(self):
        """or_else() should return Ok, ignore default."""
        result = ok(42)
        fallback = ok(0)
        assert result.or_else(fallback) is result

    def test_or_else_on_err(self):
        """or_else() should return default for Err."""
        result = err("error")
        fallback = ok(0)
        assert result.or_else(fallback) is fallback

    def test_or_else_try_with_ok(self):
        """or_else_try() should return Ok, ignore fn."""
        result = ok(42)
        assert result.or_else_try(lambda: ok(0)) is result

    def test_or_else_try_with_err(self):
        """or_else_try() should return result of fn for Err."""
        result = err("error")
        fallback = ok(0)
        assert result.or_else_try(lambda: fallback) is fallback


class TestResultImmutability:
    """Tests for Result immutability."""

    def test_ok_is_immutable(self):
        """Ok instances should be immutable."""
        result = ok(42)
        with pytest.raises(Exception):  # FrozenInstanceError
            result._value = 100

    def test_err_is_immutable(self):
        """Err instances should be immutable."""
        result = err("error")
        with pytest.raises(Exception):  # FrozenInstanceError
            result._error = "new error"


class TestResultEquality:
    """Tests for Result equality."""

    def test_ok_equality(self):
        """Ok instances should be equal if values are equal."""
        result1 = ok(42)
        result2 = ok(42)
        assert result1 == result2

    def test_ok_inequality(self):
        """Ok instances should not be equal if values differ."""
        result1 = ok(42)
        result2 = ok(43)
        assert result1 != result2

    def test_err_equality(self):
        """Err instances should be equal if errors are equal."""
        error = ValueError("test")
        result1 = err(error)
        result2 = err(error)
        assert result1 == result2

    def test_ok_err_inequality(self):
        """Ok and Err should never be equal."""
        assert ok(42) != err(42)
