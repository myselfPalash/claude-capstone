"""Unit tests for app.validation (M6 strict types, L1 PATCH, L2 code points)."""
import pytest

from app.validation import (
    ValidationError,
    validate_completed,
    validate_create_payload,
    validate_description,
    validate_patch_payload,
)


def test_app_fixture_uses_temp_db(app, client, db_path):
    assert app.config["TESTING"] is True
    assert client is not None


def test_description_trimmed():
    assert validate_description("  buy milk \n") == "buy milk"


@pytest.mark.parametrize("value", ["", "   ", "\t\n "])
def test_description_empty_or_whitespace_rejected(value):
    with pytest.raises(ValidationError):
        validate_description(value)


def test_description_255_ok_256_rejected():
    assert validate_description("a" * 255) == "a" * 255
    with pytest.raises(ValidationError):
        validate_description("a" * 256)


def test_description_counts_code_points_not_bytes():
    # 255 four-byte code points is accepted; 256 is rejected.
    assert validate_description("\U0001F600" * 255) == "\U0001F600" * 255
    with pytest.raises(ValidationError):
        validate_description("\U0001F600" * 256)
    assert validate_description("é" * 255) == "é" * 255


def test_description_length_checked_after_trim():
    assert validate_description("  " + "a" * 255 + "  ") == "a" * 255


@pytest.mark.parametrize("value", [123, None, ["x"], {"a": 1}, True, 1.5])
def test_description_non_string_rejected(value):
    with pytest.raises(ValidationError):
        validate_description(value)


@pytest.mark.parametrize("value", [True, False])
def test_completed_real_bool_ok(value):
    assert validate_completed(value) is value


@pytest.mark.parametrize("value", [1, 0, "true", "false", None, [], 1.0])
def test_completed_non_bool_rejected(value):
    with pytest.raises(ValidationError):
        validate_completed(value)


def test_create_payload_ok_and_trims():
    assert validate_create_payload({"description": " hi "}) == {"description": "hi"}


@pytest.mark.parametrize("payload", [{}, {"description": None}, {"description": 5}])
def test_create_payload_rejected(payload):
    with pytest.raises(ValidationError):
        validate_create_payload(payload)


@pytest.mark.parametrize("payload", [[], "text", 5, None, True, [{"description": "x"}]])
def test_non_object_body_rejected(payload):
    with pytest.raises(ValidationError):
        validate_create_payload(payload)
    with pytest.raises(ValidationError):
        validate_patch_payload(payload)


def test_patch_valid_fields():
    assert validate_patch_payload({"description": " x "}) == {"description": "x"}
    assert validate_patch_payload({"completed": True}) == {"completed": True}
    assert validate_patch_payload({"description": "x", "completed": False}) == {
        "description": "x",
        "completed": False,
    }


def test_patch_empty_rejected():
    with pytest.raises(ValidationError):
        validate_patch_payload({})


def test_patch_unknown_field_rejected():
    with pytest.raises(ValidationError):
        validate_patch_payload({"foo": 1})
    with pytest.raises(ValidationError):
        validate_patch_payload({"description": "x", "id": 3})


@pytest.mark.parametrize(
    "payload",
    [
        {"description": None},
        {"completed": None},
        {"completed": 1},
        {"completed": 0},
        {"completed": "true"},
        {"description": 123},
        {"description": ""},
    ],
)
def test_patch_null_and_wrong_types_rejected(payload):
    with pytest.raises(ValidationError):
        validate_patch_payload(payload)
