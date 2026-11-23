"""Authenticated, recipient-bound file sharing for SecureVault.

The package is a binary container with a JSON header followed by independently
authenticated AES-GCM chunks.  A detached Ed25519 signature covers the header
and ciphertext digest.  Files are streamed in chunks rather than loaded into
one large plaintext buffer.
"""

import base64
import hashlib
import json
import os
import struct
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from key_exchange import derive_shared_key, export_public_key, generate_exchange_salt, generate_key_pair, import_public_key


MAGIC = b"SECUREVAULT-FILE-1\n"
VERSION = 1
CHUNK_SIZE = 1024 * 1024
NONCE_LENGTH = 12
TAG_LENGTH = 16


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value, validate=True)


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(identity: dict) -> str:
    ecdh = identity["ecdh_public_key"].public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    signing = identity["signing_public_key"].public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    digest = hashlib.sha256(ecdh + signing).hexdigest()
    return ":".join(digest[index:index + 2] for index in range(0, len(digest), 2))


def _nonce(base_nonce: bytes, index: int) -> bytes:
    if len(base_nonce) != 8 or index >= 2**32:
        raise ValueError("Invalid file package nonce parameters.")
    return base_nonce + struct.pack(">I", index)


def _aad(header: dict, index: int) -> bytes:
    stable_header = {
        key: value for key, value in header.items()
        if key != "ciphertext_sha256"
    }
    return _canonical(stable_header) + b"|chunk|" + str(index).encode("ascii")


def _read_header(stream) -> tuple[dict, bytes, bytes]:
    if stream.read(len(MAGIC)) != MAGIC:
        raise ValueError("Unsupported encrypted file format.")
    raw_length = stream.read(8)
    if len(raw_length) != 8:
        raise ValueError("Encrypted file header is truncated.")
    header_length = struct.unpack(">Q", raw_length)[0]
    if header_length <= 0 or header_length > 64 * 1024:
        raise ValueError("Encrypted file header is invalid.")
    raw_header = stream.read(header_length)
    if len(raw_header) != header_length:
        raise ValueError("Encrypted file header is truncated.")
    try:
        header = json.loads(raw_header.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Encrypted file header is not valid JSON.") from exc
    signature_length_raw = stream.read(2)
    if len(signature_length_raw) != 2:
        raise ValueError("Encrypted file signature is missing.")
    signature_length = struct.unpack(">H", signature_length_raw)[0]
    signature = stream.read(signature_length)
    if len(signature) != signature_length:
        raise ValueError("Encrypted file signature is truncated.")
    return header, raw_header, signature


def get_package_metadata(package_path) -> dict:
    with Path(package_path).open("rb") as package:
        header, _, _ = _read_header(package)
    if header.get("version") != VERSION or not isinstance(header.get("filename"), str):
        raise ValueError("Invalid encrypted file package.")
    return header


def create_file_package(input_path, output_path, sender_identity, recipient_identity) -> dict:
    source = Path(input_path)
    destination = Path(output_path)
    if not source.is_file():
        raise ValueError("The selected source file does not exist.")
    if source.resolve() == destination.resolve():
        raise ValueError("The encrypted output must differ from the source file.")

    recipient_ecdh = recipient_identity.get("ecdh_public_key")
    if not isinstance(recipient_ecdh, ec.EllipticCurvePublicKey):
        raise ValueError("Recipient identity has no valid ECDH public key.")
    if not isinstance(recipient_ecdh.curve, ec.SECP256R1):
        raise ValueError("Recipient identity uses an unsupported curve.")

    ephemeral_private, ephemeral_public = generate_key_pair()
    salt = generate_exchange_salt()
    key = derive_shared_key(ephemeral_private, recipient_ecdh, salt)
    base_nonce = os.urandom(8)

    header = {
        "version": VERSION,
        "algorithm": "ECDH-SECP256R1+HKDF-SHA256+AES-256-GCM-CHUNKED",
        "signature_algorithm": "Ed25519",
        "sender_fingerprint": _fingerprint(sender_identity),
        "recipient_fingerprint": _fingerprint(recipient_identity),
        "filename": source.name,
        "size": source.stat().st_size,
        "chunk_size": CHUNK_SIZE,
        "chunks": (source.stat().st_size + CHUNK_SIZE - 1) // CHUNK_SIZE,
        "ephemeral_public_key": export_public_key(ephemeral_public).decode("utf-8"),
        "salt": _b64(salt),
        "base_nonce": _b64(base_nonce),
        "ciphertext_sha256": "",
    }

    digest = hashlib.sha256()
    chunk_count = 0
    with tempfile.NamedTemporaryFile(prefix="securevault-", suffix=".chunks", delete=False) as temp:
        temp_path = Path(temp.name)
        try:
            with source.open("rb") as source_stream:
                while True:
                    plaintext = source_stream.read(CHUNK_SIZE)
                    if not plaintext:
                        break
                    ciphertext = AESGCM(key).encrypt(
                        _nonce(base_nonce, chunk_count),
                        plaintext,
                        _aad(header, chunk_count),
                    )
                    temp.write(struct.pack(">I", len(ciphertext)))
                    temp.write(ciphertext)
                    digest.update(struct.pack(">I", len(ciphertext)))
                    digest.update(ciphertext)
                    chunk_count += 1
            if chunk_count != header["chunks"]:
                raise ValueError("Source file changed during encryption.")
            header["ciphertext_sha256"] = digest.hexdigest()
            raw_header = _canonical(header)
            signature = sender_identity["signing_private_key"].sign(
                raw_header + bytes.fromhex(header["ciphertext_sha256"])
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            temp.flush()
            temp.close()
            with destination.open("wb") as package:
                package.write(MAGIC)
                package.write(struct.pack(">Q", len(raw_header)))
                package.write(raw_header)
                package.write(struct.pack(">H", len(signature)))
                package.write(signature)
                with temp_path.open("rb") as chunks:
                    while True:
                        block = chunks.read(1024 * 1024)
                        if not block:
                            break
                        package.write(block)
        finally:
            temp_path.unlink(missing_ok=True)
    return header


def open_file_package(package_path, output_path, receiver_identity, trusted_sender_identity) -> dict:
    destination = Path(output_path)
    with Path(package_path).open("rb") as package:
        header, raw_header, signature = _read_header(package)
        required = {
            "version", "algorithm", "signature_algorithm",
            "sender_fingerprint", "recipient_fingerprint", "filename",
            "size", "chunk_size", "chunks", "ephemeral_public_key",
            "salt", "base_nonce", "ciphertext_sha256",
        }
        if set(header) != required:
            raise ValueError("Encrypted file package fields are invalid.")
        if header["version"] != VERSION or header["algorithm"] != (
            "ECDH-SECP256R1+HKDF-SHA256+AES-256-GCM-CHUNKED"
        ) or header["signature_algorithm"] != "Ed25519":
            raise ValueError("Unsupported encrypted file algorithms.")
        sender_fingerprint = _fingerprint(trusted_sender_identity)
        receiver_fingerprint = _fingerprint(receiver_identity)
        if header["sender_fingerprint"] != sender_fingerprint:
            raise ValueError("Sender identity fingerprint mismatch.")
        if header["recipient_fingerprint"] != receiver_fingerprint:
            raise ValueError("This file is not intended for this administrator.")
        try:
            trusted_sender_identity["signing_public_key"].verify(
                signature,
                raw_header + bytes.fromhex(header["ciphertext_sha256"]),
            )
        except (InvalidSignature, ValueError) as exc:
            raise ValueError("Encrypted file integrity metadata is invalid.") from exc

        ephemeral = import_public_key(header["ephemeral_public_key"].encode("utf-8"))
        salt = _unb64(header["salt"])
        base_nonce = _unb64(header["base_nonce"])
        if len(salt) != 16 or len(base_nonce) != 8:
            raise ValueError("Encrypted file key parameters are invalid.")
        key = derive_shared_key(receiver_identity["ecdh_private_key"], ephemeral, salt)
        digest = hashlib.sha256()
        written = 0
        chunks = 0
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="securevault-", suffix=".plain", delete=False) as temp:
            temp_path = Path(temp.name)
            try:
                while chunks < header["chunks"]:
                    raw_length = package.read(4)
                    if len(raw_length) != 4:
                        raise ValueError("Encrypted file is truncated.")
                    length = struct.unpack(">I", raw_length)[0]
                    if length < TAG_LENGTH or length > header["chunk_size"] + TAG_LENGTH:
                        raise ValueError("Encrypted file chunk length is invalid.")
                    ciphertext = package.read(length)
                    if len(ciphertext) != length:
                        raise ValueError("Encrypted file is truncated.")
                    digest.update(raw_length)
                    digest.update(ciphertext)
                    plaintext = AESGCM(key).decrypt(
                        _nonce(base_nonce, chunks),
                        ciphertext,
                        _aad(header, chunks),
                    )
                    temp.write(plaintext)
                    written += len(plaintext)
                    chunks += 1
                if package.read(1):
                    raise ValueError("Encrypted file contains trailing data.")
                if written != header["size"] or digest.hexdigest() != header["ciphertext_sha256"]:
                    raise ValueError("Encrypted file integrity verification failed.")
                destination_tmp = destination.with_name(destination.name + ".tmp")
                temp.flush()
                temp.close()
                with destination_tmp.open("wb") as restored, temp_path.open("rb") as plaintext:
                    while True:
                        block = plaintext.read(1024 * 1024)
                        if not block:
                            break
                        restored.write(block)
                os.replace(destination_tmp, destination)
            finally:
                temp_path.unlink(missing_ok=True)
    return {"filename": header["filename"], "size": header["size"]}
