
from key_exchange import (
    generate_key_pair,
    export_public_key,
    import_public_key,
    generate_exchange_salt,
    derive_shared_key,
    get_public_key_fingerprint
)


def test_key_generation():
    private_key, public_key = generate_key_pair()

    assert private_key is not None
    assert public_key is not None


def test_public_key_export_import():
    _, public_key = generate_key_pair()

    exported = export_public_key(public_key)
    imported = import_public_key(exported)

    assert imported.curve.name == "secp256r1"


def test_ecdh_shared_key_agreement():
    # User A generates keys.
    private_a, public_a = generate_key_pair()

    # User B generates keys.
    private_b, public_b = generate_key_pair()

    # Both exchange public keys.
    salt = generate_exchange_salt()

    # Both derive the encryption key independently.
    key_a = derive_shared_key(private_a, public_b, salt)
    key_b = derive_shared_key(private_b, public_a, salt)

    assert key_a == key_b
    assert len(key_a) == 32


def test_different_salts_produce_different_keys():
    private_a, public_a = generate_key_pair()
    private_b, public_b = generate_key_pair()

    salt_a = generate_exchange_salt()
    salt_b = generate_exchange_salt()

    key_a = derive_shared_key(private_a, public_b, salt_a)
    key_b = derive_shared_key(private_b, public_a, salt_b)

    assert key_a != key_b


def test_public_key_fingerprint():
    _, public_key = generate_key_pair()

    fingerprint = get_public_key_fingerprint(public_key)

    assert len(fingerprint) == 95
    assert isinstance(fingerprint, str)
