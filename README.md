# 🔐 KeyShield — Secure Password Manager

A robust, cryptographically authenticated desktop password manager engineered in Python using SQLite, CustomTkinter, and Fernet encryption. Designed for zero-cloud, fully offline, and mathematically verifiable credential management.

Developed by **[Prakhar Shrestha](https://github.com/prakharshrestha)**.

---

## 🛡️ Key Features

- **Master Password Authentication** — Hardened key derivation using PBKDF2-HMAC-SHA256 combined with salted SHA-256 verification.
- **Authenticated Symmetric Encryption** — Every stored password is encrypted using Fernet (AES-128-CBC + HMAC-SHA256 signature verification).
- **Zero Plaintext Persistence** — No user passwords or keys are ever stored unencrypted on disk.
- **Air-Gapped Local Operation** — 100% offline; zero network calls, zero tracking, and no external third-party dependencies.
- **CSPRNG Password Generator** — Cryptographically safe random password generator powered by Python's OS-backed `secrets` module.
- **Live Password Strength Meter** — Real-time entropy evaluation (Weak, Medium, Strong) with visual feedback.
- **SQL Injection Prevention** — Strictly parameterized SQL queries prevent database injection risks.
- **Secure Memory Lifecycle** — Session keys reside purely in volatile memory and are purged on logout or application termination.
- **Modern UI** — Sleek dark-themed interface built using CustomTkinter.

---

## 📂 Project Structure

```
KeyShield/
├── main.py              # Application entry point
├── gui.py               # CustomTkinter interface & screen workflows
├── auth.py              # Master password setup & hash verification
├── encryption.py        # PBKDF2 key derivation & Fernet encrypt/decrypt
├── db_manager.py        # Parameterized SQLite CRUD operations
├── password_gen.py      # CSPRNG password generator & entropy scoring
├── requirements.txt     # Python dependencies
├── README.md            # Project documentation
├── data/                # Local runtime data (auto-created)
│   ├── vault.db         # Encrypted SQLite credential database
│   ├── salt.bin         # 16-byte cryptographic salt
│   └── master.hash      # Salted SHA-256 digest of master password
└── tests/
    ├── __init__.py
    └── test_all.py      # Automated test suite (49 passing tests)
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.11 or higher
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/prakharshrestha/KeyShield.git
cd KeyShield
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

Launch KeyShield:
```bash
python main.py
```

### First-Time Use
1. On first launch, the **Setup Screen** prompts you to establish a Master Password (minimum 6 characters).
2. The system generates a cryptographic 16-byte salt and stores the salted SHA-256 hash in `data/master.hash`.
3. Log in with your master password to access your encrypted vault.

---

## 🧪 Automated Testing

KeyShield includes an exhaustive automated test suite covering encryption primitives, database integrity, authentication flows, and password generation:

```bash
python -m pytest tests/test_all.py -v
```

All **49 tests** run within isolated temporary directories to protect real vault data.

---

## 🔒 Security Architecture

| Security Layer | Cryptographic Standard / Primitive |
| :--- | :--- |
| **Master Authentication** | SHA-256 with 16-byte random salt (`os.urandom`) |
| **Key Derivation (KDF)** | PBKDF2-HMAC-SHA256 (200,000 iterations & 32-byte key) |
| **Vault Encryption** | Fernet envelope (AES-128-CBC + HMAC-SHA256) |
| **Initialization Vector** | 128-bit random IV uniquely generated per encryption |
| **Random Number Source** | OS kernel entropy via Python `secrets` module (CSPRNG) |
| **Database Transactions** | Parameterized queries (`?`) in SQLite with WAL mode |
