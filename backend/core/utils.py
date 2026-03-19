import uuid
import string
import random


def generate_invite_code(length: int = 8) -> str:
    """Genera un codice invito alfanumerico univoco."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


def normalize_barcode(barcode: str) -> str:
    """
    Normalizza un barcode EAN-8, EAN-13 o UPC-A.
    Rimuove spazi e caratteri non numerici.
    """
    return ''.join(filter(str.isdigit, barcode.strip()))
