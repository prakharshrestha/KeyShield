
"""
SecureVault - Secure Credential Sharing

Cryptographic algorithms:
- Ephemeral ECDH (SECP256R1)
- HKDF-SHA256
- AES-256-GCM
- Ed25519 digital signatures
"""

import os
import json
import base64
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from key_exchange import (
    generate_key_pair,
    export_public_key,
    import_public_key,
    generate_exchange_salt,
    derive_shared_key
)


NONCE_LENGTH = 12
PACKAGE_VERSION = 1
AAD_PREFIX = b"SecureVault Credential Share v1"


def _b64(data):
    return base64.b64encode(data).decode("ascii")


def _unb64(value):
    return base64.b64decode(value, validate=True)


def _canonical_json(data):
    """Produce deterministic bytes for digital signing."""
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")


def _fingerprint(ecdh_public, signing_public):
    """Calculate the fingerprint of a complete public identity."""

    ecdh_bytes = ecdh_public.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    signing_bytes = signing_public.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    digest = hashlib.sha256(ecdh_bytes + signing_bytes).hexdigest()

    return ":".join(
        digest[i:i + 2]
        for i in range(0, len(digest), 2)
    )


def _identity_fingerprint(identity):
    return _fingerprint(
        identity["ecdh_public_key"],
        identity["signing_public_key"]
    )


def _aad(sender_fingerprint, recipient_fingerprint):
    return (
        AAD_PREFIX
        + b"|"
        + sender_fingerprint.encode("ascii")
        + b"|"
        + recipient_fingerprint.encode("ascii")
    )


def create_share_package(
    sender_identity,
    recipient_public_identity,
    credential
):
    """
    Encrypt a credential for a recipient.

    The sender signs the complete package using Ed25519.
    The recipient's ECDH public key is used for key agreement.

    Returns a JSON-serializable dictionary.
    """

    if not isinstance(credential, dict) or not credential:
        raise ValueError("Credential must be a non-empty dictionary.")

    # Validate the recipient's public identity.
    recipient_ecdh = recipient_public_identity["ecdh_public_key"]
    recipient_signing = recipient_public_identity["signing_public_key"]

    if not isinstance(recipient_ecdh, ec.EllipticCurvePublicKey):
        raise ValueError("Invalid recipient ECDH public key.")

    if not isinstance(recipient_ecdh.curve, ec.SECP256R1):
        raise ValueError("Unsupported recipient ECDH curve.")

    if not isinstance(recipient_signing, ed25519.Ed25519PublicKey):
        raise ValueError("Invalid recipient signing public key.")

    sender_fingerprint = _identity_fingerprint(sender_identity)
    recipient_fingerprint = _identity_fingerprint(
        recipient_public_identity
    )

    # Generate a fresh ephemeral ECDH key pair.
    ephemeral_private, ephemeral_public = generate_key_pair()

    salt = generate_exchange_salt()

    # Derive the AES-256 key.
    aes_key = derive_shared_key(
        ephemeral_private,
        recipient_ecdh,
        salt
    )

    nonce = os.urandom(NONCE_LENGTH)

    plaintext = _canonical_json(credential)

    # Authenticate sender and recipient identity context.
    associated_data = _aad(
        sender_fingerprint,
        recipient_fingerprint
    )

    ciphertext = AESGCM(aes_key).encrypt(
        nonce,
        plaintext,
        associated_data
    )

    # Export only the ephemeral public key.
    ephemeral_public_pem = export_public_key(
        ephemeral_public
    ).decode("utf-8")

    # Construct the package fields.
    package = {
        "version": PACKAGE_VERSION,
        "algorithm": "ECDH-SECP256R1+HKDF-SHA256+AES-256-GCM",
        "signature_algorithm": "Ed25519",
        "sender_fingerprint": sender_fingerprint,
        "recipient_fingerprint": recipient_fingerprint,
        "ephemeral_public_key": ephemeral_public_pem,
        "salt": _b64(salt),
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext)
    }

    # Sign all package fields.
    signature = sender_identity["signing_private_key"].sign(
        _canonical_json(package)
    )

    package["signature"] = _b64(signature)

    return package


def open_share_package(
    receiver_identity,
    package,
    trusted_sender_identity
):
    """
    Verify and decrypt a received credential package.

    trusted_sender_identity must be independently imported
    and its fingerprint verified through a trusted channel.
    """

    required_fields = {
        "version",
        "algorithm",
        "signature_algorithm",
        "sender_fingerprint",
        "recipient_fingerprint",
        "ephemeral_public_key",
        "salt",
        "nonce",
        "ciphertext",
        "signature"
    }

    if not isinstance(package, dict):
        raise ValueError("Invalid sharing package.")

    if set(package.keys()) != required_fields:
        raise ValueError("Missing or unexpected package fields.")

    if package["version"] != PACKAGE_VERSION:
        raise ValueError("Unsupported sharing package version.")

    if package["algorithm"] != (
        "ECDH-SECP256R1+HKDF-SHA256+AES-256-GCM"
    ):
        raise ValueError("Unsupported encryption algorithm.")

    if package["signature_algorithm"] != "Ed25519":
        raise ValueError("Unsupported signature algorithm.")

    sender_fingerprint = _identity_fingerprint(
        trusted_sender_identity
    )

    receiver_fingerprint = _identity_fingerprint(
        receiver_identity
    )

    # Verify expected identities before decryption.
    if package["sender_fingerprint"] != sender_fingerprint:
        raise ValueError("Sender identity fingerprint mismatch.")

    if package["recipient_fingerprint"] != receiver_fingerprint:
        raise ValueError("This package was not created for this user.")

    # Verify sender's digital signature.
    unsigned_package = {
        key: value
        for key, value in package.items()
        if key != "signature"
    }

    signature = _unb64(package["signature"])

    trusted_sender_identity["signing_public_key"].verify(
        signature,
        _canonical_json(unsigned_package)
    )

    # Import the sender's ephemeral public key.
    ephemeral_public = import_public_key(
        package["ephemeral_public_key"].encode("utf-8")
    )

    salt = _unb64(package["salt"])
    nonce = _unb64(package["nonce"])
    ciphertext = _unb64(package["ciphertext"])

    if len(salt) != 16:
        raise ValueError("Invalid HKDF salt.")

    if len(nonce) != NONCE_LENGTH:
        raise ValueError("Invalid AES-GCM nonce.")

    # Derive the same AES key using receiver's private key.
    aes_key = derive_shared_key(
        receiver_identity["ecdh_private_key"],
        ephemeral_public,
        salt
    )

    associated_data = _aad(
        sender_fingerprint,
        receiver_fingerprint
    )

    # AES-GCM authenticates and decrypts the ciphertext.
    plaintext = AESGCM(aes_key).decrypt(
        nonce,
        ciphertext,
        associated_data
    )

    credential = json.loads(plaintext.decode("utf-8"))

    if not isinstance(credential, dict):
        raise ValueError("Invalid credential data.")

    return credential
