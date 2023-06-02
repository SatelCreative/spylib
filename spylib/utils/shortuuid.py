# Code copied over from shortuuid package:
# https://github.com/skorokithakis/shortuuid/blob/v1.0.8/shortuuid/main.py
import binascii
import os

ALPHABET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def random(length):
    """Generate a cryptographically-secure short random string of the specified length."""
    random_num = int(binascii.b2a_hex(os.urandom(length)), 16)
    return int_to_string(random_num, ALPHABET, padding=length)[:length]


def int_to_string(number, alphabet, padding=None):
    """Convert a number to a string, using the given alphabet.

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
