from uuid import uuid4


def generate_uuid() -> str:
    """Generate a stable string UUID for database and artifact records."""

    return str(uuid4())

