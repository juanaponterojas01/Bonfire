from unittest.mock import patch

import pytest

from src.utils import render_prompt


def test_render_prompt_replaces_all_variables():
    """All placeholder variables are replaced with provided kwarg values."""
    mock_content = "Hello {name}, welcome to {place}!"
    with (
        patch("src.utils.Path.is_file", return_value=True),
        patch("src.utils.Path.read_text", return_value=mock_content),
    ):
        result = render_prompt("greeting", name="Alice", place="Wonderland")

    assert result == "Hello Alice, welcome to Wonderland!"


def test_render_prompt_raises_on_missing_template():
    """FileNotFoundError is raised when the template .md file does not exist."""
    with patch("src.utils.Path.is_file", return_value=False):
        with pytest.raises(FileNotFoundError, match="Template file not found"):
            render_prompt("nonexistent", var="value")


def test_render_prompt_raises_on_unreplaced_variables():
    """ValueError is raised when a {variable} placeholder has no matching kwarg."""
    mock_content = "Dear {name}, your order {order_id} is ready."
    with (
        patch("src.utils.Path.is_file", return_value=True),
        patch("src.utils.Path.read_text", return_value=mock_content),
    ):
        with pytest.raises(ValueError) as exc_info:
            render_prompt("order_tmpl", name="Bob")

    msg = str(exc_info.value)
    assert "Unreplaced variable(s)" in msg
    assert "order_tmpl.md" in msg
    assert "{order_id}" in msg


def test_render_prompt_preserves_raw_braces_in_text():
    """Raw curly braces (e.g. from JSON snippets) are not corrupted by replacement."""
    mock_content = (
        "Profile data:\n"
        '{ "skills": ["python", "sql"], "years": {years_experience} }\n'
        "End of profile."
    )
    with (
        patch("src.utils.Path.is_file", return_value=True),
        patch("src.utils.Path.read_text", return_value=mock_content),
    ):
        result = render_prompt("profile_tmpl", years_experience="5")

    assert '{ "skills": ["python", "sql"], "years": 5 }' in result
    assert "End of profile." in result


def test_render_prompt_replaces_multiple_occurrences():
    """The same variable placeholder is replaced everywhere it appears."""
    mock_content = "{greeting} Alice! {greeting} Bob! {greeting} Charlie!"
    with (
        patch("src.utils.Path.is_file", return_value=True),
        patch("src.utils.Path.read_text", return_value=mock_content),
    ):
        result = render_prompt("multi_greet", greeting="Hi")

    assert result == "Hi Alice! Hi Bob! Hi Charlie!"


def test_render_prompt_handles_substring_collisions():
    """Longer keys are replaced first to avoid corrupting shorter-key placeholders.

    Without descending-length sort, {name} would be replaced before {full_name},
    breaking the longer placeholder.
    """
    mock_content = "Name: {name}, Full Name: {full_name}"
    with (
        patch("src.utils.Path.is_file", return_value=True),
        patch("src.utils.Path.read_text", return_value=mock_content),
    ):
        result = render_prompt("collision", name="Alice", full_name="Alice Smith")

    assert result == "Name: Alice, Full Name: Alice Smith"


# ---------------------------------------------------------------------------
# Edge cases — non-string kwarg values
# ---------------------------------------------------------------------------


def test_render_prompt_converts_non_string_kwargs_via_str():
    """Non-string kwarg values are converted to strings (docstring contract)."""
    mock_content = "Count: {count}, Tags: {tags}"
    with (
        patch("src.utils.Path.is_file", return_value=True),
        patch("src.utils.Path.read_text", return_value=mock_content),
    ):
        result = render_prompt("tmpl", count=42, tags=["a", "b"])

    assert result == "Count: 42, Tags: ['a', 'b']"


# ---------------------------------------------------------------------------
# Edge cases — no kwargs supplied
# ---------------------------------------------------------------------------


def test_render_prompt_returns_unmodified_text_when_no_kwargs_and_no_placeholders():
    """When no kwargs are given and the template has no {placeholders},
    the text is returned unchanged."""
    mock_content = "This is a static prompt with no variables."
    with (
        patch("src.utils.Path.is_file", return_value=True),
        patch("src.utils.Path.read_text", return_value=mock_content),
    ):
        result = render_prompt("static_tmpl")

    assert result == mock_content


def test_render_prompt_raises_when_no_kwargs_but_placeholders_present():
    """ValueError is raised when the template contains {placeholders} but
    no kwargs are supplied to replace them."""
    mock_content = "Hello {name}, your score is {score}."
    with (
        patch("src.utils.Path.is_file", return_value=True),
        patch("src.utils.Path.read_text", return_value=mock_content),
    ):
        with pytest.raises(ValueError, match="Unreplaced variable"):
            render_prompt("scored_tmpl")


# ---------------------------------------------------------------------------
# Edge case — empty template
# ---------------------------------------------------------------------------


def test_render_prompt_handles_empty_template():
    """An empty template file returns an empty string without error."""
    with (
        patch("src.utils.Path.is_file", return_value=True),
        patch("src.utils.Path.read_text", return_value=""),
    ):
        result = render_prompt("empty_tmpl", name="Alice")

    assert result == ""


# ---------------------------------------------------------------------------
# Edge case — underscore and digit in variable names
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("template, kwargs, expected", [
    (
        "User: {user_name}, Age: {age}",
        {"user_name": "Alice", "age": "30"},
        "User: Alice, Age: 30",
    ),
    (
        "Item: {item_2}, Qty: {qty_1}",
        {"item_2": "Widget", "qty_1": "5"},
        "Item: Widget, Qty: 5",
    ),
])
def test_render_prompt_supports_underscores_and_digits_in_var_names(
    template, kwargs, expected,
):
    """Variable names with underscores and trailing digits are supported
    per the regex [a-zA-Z_][a-zA-Z0-9_]*."""
    with (
        patch("src.utils.Path.is_file", return_value=True),
        patch("src.utils.Path.read_text", return_value=template),
    ):
        result = render_prompt("tmpl", **kwargs)

    assert result == expected
