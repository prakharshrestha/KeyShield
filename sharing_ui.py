
"""
SecureVault - Credential Sharing GUI

Provides:
1. Generate or load local identity
2. Export public identity
3. Import and verify recipient identity
4. Share selected credential
5. Receive and save a credential
"""

import json
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

import identity_keys
import sharing
import encryption
import db_manager


COLORS = {
    "bg_dark": "#0F172A",
    "bg_card": "#1E293B",
    "primary": "#3B82F6",
    "success": "#22C55E",
    "text": "#F8FAFC",
    "secondary": "#94A3B8"
}


class SecureSharingDialog:

    def __init__(self, app):
        self.app = app
        self.local_identity = None
        self.recipient_identity = None

        self.window = ctk.CTkToplevel(app.root)
        self.window.title("SecureVault - Cryptographic Sharing")
        self.window.geometry("620x570")
        self.window.configure(fg_color=COLORS["bg_dark"])
        self.window.transient(app.root)
        self.window.grab_set()

        self._build_interface()

    def _build_interface(self):

        ctk.CTkLabel(
            self.window,
            text="🔐 Secure Credential Sharing",
            font=ctk.CTkFont(size=23, weight="bold"),
            text_color=COLORS["text"]
        ).pack(pady=(25, 5))

        ctk.CTkLabel(
            self.window,
            text="ECDH + HKDF + AES-256-GCM + Ed25519",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["secondary"]
        ).pack(pady=(0, 20))

        card = ctk.CTkFrame(
            self.window,
            fg_color=COLORS["bg_card"],
            corner_radius=12
        )
        card.pack(fill="both", expand=True, padx=25, pady=10)

        self.status = ctk.CTkLabel(
            card,
            text="Your cryptographic identity is not loaded.",
            text_color=COLORS["secondary"],
            wraplength=500
        )
        self.status.pack(pady=(18, 15))

        buttons = [
            ("1. Generate / Load My Identity",
             self._load_or_create_identity),

            ("2. Export My Public Identity",
             self._export_identity),

            ("3. Import Recipient Public Identity",
             self._import_recipient),

            ("4. Share Selected Credential",
             self._share_credential),

            ("5. Receive Credential Package",
             self._receive_credential)
        ]

        for label, command in buttons:
            ctk.CTkButton(
                card,
                text=label,
                height=43,
                width=440,
                fg_color=COLORS["primary"],
                hover_color="#2563EB",
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=13, weight="bold"),
                command=command
            ).pack(pady=7)

        ctk.CTkLabel(
            card,
            text="Always verify public-key fingerprints through a trusted channel.",
            text_color=COLORS["secondary"],
            wraplength=450,
            font=ctk.CTkFont(size=11)
        ).pack(pady=(18, 5))

        ctk.CTkButton(
            self.window,
            text="Close",
            width=130,
            fg_color="#334155",
            hover_color="#475569",
            command=self.window.destroy
        ).pack(pady=15)

    def _ensure_identity(self):
        """Load an existing identity or create one if none exists."""

        if not self.app.master_password:
            raise ValueError("Please log in to your vault first.")

        identity_dir = Path("data/identity")
        private_file = identity_dir / "identity_private.enc"
        public_file = identity_dir / "identity_public.json"

        if private_file.exists() and public_file.exists():
            self.local_identity = identity_keys.load_identity(
                self.app.master_password,
                identity_dir
            )

        elif private_file.exists() or public_file.exists():
            raise ValueError(
                "Identity files are incomplete. Restore them from backup."
            )

        else:
            self.local_identity = identity_keys.create_identity(
                self.app.master_password,
                identity_dir
            )

        return self.local_identity

    def _load_or_create_identity(self):

        try:
            self._ensure_identity()

            self.status.configure(
                text="Your cryptographic identity is ready.",
                text_color=COLORS["success"]
            )

            messagebox.showinfo(
                "Identity Ready",
                "Your ECDH and Ed25519 identity keys are ready."
            )

        except Exception as exc:
            messagebox.showerror("Identity Error", str(exc))

    def _export_identity(self):

        try:
            identity = self._ensure_identity()

            path = filedialog.asksaveasfilename(
                parent=self.window,
                title="Export Public Identity",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )

            if not path:
                return

            identity_keys.export_public_identity(
                identity,
                path
            )

            messagebox.showinfo(
                "Export Successful",
                "Your PUBLIC identity was exported.\n\n"
                "Share this file with the recipient.\n"
                "Never share your private identity file."
            )

        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def _import_recipient(self):

        path = filedialog.askopenfilename(
            parent=self.window,
            title="Select Recipient Public Identity",
            filetypes=[("JSON files", "*.json")]
        )

        if not path:
            return

        try:
            recipient = identity_keys.load_public_identity(path)

            fingerprint = recipient["fingerprint"]

            approved = messagebox.askyesno(
                "Verify Recipient Identity",
                "Recipient fingerprint:\n\n"
                f"{fingerprint}\n\n"
                "Compare this fingerprint with the recipient "
                "using a separate trusted channel.\n\n"
                "Have you independently verified it?"
            )

            if not approved:
                return

            self.recipient_identity = recipient

            self.status.configure(
                text="Recipient identity imported and fingerprint verified.",
                text_color=COLORS["success"]
            )

            messagebox.showinfo(
                "Recipient Ready",
                "Recipient public identity is ready for sharing."
            )

        except Exception as exc:
            messagebox.showerror("Import Error", str(exc))

    def _share_credential(self):

        try:
            sender = self._ensure_identity()

            if self.recipient_identity is None:
                messagebox.showwarning(
                    "Recipient Required",
                    "Import and verify the recipient's public identity first."
                )
                return

            cred = self.app._get_selected_credential()

            if cred is None:
                return

            # Database tuple:
            # id, website, username, encrypted_pass, notes,
            # created_at, updated_at

            website = cred[1]
            username = cred[2]
            password = encryption.decrypt_password(
                cred[3],
                self.app.master_password
            )
            notes = cred[4] or ""

            credential = {
                "website": website,
                "username": username,
                "password": password,
                "notes": notes
            }

            package = sharing.create_share_package(
                sender,
                self.recipient_identity,
                credential
            )

            path = filedialog.asksaveasfilename(
                parent=self.window,
                title="Save Encrypted Credential Package",
                defaultextension=".json",
                initialfile="securevault_share.json",
                filetypes=[("JSON files", "*.json")]
            )

            if not path:
                return

            Path(path).write_text(
                json.dumps(package, indent=4),
                encoding="utf-8"
            )

            messagebox.showinfo(
                "Sharing Successful",
                "Credential encrypted and signed successfully.\n\n"
                "Send the JSON package to the recipient."
            )

        except Exception as exc:
            messagebox.showerror("Sharing Error", str(exc))

    def _receive_credential(self):

        try:
            receiver = self._ensure_identity()

            # Import and independently verify sender identity.
            sender_path = filedialog.askopenfilename(
                parent=self.window,
                title="Select Trusted Sender Public Identity",
                filetypes=[("JSON files", "*.json")]
            )

            if not sender_path:
                return

            trusted_sender = identity_keys.load_public_identity(
                sender_path
            )

            fingerprint = trusted_sender["fingerprint"]

            approved = messagebox.askyesno(
                "Verify Sender Identity",
                "Sender fingerprint:\n\n"
                f"{fingerprint}\n\n"
                "Compare this with the sender's fingerprint "
                "through a separate trusted channel.\n\n"
                "Have you independently verified it?"
            )

            if not approved:
                return

            # Select encrypted sharing package.
            package_path = filedialog.askopenfilename(
                parent=self.window,
                title="Select Encrypted Credential Package",
                filetypes=[("JSON files", "*.json")]
            )

            if not package_path:
                return

            package = json.loads(
                Path(package_path).read_text(encoding="utf-8")
            )

            credential = sharing.open_share_package(
                receiver,
                package,
                trusted_sender
            )

            # Validate received fields.
            required = ("website", "username", "password")

            if any(
                not isinstance(credential.get(key), str)
                or not credential[key].strip()
                for key in required
            ):
                raise ValueError("Received credential fields are invalid.")

            notes = credential.get("notes", "")

            if not isinstance(notes, str):
                raise ValueError("Received notes are invalid.")

            # Re-encrypt password using receiver's own vault key.
            encrypted_password = encryption.encrypt_password(
                credential["password"],
                self.app.master_password
            )

            # Save using existing SQLite database.
            db_manager.insert_credential(
                credential["website"],
                credential["username"],
                encrypted_password,
                notes
            )

            self.app._refresh_credentials()

            messagebox.showinfo(
                "Credential Received",
                "Signature verified successfully.\n"
                "Credential decrypted and saved in your vault."
            )

        except Exception as exc:
            messagebox.showerror(
                "Receive Error",
                f"Credential could not be received:\n\n{exc}"
            )
