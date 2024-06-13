import hashlib
import uuid


def generate_transaction_code(*fields: str) -> uuid.UUID:
    """
    Generates a UUID based on specific fields using custom hashing (SHA-256).

    Args:
        fields (str): Variable length argument list of fields to combine.

    Returns:
        uuid.UUID: The generated UUID.
    """
    combined = "-".join(fields)
    hash_obj = hashlib.sha256(combined.encode())
    return uuid.UUID(hash_obj.hexdigest()[:32])


