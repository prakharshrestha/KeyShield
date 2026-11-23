
"""
SecureVault - Identity and Private Key Protection

Features:
1. ECDH key pair generation
2. Ed25519 signing key generation
3. PBKDF2-HMAC-SHA256 key derivation
4. AES-256-GCM private key encryption
5. Public identity export and import
6. Digital signature creation and verification
"""

import os
import json
import base64
import hashlib
import hmac
from pathlib import Path

from cryptography.exceptions import InvalidTag, InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# Configuration
PBKDF2_ITERATIONS = 200_000
SALT_LENGTH = 16
NONCE_LENGTH = 12
KEY_LENGTH = 32

PRIVATE_FILE = "identity_private.enc"
PUBLIC_FILE = "identity_public.json"

AAD = b"SecureVault Identity Keys v1"


def _derive_storage_key(master_password, salt):
    """Derive an AES-256 key from the master password."""

    if not isinstance(master_password, str) or not master_password:
        raise ValueError("Master password cannot be empty.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS
    )

    return kdf.derive(master_password.encode("utf-8"))


def _private_key_to_pem(private_key):
    """Serialize a private key into unencrypted PEM bytes.
    These bytes are encrypted before being written to disk.
    """

    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )


def _public_key_to_pem(public_key):
    """Serialize a public key into PEM format."""

    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )


def _build_public_identity(ecdh_private, signing_private):
    """Build the shareable public identity."""

    ecdh_public = ecdh_private.public_key()
    signing_public = signing_private.public_key()

    ecdh_pem = _public_key_to_pem(ecdh_public)
    signing_pem = _public_key_to_pem(signing_public)

    fingerprint_data = (
        ecdh_public.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        +
        signing_public.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )

    fingerprint = hashlib.sha256(fingerprint_data).hexdigest()

    return {
        "version": 1,
        "ecdh_public_key": ecdh_pem.decode("utf-8"),
        "signing_public_key": signing_pem.decode("utf-8"),
        "fingerprint": ":".join(
            fingerprint[i:i + 2]
            for i in range(0, len(fingerprint), 2)
        )
    }


def create_identity(master_password, directory="data/identity"):
    """
    Generate and securely save a user's ECDH and Ed25519 keys.

    Existing identities are never silently overwritten.
    """

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    private_path = directory / PRIVATE_FILE
    public_path = directory / PUBLIC_FILE

    if private_path.exists() or public_path.exists():
        raise FileExistsError(
            "An identity already exists. Load it instead."
        )

    # Generate independent key pairs.
    ecdh_private = ec.generate_private_key(ec.SECP256R1())
    signing_private = ed25519.Ed25519PrivateKey.generate()

    # Serialize both private keys.
    private_data = {
        "ecdh_private_key": _private_key_to_pem(
            ecdh_private
        ).decode("utf-8"),

        "signing_private_key": _private_key_to_pem(
            signing_private
        ).decode("utf-8")
    }

    plaintext = json.dumps(private_data).encode("utf-8")

    # Encrypt the private key bundle.
    salt = os.urandom(SALT_LENGTH)
    nonce = os.urandom(NONCE_LENGTH)

    storage_key = _derive_storage_key(master_password, salt)

    ciphertext = AESGCM(storage_key).encrypt(
        nonce,
        plaintext,
        AAD
    )

    encrypted_data = {
        "version": 1,
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii")
    }

    public_identity = _build_public_identity(
        ecdh_private,
        signing_private
    )

    # Save encrypted private keys and public identity.
    private_path.write_text(
        json.dumps(encrypted_data, indent=4),
        encoding="utf-8"
    )

    public_path.write_text(
        json.dumps(public_identity, indent=4),
        encoding="utf-8"
    )

    return {
        "ecdh_private_key": ecdh_private,
        "signing_private_key": signing_private,
        "ecdh_public_key": ecdh_private.public_key(),
        "signing_public_key": signing_private.public_key()
    }


def load_identity(master_password, directory="data/identity"):
    """
    Load and decrypt a previously created identity.
    A wrong master password or modified file raises ValueError.
    """

    directory = Path(directory)
    private_path = directory / PRIVATE_FILE

    if not private_path.exists():
        raise FileNotFoundError("Private identity file not found.")

    try:
        encrypted_data = json.loads(
            private_path.read_text(encoding="utf-8")
        )

        if encrypted_data.get("version") != 1:
            raise ValueError("Unsupported identity file version.")

        salt = base64.b64decode(encrypted_data["salt"])
        nonce = base64.b64decode(encrypted_data["nonce"])
        ciphertext = base64.b64decode(encrypted_data["ciphertext"])

        if len(salt) != SALT_LENGTH or len(nonce) != NONCE_LENGTH:
            raise ValueError("Invalid identity file parameters.")

        storage_key = _derive_storage_key(master_password, salt)

        plaintext = AESGCM(storage_key).decrypt(
            nonce,
            ciphertext,
            AAD
        )

        private_data = json.loads(plaintext.decode("utf-8"))

        ecdh_private = serialization.load_pem_private_key(
            private_data["ecdh_private_key"].encode("utf-8"),
            password=None
        )

        signing_private = serialization.load_pem_private_key(
            private_data["signing_private_key"].encode("utf-8"),
            password=None
        )

        if not isinstance(ecdh_private, ec.EllipticCurvePrivateKey):
            raise ValueError("Invalid ECDH private key.")

        if not isinstance(ecdh_private.curve, ec.SECP256R1):
            raise ValueError("Unsupported ECDH curve.")

        if not isinstance(signing_private, ed25519.Ed25519PrivateKey):
            raise ValueError("Invalid Ed25519 private key.")

        return {
            "ecdh_private_key": ecdh_private,
            "signing_private_key": signing_private,
            "ecdh_public_key": ecdh_private.public_key(),
            "signing_public_key": signing_private.public_key()
        }

    except (InvalidTag, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "Unable to unlock identity. Check the master password "
            "or identity file."
        ) from exc


def export_public_identity(identity, output_path):
    """Export only public keys. Never export private keys."""

    public_identity = _build_public_identity(
        identity["ecdh_private_key"],
        identity["signing_private_key"]
    )

    Path(output_path).write_text(
        json.dumps(public_identity, indent=4),
        encoding="utf-8"
    )

    return public_identity


def load_public_identity(input_path):
    """Load public keys and verify their SHA-256 fingerprint."""

    data = json.loads(
        Path(input_path).read_text(encoding="utf-8")
    )

    if data.get("version") != 1:
        raise ValueError("Unsupported public identity version.")

    ecdh_public = serialization.load_pem_public_key(
        data["ecdh_public_key"].encode("utf-8")
    )

    signing_public = serialization.load_pem_public_key(
        data["signing_public_key"].encode("utf-8")
    )

    if not isinstance(ecdh_public, ec.EllipticCurvePublicKey):
        raise ValueError("Invalid ECDH public key.")

    if not isinstance(ecdh_public.curve, ec.SECP256R1):
        raise ValueError("Unsupported ECDH curve.")

    if not isinstance(signing_public, ed25519.Ed25519PublicKey):
        raise ValueError("Invalid Ed25519 public key.")

    # Recalculate fingerprint from the actual public keys.
    fingerprint_data = (
        ecdh_public.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        +
        signing_public.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )

    digest = hashlib.sha256(fingerprint_data).hexdigest()

    expected_fingerprint = ":".join(
        digest[i:i + 2]
        for i in range(0, len(digest), 2)
    )

    if not hmac.compare_digest(
        expected_fingerprint,
        data.get("fingerprint", "")
    ):
        raise ValueError("Public identity fingerprint is invalid.")

    return {
        "ecdh_public_key": ecdh_public,
        "signing_public_key": signing_public,
        "fingerprint": expected_fingerprint
    }


def sign_message(identity, message: bytes) -> bytes:
    if not isinstance(message, bytes):
        raise TypeError("Message must be bytes.")
    return identity["signing_private_key"].sign(message)


def verify_signature(public_key, message: bytes, signature: bytes) -> bool:
    try:
        public_key.verify(signature, message)
        return True
    except InvalidSignature:
        return False
