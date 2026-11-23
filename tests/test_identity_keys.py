
import pytest

from identity_keys import (
    create_identity,
    load_identity,
    export_public_identity,
    load_public_identity,
    sign_message,
    verify_signature
)


def test_identity_generation(tmp_path):
    identity = create_identity(
        "SecureVault@123",
        tmp_path
    )

    assert identity["ecdh_private_key"] is not None
    assert identity["signing_private_key"] is not None


def test_private_keys_are_encrypted(tmp_path):
    create_identity("SecureVault@123", tmp_path)

    private_file = tmp_path / "identity_private.enc"

    content = private_file.read_text(encoding="utf-8")

    assert "BEGIN PRIVATE KEY" not in content
    assert "ecdh_private_key" not in content


def test_identity_load_with_correct_password(tmp_path):
    original = create_identity(
        "SecureVault@123",
        tmp_path
    )

    loaded = load_identity(
        "SecureVault@123",
        tmp_path
    )

    assert (
        original["ecdh_public_key"].public_numbers()
        ==
        loaded["ecdh_public_key"].public_numbers()
    )


def test_identity_rejects_wrong_password(tmp_path):
    create_identity("SecureVault@123", tmp_path)

    with pytest.raises(ValueError):
        load_identity("WrongPassword", tmp_path)


def test_existing_identity_is_not_overwritten(tmp_path):
    create_identity("SecureVault@123", tmp_path)

    with pytest.raises(FileExistsError):
        create_identity("AnotherPassword", tmp_path)


def test_public_identity_export_import(tmp_path):
    identity = create_identity(
        "SecureVault@123",
        tmp_path / "user_a"
    )

    public_file = tmp_path / "user_a_public.json"

    export_public_identity(identity, public_file)

    imported = load_public_identity(public_file)

    assert imported["ecdh_public_key"] is not None
    assert imported["signing_public_key"] is not None
    assert imported["fingerprint"]


def test_digital_signature_verification(tmp_path):
    identity = create_identity(
        "SecureVault@123",
        tmp_path
    )

    message = b"SecureVault credential sharing test"

    signature = sign_message(identity, message)

    assert verify_signature(
        identity["signing_public_key"],
        message,
        signature
    )


def test_tampered_message_is_rejected(tmp_path):
    identity = create_identity(
        "SecureVault@123",
        tmp_path
    )

    message = b"Original credential"
    signature = sign_message(identity, message)

    tampered_message = b"Modified credential"

    assert not verify_signature(
        identity["signing_public_key"],
        tampered_message,
        signature
    )


def test_different_signing_key_rejects_signature(tmp_path):
    user_a = create_identity(
        "SecureVault@123",
        tmp_path / "user_a"
    )

    user_b = create_identity(
        "SecureVault@456",
        tmp_path / "user_b"
    )

    message = b"Test message"
    signature = sign_message(user_a, message)

    assert not verify_signature(
        user_b["signing_public_key"],
        message,
        signature
    )
