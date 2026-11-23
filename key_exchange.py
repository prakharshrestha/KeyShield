
"""
SecureVault - ECDH Key Exchange Module

Algorithms:
1. ECDH using SECP256R1
2. HKDF using SHA-256
3. SHA-256 public key fingerprint
"""

import os
import hashlib

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


# Configuration
CURVE = ec.SECP256R1()
KEY_LENGTH = 32
SALT_LENGTH = 16
HKDF_INFO = b"SecureVault Credential Sharing v1"


def generate_key_pair():
    """
    Generate an ECDH private and public key pair.

    Returns:
        tuple: (private_key, public_key)
    """
    private_key = ec.generate_private_key(CURVE)
    public_key = private_key.public_key()

    return private_key, public_key


def export_public_key(public_key):
    """
    Export the public key in PEM format.
    The public key can safely be shared with another user.
    """
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )


def import_public_key(public_key_data):
    """
    Import and validate another user's ECDH public key.
    """
    public_key = serialization.load_pem_public_key(public_key_data)

    if not isinstance(public_key, ec.EllipticCurvePublicKey):
        raise ValueError("Invalid key: Expected an EC public key.")

    if not isinstance(public_key.curve, ec.SECP256R1):
        raise ValueError("Invalid key: Unsupported elliptic curve.")

    return public_key


def generate_exchange_salt():
    """
    Generate a random, non-secret salt for HKDF.
    Both users must use the same salt.
    """
    return os.urandom(SALT_LENGTH)


def derive_shared_key(private_key, peer_public_key, salt):
    """
    Derive the same AES-256 key on both users' devices.

    Args:
        private_key: Current user's ECDH private key.
        peer_public_key: Other user's ECDH public key.
        salt: Shared HKDF salt.

    Returns:
        bytes: 32-byte derived encryption key.
    """
    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise ValueError("Invalid private key.")

    if not isinstance(peer_public_key, ec.EllipticCurvePublicKey):
        raise ValueError("Invalid public key.")

    if not isinstance(private_key.curve, ec.SECP256R1):
        raise ValueError("Unsupported private key curve.")

    if not isinstance(peer_public_key.curve, ec.SECP256R1):
        raise ValueError("Unsupported public key curve.")

    if not isinstance(salt, bytes) or len(salt) != SALT_LENGTH:
        raise ValueError("HKDF salt must be 16 bytes.")

    # ECDH: Calculate the common shared secret.
    shared_secret = private_key.exchange(
        ec.ECDH(),
        peer_public_key
    )

    # HKDF: Convert the shared secret into a 256-bit key.
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        info=HKDF_INFO
    ).derive(shared_secret)

    return derived_key


def get_public_key_fingerprint(public_key):
    """
    Generate a SHA-256 fingerprint for public key verification.
    """
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    fingerprint = hashlib.sha256(public_bytes).hexdigest()

    return ":".join(
        fingerprint[i:i + 2]
        for i in range(0, len(fingerprint), 2)
    )
