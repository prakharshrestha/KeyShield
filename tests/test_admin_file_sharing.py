import hashlib

import pytest

import admin_auth
import db_manager
import file_sharing
import identity_keys


def test_admin_accounts_are_independent(tmp_path, monkeypatch):
    monkeypatch.setattr(db_manager, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(db_manager, "DB_PATH", str(tmp_path / "vault.db"))
    db_manager.init_db()
    admin_auth.setup_accounts("Admin One", "AdminOne!123", "Admin Two", "AdminTwo!123")

    assert admin_auth.authenticate(1, "AdminOne!123")["name"] == "Admin One"
    assert admin_auth.authenticate(2, "AdminTwo!123")["name"] == "Admin Two"
    assert admin_auth.authenticate(1, "AdminTwo!123") is None
    with pytest.raises(ValueError):
        admin_auth.setup_accounts("Other One", "OtherOne!123", "Other Two", "OtherTwo!123")


def test_admin_file_round_trip_and_tamper_detection(tmp_path):
    sender = identity_keys.create_identity("SenderPassword!123", tmp_path / "sender")
    receiver = identity_keys.create_identity("ReceiverPassword!123", tmp_path / "receiver")
    public_sender_path = tmp_path / "sender-public.json"
    public_receiver_path = tmp_path / "receiver-public.json"
    identity_keys.export_public_identity(sender, public_sender_path)
    identity_keys.export_public_identity(receiver, public_receiver_path)
    public_sender = identity_keys.load_public_identity(public_sender_path)
    public_receiver = identity_keys.load_public_identity(public_receiver_path)

    original = tmp_path / "sample.bin"
    original.write_bytes(bytes(range(256)) * 9000)
    package = tmp_path / "sample.svf"
    restored = tmp_path / "restored.bin"
    file_sharing.create_file_package(original, package, sender, public_receiver)
    file_sharing.open_file_package(package, restored, receiver, public_sender)
    assert hashlib.sha256(original.read_bytes()).digest() == hashlib.sha256(restored.read_bytes()).digest()

    tampered = bytearray(package.read_bytes())
    tampered[-1] ^= 1
    package.write_bytes(tampered)
    with pytest.raises(Exception):
        file_sharing.open_file_package(package, tmp_path / "bad.bin", receiver, public_sender)
