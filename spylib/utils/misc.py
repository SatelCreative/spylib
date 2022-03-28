import binascii
import os
from datetime import datetime, timezone

from .constants import ALPHABET


def now_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def get_unique_id() -> str:
    return random(length=10)


def random(length):
    """
    Generate and return a cryptographically-secure short random string
    of the specified length.
    """
    random_num = int(binascii.b2a_hex(os.urandom(length)), 16)
    return int_to_string(random_num, ALPHABET, padding=length)[:length]


def int_to_string(number, alphabet, padding=None):
    """
    Convert a number to a string, using the given alphabet.
    The output has the most significant digit first.
    """
    output = ''
    alpha_len = len(alphabet)
    while number:
        number, digit = divmod(number, alpha_len)
        output += alphabet[digit]
    if padding:
        remainder = max(padding - len(output), 0)
        output = output + alphabet[0] * remainder
    return output[::-1]
