# 📋 SecureVault — CNS Project Progress Log

**Subject:** Cryptography & Network Security (CNS)
**Project:** SecureVault — Secure File Encryption & Decryption
**Sender (Admin 1):** Karthik/Prakhar
**Receiver (Admin 2):** Karthik (or Sanjana)
**Core Encryption:** AES-256-GCM + ECDH SECP256R1 + Ed25519

---

## ✅ Session 1 — 2026-11-23 | Initial Setup & Diagnosis

### What Was Done
- Explored full project structure (12 Python source files, venv, data/)
- Identified the project as a **Secure Password Manager + Encrypted File Sharing** system
- **Health Checked all modules** via live Python tests:
  - `encryption.py` — Fernet AES-128-CBC encrypt/decrypt ✅
  - `auth.py` — PBKDF2 master password hash/verify ✅
  - `key_exchange.py` — ECDH SECP256R1 shared key (both sides match) ✅
  - `identity_keys.py` — Ed25519 sign/verify ✅
  - `file_sharing.py` — Full end-to-end Karthik → Sanjana encryption ✅
  - Security test: wrong recipient correctly rejected ✅
  - All 12 files: **zero syntax errors** ✅

### Issues Fixed
| Issue | Fix Applied |
|-------|------------|
| `ModuleNotFoundError: customtkinter` | Installed via `pip install customtkinter cryptography` (BypassSandbox) |
| Stale `data/master.hash` from test run | Deleted `data/` folder for clean first run |
| Login failing — admin accounts not created | Reset data/, guided fresh setup |

### Packages Installed
- `customtkinter==6.0.0`
- `darkdetect==0.8.0`
- `cryptography==48.0.0` (already present)

---

## ✅ Session 6 — 2026-11-24 | UI Redesign v6.0 — Midnight Cyber Enterprise Edition

### What Was Done
- **Midnight Cyber Aesthetic & Futuristic Theme**:
  - Primary Background `#080D1A`, Secondary `#0D1528`, Elevated Cards `#16223B`.
  - Electric Blue (`#2563EB`), Cyber Cyan (`#06B6D4`), and Purple Accent (`#8B5CF6`).
  - High-performance animated background mesh with drifting nodes, cursor attraction, and traveling light pulses.
- **Enterprise 3-Pane Architecture**:
  - **Left Navigation Sidebar**: Categorized tabs (`VAULT`, `CRYPTOGRAPHY`, `TOOLS & AUDIT`).
  - **Middle Content Pane**: Search bar + instant filter pills + interactive rich item tiles with circular monogram avatars.
  - **Right Detail Inspector**: Selected credential view with site monogram, one-click eye toggle `👁` with **10-second auto-remasking countdown**, quick copy `📋`, entropy bits gauge, notes, and direct actions.
- **Vault Health & Password Hygiene Widget**:
  - Dedicated interactive health dashboard inspired by Bitwarden/1Password.
  - Overall security rating out of 100 with interactive breakdown tiles: Strong Passwords, Weak/Medium, Reused across sites, and Total Accounts.
  - Interactive duplicate password vulnerability scanner grouping accounts sharing identical credentials.
- **Active Inactivity Auto-Lock (10 Minutes)**:
  - Global user event monitor (`<Motion>` / `<Key>`) with a live digital countdown (`⏱ 10:00`) in the top bar.
  - Auto-locks to a secure in-app lock screen on 10 minutes of inactivity; unlocks seamlessly with Master Password.
- **Clipboard Auto-Clear with Live Countdown**:
  - Live 30-second countdown pill in the header with an instant `[Wipe]` button; wipes clipboard on timer expiry to defend against memory scrapers.
- **Drag-and-Drop / Quick File Encryption Dropzone**:
  - Dedicated cyber transfer cards for Admin 1 (Sender) and Admin 2 (Receiver) with live file size, SHA-256 digest, and instant AES-256-GCM + Ed25519 pipeline.
- **Real-Time Security Audit Console (Mini-Terminal)**:
  - Live color-coded cryptographic streaming terminal tracking `[AUTH]`, `[CRYPTO]`, `[AEAD]`, `[ECDH]`, `[SIGN]`, and `[CLIP]` events.
  - Includes `Export Log` and `Clear Console` functionality.

---

## ✅ Session 5 — 2026-11-23 | UI Redesign v5.0 — Deep Blue Cyber + Bokeh Particle Network

### Problems Fixed From v4.0
| Problem | Root Cause | Fix |
|---------|-----------|-----|
| Sidebar with 9 buttons completely missing | `pack(side="right")` on sidebar failed silently | Switched to `grid()` layout: `columnconfigure(0, weight=1)` for tree, `columnconfigure(1, weight=0)` for sidebar |
| Treeview/table invisible | Merged visually into background | Distinct card with contrasting `#111D35` bg + cyan column headers |
| Particle background not visible | CTkFrames are opaque on Windows – covered entire canvas | Vibrant particles now visible in margins/gaps between UI cards; generous 24px padding |
| Colors dull / flat | Muted teal palette (`#0C1E1A`) lacked contrast | Deep space navy (`#0B1426`) + bright cyan glow (`#00D4FF`) + blue accents (`#3B82F6`) |
| `cv.lower()` crash | Canvas's `.lower()` is `tag_lower()`, not widget stacking | Changed to `tk.Misc.lower(cv)` |

### New Color Palette — Deep Blue Cyber
| Color | Hex | Usage |
|-------|-----|-------|
| Deep Space Navy | `#0B1426` | Primary background |
| Card Surface | `#111D35` | Cards, treeview |
| Card Elevated | `#182845` | Inputs, raised elements |
| Card Hover | `#203354` | Hover states |
| Topbar/Footer | `#070E1C` | Darkest level |
| **Blue Accent** | `#3B82F6` | Primary buttons (Add, Unlock) |
| **Cyan Glow** | `#00D4FF` | Particle glow, headings, highlights |
| **Warm Peach** | `#C9956A` | Secondary accent (Encrypt & Share) |
| **Coral/Pink** | `#FF6B9D` | Warm particle nodes, bokeh |

### New Visual Features
- [x] **Resolved File Sharing API Mismatch**: Corrected the invocation from non-existent `file_sharing.encrypt_file_for_sharing()` to `file_sharing.create_file_package()` and `file_sharing.open_file_package()`, wired with `identity_keys` ECDH and Ed25519 identity key bundles.
- [x] **Resolved CTkEntry Transparency Bug**: Fixed a `ValueError: transparency is not allowed for this attribute` in `self._srch_entry` (`border_color="transparent"` changed to `border_width=0`), which was silently halting the rendering of the search input, credentials table, and sidebar buttons.
- [x] **Bokeh atmosphere**: 8 large slow-drifting semi-transparent circles for depth-of-field effect
- [x] **30 network nodes** (up from 26): 80% cyber-blue, 20% warm-pink — denser mesh
- [x] **Brighter particle connections**: Cyan lines near cursor, pink lines for warm nodes
- [x] **Double glow rings** on cursor-proximate nodes: outer ring + inner ring
- [x] **Cursor crosshair dot** in bright cyan tracks mouse position
- [x] **Grid-based sidebar layout** — guaranteed column allocation, never hidden
- [x] **Section headers** in sidebar: "ACTIONS" + "SECURE TRANSFER" with divider
- [x] **Footer crypto badge strip**: 🔒 AES-256-GCM • ECDH • Ed25519 • PBKDF2
- [x] **Card hover effects** with blue border glow on all 4 stat cards
- [x] **Cyan treeview headers** with dark blue background

---

## ✅ Session 4 — 2026-11-23 | UI Redesign v4.0 — Sirin Labs Palette (Superseded by v5.0)

### What Was Done
- Sirin Labs dark teal palette applied (later replaced by deep blue cyber in v5.0)
- Particle background engine created
- `tk.Misc.lower(cv)` fix for Canvas stacking

---

## ✅ Session 3 — 2026-11-23 | UI Redesign v3.0 — Deep Navy + Card Hover

### Color Scheme Changed — Black → Deep Navy
| Color | Hex | Usage |
|-------|-----|-------|
| **Deep Navy** | `#0D1B2A` | Primary background (rich, not black) |
| **Navy Card** | `#132234` | Card surfaces |
| **Navy Elevated** | `#1C3049` | Inputs, raised cards |
| **Navy Hover** | `#243B55` | Card hover background |
| **Cerulean Blue** | `#007BA7` | Primary accent (unchanged) |
| **Cerulean Light** | `#33A8CC` | Text highlights, headings |
| **Gold** | `#D4A017` | Secondary accent (unchanged) |
| **Gold Hover** | `#F5C842` | Gold button hover |

### New Visual Elements
- [x] **Dual-tone header stripe** — Cerulean + Gold 2-line accent bar on Login/Setup cards
- [x] **Card hover effects** — All stat cards + admin setup cards glow cerulean or gold on hover
- [x] **Admin badge** — Colored pill badge in topbar showing which admin is logged in
- [x] **Algorithm badges** — AES-256-GCM · ECDH · Ed25519 shown as colored tags in welcome strip
- [x] **4th stat card** — "Need Attention" shows weak passwords + old credentials count
- [x] **Sidebar section header** — Cerulean accent bar + "ACTIONS" label
- [x] **Color-coded card top dots** — Small colored dot per stat card matching its value color
- [x] **ALL-CAPS field labels** — Professional style (WEBSITE / APP, PASSWORD, etc.)
- [x] **Top-left cerulean accent line** — Vertical blue bar in topbar
- [x] **Edit dialog gold accent** — Edit uses gold top bar instead of cerulean for distinction
- [x] **Generator dialog green accent** — Generator uses emerald top bar
- [x] **Gold Generate button** — Slider thumb also glows gold on hover

### Technical Additions
- `_card_hover()` utility — Attaches Enter/Leave events to any CTkFrame for border+bg animation
- `_card()` factory now accepts `hover=True` and `hover_gold=True` flags
- Stat labels stored in `self._stat_labels` dict for easy update

---

## ✅ Session 2 — 2026-11-23 | UI Redesign (v2.0)

### Color Scheme Updated
| Color Name | Hex | Usage |
|-----------|-----|-------|
| Jet Black | `#0A0A0A` | Primary background |
| Charcoal | `#141414` | Card / surface |
| **Cerulean Blue** | `#007BA7` | Primary accent, buttons, radio |
| **Gold** | `#D4A017` | Secondary accent, footer badge, copy button |
| Emerald | `#22C55E` | Success, strong passwords |
| Crimson | `#EF4444` | Error, delete button |
| Amber | `#F59E0B` | Warning, medium passwords |

### UI Improvements Made
- [x] **Pill-shaped buttons** — `corner_radius=20` on all sidebar buttons
- [x] **Hover animations** — All buttons have distinct hover colors via `_make_btn()`
- [x] **Cerulean header strip** on Login card for professional look
- [x] **Gold footer badge** — Shows encryption stack (AES-256-GCM · ECDH · Ed25519)
- [x] **Admin selector redesigned** — Styled radio buttons in a framed panel
- [x] **Sidebar redesigned** — Dark card with section divider, compact pill buttons
- [x] **Top bar** — Clock widget (live HH:MM:SS), Logout button
- [x] **Stat cards** — Clean flat cards with colored values
- [x] **Treeview** — Cerulean heading color, alternating row colors
- [x] **Password age badge** — Rows > 90 days old flagged in amber

### New Features Added (v2.0)
| Feature | Description |
|---------|-------------|
| **⏱ Live Clock** | Real-time HH:MM:SS in top bar, refreshes every second |
| **📋 Clipboard Auto-Clear** | Clipboard cleared automatically after 30 seconds |
| **⌨ Keyboard Shortcuts** | Ctrl+N (Add), Ctrl+F (Search), Ctrl+G (Generator), Delete (Delete) |
| **🔑 Password Age Badge** | Credentials older than 90 days shown in amber warning color |
| **Admin-aware file transfer** | Explicit guard: only Admin 1 can encrypt, only Admin 2 can decrypt |
| **Better error messages** | Descriptive ⚠ prefix on all auth error labels |

### Architecture (Unchanged — All Crypto Intact)
```
gui.py (UI) ─────────────────────────────────────────
  │
  ├── auth.py              Master password (SHA-256 + salt)
  ├── admin_auth.py        Admin accounts (PBKDF2 310K iterations)
  ├── encryption.py        Vault encryption (PBKDF2 200K + Fernet AES-128-CBC)
  ├── db_manager.py        SQLite CRUD (parameterised queries)
  ├── password_gen.py      Cryptographically secure generator
  │
  ├── identity_keys.py     ECDH + Ed25519 keys (AES-256-GCM encrypted on disk)
  ├── key_exchange.py      ECDH SECP256R1 + HKDF-SHA256
  ├── file_sharing.py      AES-256-GCM chunked file encrypt/decrypt + Ed25519 sign
  │
  ├── sharing.py           Credential-to-credential sharing logic
  └── sharing_ui.py        Secure sharing UI dialog
```

---

## 🔐 Cryptographic Algorithms in This Project

| Layer | Algorithm | Purpose |
|-------|-----------|---------|
| Vault passwords | AES-128-CBC (Fernet) | Encrypt stored credentials |
| Key derivation | PBKDF2-HMAC-SHA256 (200K) | Master password → encryption key |
| Admin auth | PBKDF2-HMAC-SHA256 (310K) | Admin password verifier |
| File encryption | **AES-256-GCM** | Encrypt file chunks (authenticated) |
| Key exchange | **ECDH SECP256R1** | Derive shared key without transmitting it |
| Key expansion | **HKDF-SHA256** | Shared secret → 256-bit AES key |
| Digital signature | **Ed25519** | Karthik signs file; Sanjana verifies |
| Identity storage | AES-256-GCM | Private keys encrypted on disk |
| Hash | SHA-256 | Fingerprints, master password hash |

---

## 📁 File Structure
```
Secure-Password-Manager-main/
├── main.py              ← Entry point (run this)
├── gui.py               ← UI — REDESIGNED v2.0
├── auth.py              ← Master password
├── encryption.py        ← Fernet encrypt/decrypt
├── db_manager.py        ← SQLite operations
├── password_gen.py      ← Password generator + strength
├── admin_auth.py        ← Admin 1 & Admin 2 auth
├── identity_keys.py     ← ECDH + Ed25519 key management
├── key_exchange.py      ← ECDH + HKDF helpers
├── file_sharing.py      ← .svf package encrypt/decrypt
├── sharing.py           ← Credential sharing
├── sharing_ui.py        ← Sharing UI
├── requirements.txt     ← cryptography, customtkinter
├── PROGRESS.md          ← This file (progress tracker)
└── data/                ← Auto-created at runtime
    ├── vault.db
    ├── salt.bin
    ├── master.hash
    └── admin_identities/
        ├── admin1/      ← Karthik/Prakhar identity
        └── admin2/      ← Sanjana/Karthik identity
```

---

## 🚀 How to Run
```cmd
cd "C:\Users\ASUS\Desktop\Projects\CNS Project\Secure-Password-Manager-main (2)\Secure-Password-Manager-main\Secure-Password-Manager-main"
python main.py
```

## 🧪 How to Run Tests
```cmd
python -m pytest tests/ -v
```

---

## 📌 Pending / Future Improvements
- [ ] Export vault as encrypted backup file
- [ ] Dark/Light theme toggle button in top bar
- [ ] Auto-lock after inactivity (e.g., 5 minutes)
- [ ] Category/tag system for credentials
- [ ] Clipboard history viewer (optional)
- [ ] SHA-256 hash viewer for the .svf package (demo feature)
