"""Single place for request validation rules.

Errors are raised as ValidationError carrying one message string; the API
layer maps it to a 400 response with the shape {"error": "<message>"}.
"""

MAX_DESCRIPTION_LENGTH = 255  # Unicode code points, after trimming
PATCH_FIELDS = frozenset({"description", "completed"})


class ValidationError(ValueError):
    """Raised when input fails validation. str(exc) is the client message."""


def require_object(payload):
    """Payload must be a JSON object (dict)."""
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object.")
    return payload


def validate_description(value):
    """Return the trimmed description or raise ValidationError."""
    if not isinstance(value, str):
        raise ValidationError("description must be a string.")
    text = value.strip()
    if not text:
        raise ValidationError("description must not be empty.")
    if len(text) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(
            "description must be at most %d characters." % MAX_DESCRIPTION_LENGTH
        )
    return text


def validate_completed(value):
    """Accept only real booleans (bool is a subclass of int, so 1/0 fail)."""
    if not isinstance(value, bool):
        raise ValidationError("completed must be a boolean.")
    return value


def validate_create_payload(payload):
    """Validate a POST body. Returns {"description": <trimmed>}."""
    require_object(payload)
    if "description" not in payload:
        raise ValidationError("description is required.")
    return {"description": validate_description(payload["description"])}


def validate_patch_payload(payload):
    """Validate a PATCH body. Returns a dict of cleaned known fields.

    Requires at least one known field; unknown fields and null values for
    known fields are rejected.
    """
    require_object(payload)
    unknown = sorted(str(k) for k in payload if k not in PATCH_FIELDS)
    if unknown:
        raise ValidationError("Unknown field(s): %s." % ", ".join(unknown))
    if not payload:
        raise ValidationError(
            "Provide at least one of: description, completed."
        )
    cleaned = {}
    if "description" in payload:
        cleaned["description"] = validate_description(payload["description"])
    if "completed" in payload:
        cleaned["completed"] = validate_completed(payload["completed"])
    return cleaned
