
import copy
import pytest

from cryptography.exceptions import InvalidSignature

from identity_keys import (
    create_identity,
    export_public_identity,
    load_public_identity
)

from sharing import (
    create_share_package,
    open_share_package
)


@pytest.fixture
def two_users(tmp_path):
    """Create two independent SecureVault users."""

    user_a = create_identity(
        "UserA@123",
        tmp_path / "user_a"
    )

    user_b = create_identity(
        "UserB@123",
        tmp_path / "user_b"
    )

    # Export public identities.
    public_a_file = tmp_path / "user_a_public.json"
    public_b_file = tmp_path / "user_b_public.json"

    export_public_identity(user_a, public_a_file)
    export_public_identity(user_b, public_b_file)

    public_a = load_public_identity(public_a_file)
    public_b = load_public_identity(public_b_file)

    return user_a, user_b, public_a, public_b


def test_secure_credential_sharing(two_users):
    user_a, user_b, public_a, public_b = two_users

    credential = {
        "website": "github.com",
        "username": "demo_user",
        "password": "DummyPassword@123"
    }

    package = create_share_package(
        user_a,
        public_b,
        credential
    )

    received = open_share_package(
        user_b,
        package,
        public_a
    )

    assert received == credential


def test_package_does_not_expose_plaintext(two_users):
    user_a, user_b, public_a, public_b = two_users

    credential = {
        "website": "example.com",
        "username": "demo",
        "password": "SecretDummy123"
    }

    package = create_share_package(
        user_a,
        public_b,
        credential
    )

    package_text = str(package)

    assert "SecretDummy123" not in package_text
    assert "demo" not in package_text


def test_wrong_recipient_cannot_decrypt(two_users, tmp_path):
    user_a, user_b, public_a, public_b = two_users

    user_c = create_identity(
        "UserC@123",
        tmp_path / "user_c"
    )

    credential = {
        "website": "example.com",
        "username": "demo",
        "password": "Dummy123"
    }

    package = create_share_package(
        user_a,
        public_b,
        credential
    )

    with pytest.raises(ValueError):
        open_share_package(
            user_c,
            package,
            public_a
        )


def test_tampered_package_signature_rejected(two_users):
    user_a, user_b, public_a, public_b = two_users

    credential = {
        "website": "example.com",
        "username": "demo",
        "password": "Dummy123"
    }

    package = create_share_package(
        user_a,
        public_b,
        credential
    )

    modified_package = copy.deepcopy(package)
    modified_package["ciphertext"] = "AAAA"

    with pytest.raises(InvalidSignature):
        open_share_package(
            user_b,
            modified_package,
            public_a
        )


def test_wrong_sender_identity_rejected(two_users, tmp_path):
    user_a, user_b, public_a, public_b = two_users

    user_c = create_identity(
        "UserC@123",
        tmp_path / "user_c"
    )

    public_c_file = tmp_path / "user_c_public.json"
    export_public_identity(user_c, public_c_file)
    public_c = load_public_identity(public_c_file)

    package = create_share_package(
        user_a,
        public_b,
        {
            "website": "example.com",
            "username": "demo",
            "password": "Dummy123"
        }
    )

    with pytest.raises(ValueError):
        open_share_package(
            user_b,
            package,
            public_c
        )


def test_empty_credential_rejected(two_users):
    user_a, user_b, public_a, public_b = two_users

    with pytest.raises(ValueError):
        create_share_package(
            user_a,
            public_b,
            {}
        )


def test_modified_package_fields_rejected(two_users):
    user_a, user_b, public_a, public_b = two_users

    package = create_share_package(
        user_a,
        public_b,
        {
            "website": "example.com",
            "username": "demo",
            "password": "Dummy123"
        }
    )

    package["unexpected_field"] = "modified"

    with pytest.raises(ValueError):
        open_share_package(
            user_b,
            package,
            public_a
        )
