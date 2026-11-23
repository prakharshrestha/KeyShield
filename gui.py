"""
gui.py – SecureVault Password Manager GUI  v5.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Deep-blue cyber palette  ·  Vibrant bokeh particle network background
(cursor-reactive glowing nodes + connecting lines + atmospheric bokeh)
All 9 sidebar actions  ·  Full credential management
"""

from __future__ import annotations

import math
import random
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from pathlib import Path

import customtkinter as ctk

import admin_auth
import auth
import db_manager
import encryption
import file_sharing
import identity_keys
import password_gen
from sharing_ui import SecureSharingDialog

# ═══════════════════════════  PALETTE  ═══════════════════════════════════════
C = {
    # backgrounds – deep navy blues (vibrant, not dull teal)
    "bg":      "#0B1426",   # deep space navy
    "bg2":     "#0F1B32",   # slightly lighter
    "card":    "#111D35",   # card surface
    "card2":   "#182845",   # elevated card / inputs
    "card3":   "#203354",   # hover card
    "nav":     "#070E1C",   # topbar / footer (darkest)
    # blue accent
    "blue":    "#3B82F6",
    "blue_h":  "#2563EB",
    "blue_l":  "#60A5FA",
    "blue_d":  "#1E3A6E",
    # cyan glow
    "cyan":    "#00D4FF",
    "cyan_h":  "#33E0FF",
    "cyan_d":  "#0A3550",
    # warm accents (peach / coral from reference)
    "peach":   "#C9956A",
    "peach_h": "#E8B07A",
    "peach_l": "#FFCB9A",
    "coral":   "#FF6B9D",
    "coral_d": "#5A2040",
    # semantic
    "ok":      "#22C55E",  "ok_h":    "#16A34A",
    "warn":    "#F59E0B",  "warn_h":  "#D97706",
    "err":     "#EF4444",  "err_h":   "#DC2626",
    "purple":  "#7C3AED",  "purple_h":"#6D28D9",
    # text
    "t1":      "#E8F0FE",   # primary (blue-white)
    "t2":      "#8BA3C7",   # secondary
    "t3":      "#4A6B8A",   # muted
    # borders
    "bdr":     "#1A2D50",
    "bdr2":    "#253D65",
    "bdr_b":   "#3B82F6",
    "bdr_c":   "#00D4FF",
}


# ═══════════════════════════  PARTICLE BACKGROUND  ═══════════════════════════
class ParticleBG:
    """
    Animated network-node particle background with bokeh atmosphere.
    Nodes bounce, connect via glowing lines, react to cursor.
    Large bokeh circles drift slowly for depth-of-field effect.
    """
    N_NODES  = 30
    N_BOKEH  = 8
    SPEED    = 0.45
    CONN_D   = 155
    CUR_D    = 180
    FRAME    = 33

    def __init__(self, canvas: tk.Canvas, w: int, h: int) -> None:
        self.cv  = canvas
        self.w   = max(w, 1)
        self.h   = max(h, 1)
        self.mx  = w // 2
        self.my  = h // 2
        self._alive = True
        self._nodes: list[dict] = []
        self._bokeh: list[dict] = []
        self._init_nodes()
        self._init_bokeh()
        self._animate()

    def _init_nodes(self) -> None:
        self._nodes = []
        for i in range(self.N_NODES):
            # ~20% warm, ~80% cool
            warm = (i % 5 == 0)
            angle = random.uniform(0, 2 * math.pi)
            sp = random.uniform(0.15, self.SPEED)
            self._nodes.append({
                "x":  random.uniform(20, self.w - 20),
                "y":  random.uniform(20, self.h - 20),
                "vx": math.cos(angle) * sp,
                "vy": math.sin(angle) * sp,
                "r":  random.uniform(3, 7),
                "warm": warm,
            })

    def _init_bokeh(self) -> None:
        """Large, slow-drifting atmospheric bokeh circles."""
        self._bokeh = []
        for _ in range(self.N_BOKEH):
            warm = random.random() < 0.3
            self._bokeh.append({
                "x":  random.uniform(0, self.w),
                "y":  random.uniform(0, self.h),
                "vx": random.uniform(-0.12, 0.12),
                "vy": random.uniform(-0.12, 0.12),
                "r":  random.uniform(25, 60),
                "warm": warm,
            })

    def resize(self, w: int, h: int) -> None:
        self.w = max(w, 1)
        self.h = max(h, 1)

    def on_motion(self, x: int, y: int) -> None:
        self.mx = x
        self.my = y

    def stop(self) -> None:
        self._alive = False

    def _animate(self) -> None:
        if not self._alive:
            return
        self._update()
        self._draw()
        try:
            self.cv.after(self.FRAME, self._animate)
        except Exception:
            pass

    def _update(self) -> None:
        # update network nodes
        for nd in self._nodes:
            dx = self.mx - nd["x"]
            dy = self.my - nd["y"]
            dist = math.hypot(dx, dy)
            if 0 < dist < self.CUR_D:
                f = (1 - dist / self.CUR_D) * 0.015
                nd["vx"] += dx / dist * f
                nd["vy"] += dy / dist * f
            sp = math.hypot(nd["vx"], nd["vy"])
            if sp > self.SPEED * 1.8:
                nd["vx"] = nd["vx"] / sp * self.SPEED * 1.8
                nd["vy"] = nd["vy"] / sp * self.SPEED * 1.8
            nd["x"] += nd["vx"]
            nd["y"] += nd["vy"]
            if nd["x"] < 5:        nd["x"] = 5;         nd["vx"] *= -1
            if nd["x"] > self.w-5: nd["x"] = self.w-5;  nd["vx"] *= -1
            if nd["y"] < 5:        nd["y"] = 5;         nd["vy"] *= -1
            if nd["y"] > self.h-5: nd["y"] = self.h-5;  nd["vy"] *= -1

        # update bokeh
        for bk in self._bokeh:
            bk["x"] += bk["vx"]
            bk["y"] += bk["vy"]
            if bk["x"] < -bk["r"]:     bk["x"] = self.w + bk["r"]
            if bk["x"] > self.w + bk["r"]: bk["x"] = -bk["r"]
            if bk["y"] < -bk["r"]:     bk["y"] = self.h + bk["r"]
            if bk["y"] > self.h + bk["r"]: bk["y"] = -bk["r"]

    def _draw(self) -> None:
        cv = self.cv
        try:
            cv.delete("p")
        except Exception:
            return

        # background fill
        cv.create_rectangle(0, 0, self.w + 2, self.h + 2,
                            fill=C["bg"], outline="", tags="p")

        mx, my = self.mx, self.my

        # draw bokeh circles (atmospheric depth)
        for bk in self._bokeh:
            r = bk["r"]
            if bk["warm"]:
                fill = "#1A0A15"      # very subtle warm
                outline = "#3D1530"
            else:
                fill = "#0A1530"
                outline = "#1A3060"
            cv.create_oval(bk["x"]-r, bk["y"]-r, bk["x"]+r, bk["y"]+r,
                           fill=fill, outline=outline, width=1.5, tags="p")

        # draw connecting lines
        for i, a in enumerate(self._nodes):
            for b in self._nodes[i+1:]:
                dist = math.hypot(a["x"]-b["x"], a["y"]-b["y"])
                if dist > self.CONN_D:
                    continue
                alpha = 1 - dist / self.CONN_D
                near_cur = (math.hypot(a["x"]-mx, a["y"]-my) < self.CUR_D or
                            math.hypot(b["x"]-mx, b["y"]-my) < self.CUR_D)
                if near_cur:
                    if a["warm"] or b["warm"]:
                        col = "#FF8DC7" if alpha > 0.5 else "#7A3055"
                    else:
                        col = C["cyan"] if alpha > 0.5 else "#1A6080"
                    w = max(0.6, alpha * 2.0)
                else:
                    col = "#1A3565" if not (a["warm"] and b["warm"]) else "#3D2030"
                    w = max(0.3, alpha * 1.0)
                cv.create_line(a["x"], a["y"], b["x"], b["y"],
                               fill=col, width=w, tags="p")

        # draw nodes
        for nd in self._nodes:
            nx, ny, r = nd["x"], nd["y"], nd["r"]
            d = math.hypot(nx - mx, ny - my)
            near = d < self.CUR_D

            if nd["warm"]:
                core = "#FF6B9D" if near else "#AA4466"
                glow = "#FF8DC7"
            else:
                core = C["cyan"] if near else C["blue"]
                glow = C["cyan_h"]

            rr = r * (1.8 if near else 1.0)

            # outer glow ring
            if near:
                cv.create_oval(nx-rr-8, ny-rr-8, nx+rr+8, ny+rr+8,
                               outline=glow, width=1, tags="p")
                cv.create_oval(nx-rr-4, ny-rr-4, nx+rr+4, ny+rr+4,
                               outline=glow, width=1, tags="p")

            # core circle
            cv.create_oval(nx-rr, ny-rr, nx+rr, ny+rr,
                           fill=core, outline="", tags="p")

        # cursor lines from nearby nodes
        for nd in self._nodes:
            d = math.hypot(nd["x"]-mx, nd["y"]-my)
            if d < self.CUR_D:
                alpha = 1 - d / self.CUR_D
                col = "#FF8DC7" if nd["warm"] else C["cyan"]
                cv.create_line(nd["x"], nd["y"], mx, my,
                               fill=col, width=max(0.4, alpha*1.5), tags="p")

        # cursor dot
        cv.create_oval(mx-4, my-4, mx+4, my+4,
                       fill=C["cyan"], outline=C["cyan_h"], width=1, tags="p")


# ═══════════════════════════  HELPERS  ═══════════════════════════════════════
def _pill(parent, text, bg, hbg, cmd,
          w=174, h=38, r=19, fg=None):
    if fg is None:
        fg = C["t1"]
    return ctk.CTkButton(
        parent, text=text, command=cmd,
        width=w, height=h, corner_radius=r,
        fg_color=bg, hover_color=hbg,
        text_color=fg,
        font=ctk.CTkFont(size=12, weight="bold"),
    )


def _card(parent, **kw):
    defaults = dict(fg_color=C["card"], corner_radius=12,
                    border_width=1, border_color=C["bdr"])
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def _card_hover(frame, nb=None, hb=None, nc=None, hc=None):
    if nb is None: nb = C["card"]
    if hb is None: hb = C["card3"]
    if nc is None: nc = C["bdr"]
    if hc is None: hc = C["bdr_b"]

    def _enter(_e=None):
        try: frame.configure(fg_color=hb, border_color=hc)
        except: pass
    def _leave(_e=None):
        try: frame.configure(fg_color=nb, border_color=nc)
        except: pass
    for w in [frame] + list(frame.winfo_children()):
        try:
            w.bind("<Enter>", _enter, add="+")
            w.bind("<Leave>", _leave, add="+")
        except: pass


# ═══════════════════════════  MAIN APP  ══════════════════════════════════════
class PasswordManagerApp:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title("SecureVault — CNS Project")
        self.root.geometry("1080x700")
        self.root.minsize(900, 600)
        self.root.configure(fg_color=C["bg"])

        self.master_password = None
        self.admin_info = None

        # container holds everything
        self.container = ctk.CTkFrame(self.root, fg_color=C["bg"], corner_radius=0)
        self.container.pack(fill="both", expand=True)

        # particle canvas
        self._pcanvas = None
        self._particles = None
        self._init_particles()

        self.root.bind("<Motion>", self._on_motion)
        self.root.bind("<Configure>", self._on_resize)

        self._show_login()

    # ── particles ─────────────────────────────────────────────────────────────
    def _init_particles(self):
        if self._particles:
            self._particles.stop()
        if self._pcanvas:
            try: self._pcanvas.destroy()
            except: pass
        w = max(self.root.winfo_width(), 980)
        h = max(self.root.winfo_height(), 680)
        cv = tk.Canvas(self.container, bg=C["bg"], highlightthickness=0,
                       bd=0, relief="flat")
        cv.place(x=0, y=0, relwidth=1, relheight=1)
        # Use Misc.lower to lower the Canvas *widget* in the stacking order
        tk.Misc.lower(cv)
        self._pcanvas  = cv
        self._particles = ParticleBG(cv, w, h)

    def _on_motion(self, e):
        if self._particles:
            try:
                cx = e.x_root - self.container.winfo_rootx()
                cy = e.y_root - self.container.winfo_rooty()
                self._particles.on_motion(cx, cy)
            except: pass

    def _on_resize(self, e):
        if e.widget is self.root and self._particles:
            self._particles.resize(e.width, e.height)

    def _clear(self):
        for w in list(self.container.winfo_children()):
            try: w.destroy()
            except: pass
        self._pcanvas = None
        self._particles = None
        self._init_particles()

    # ══════════════════════════════════════════════════════════════════════════
    #                           LOGIN SCREENS
    # ══════════════════════════════════════════════════════════════════════════
    def _show_login(self):
        self._clear()
        self.root.title("SecureVault — Login")

        is_first = auth.is_first_run()
        needs_admin = admin_auth.count_accounts() == 0

        # center wrapper (transparent so particles show through)
        wrap = ctk.CTkFrame(self.container, fg_color="transparent")
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        # crypto badges
        badge_row = ctk.CTkFrame(wrap, fg_color="transparent")
        badge_row.pack(pady=(0, 16))
        for tag in ("AES-256-GCM", "ECDH", "Ed25519", "PBKDF2"):
            ctk.CTkLabel(badge_row, text=tag,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=C["cyan"],
                         fg_color=C["cyan_d"], corner_radius=6,
                         padx=8, pady=3).pack(side="left", padx=4)

        # login card
        card = _card(wrap, corner_radius=20, border_color=C["bdr_b"])
        card.pack()
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=40, pady=36)

        # title
        ctk.CTkLabel(inner, text="🔐  SecureVault",
                     font=ctk.CTkFont(size=30, weight="bold"),
                     text_color=C["cyan"]).pack()
        ctk.CTkLabel(inner, text="Choose an administrator and unlock your vault",
                     font=ctk.CTkFont(size=12),
                     text_color=C["t2"]).pack(pady=(4, 22))

        if needs_admin:
            self._build_admin_setup(inner, is_first)
        elif is_first:
            self._build_vault_setup(inner)
        else:
            self._build_login_form(inner)

    def _build_admin_setup(self, parent, is_first_vault):
        ctk.CTkLabel(parent,
                     text="FIRST RUN – Set up Administrator Accounts",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["peach"]).pack(pady=(0, 16))

        fields = {}
        for lbl, key, show in [
            ("Admin 1 Name", "a1n", ""),
            ("Admin 1 Password", "a1p", "●"),
            ("Admin 2 Name", "a2n", ""),
            ("Admin 2 Password", "a2p", "●"),
        ]:
            ctk.CTkLabel(parent, text=lbl, font=ctk.CTkFont(size=11),
                         text_color=C["t2"], anchor="w").pack(fill="x")
            e = ctk.CTkEntry(parent, width=330,
                             fg_color=C["card2"], border_color=C["bdr2"],
                             text_color=C["t1"], show=show, corner_radius=10)
            e.pack(pady=(0, 10))
            fields[key] = e

        err_lbl = ctk.CTkLabel(parent, text="", text_color=C["err"],
                               font=ctk.CTkFont(size=11), wraplength=300)
        err_lbl.pack()

        def _do():
            a1n = fields["a1n"].get().strip()
            a1p = fields["a1p"].get()
            a2n = fields["a2n"].get().strip()
            a2p = fields["a2p"].get()
            try:
                admin_auth.setup_accounts(a1n, a1p, a2n, a2p)
                self._ensure_admin_identity(1, a1p)
                self._ensure_admin_identity(2, a2p)
            except ValueError as ex:
                err_lbl.configure(text=str(ex)); return
            self._show_login()

        _pill(parent, "Create Accounts", C["blue"], C["blue_h"], _do,
              w=330, h=42).pack(pady=(12, 0))

    def _build_vault_setup(self, parent):
        ctk.CTkLabel(parent, text="Set Vault Master Password",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["peach"]).pack(pady=(0, 14))

        pw1 = ctk.CTkEntry(parent, width=330, placeholder_text="Choose master password",
                           fg_color=C["card2"], border_color=C["bdr2"],
                           text_color=C["t1"], show="●", corner_radius=10)
        pw1.pack(pady=(0, 10))
        pw2 = ctk.CTkEntry(parent, width=330, placeholder_text="Confirm master password",
                           fg_color=C["card2"], border_color=C["bdr2"],
                           text_color=C["t1"], show="●", corner_radius=10)
        pw2.pack(pady=(0, 10))

        err_lbl = ctk.CTkLabel(parent, text="", text_color=C["err"],
                               font=ctk.CTkFont(size=11), wraplength=300)
        err_lbl.pack()

        def _do():
            if pw1.get() != pw2.get():
                err_lbl.configure(text="Passwords do not match."); return
            ok, msg = auth.setup_master_password(pw1.get())
            if not ok:
                err_lbl.configure(text=msg); return
            self._show_login()

        _pill(parent, "Set Master Password", C["blue"], C["blue_h"], _do,
              w=330, h=42).pack(pady=(12, 0))

    def _build_login_form(self, parent):
        admin_var = tk.IntVar(value=1)
        rrow = ctk.CTkFrame(parent, fg_color="transparent")
        rrow.pack(pady=(0, 16))
        for n, label in ((1, "Admin 1"), (2, "Admin 2")):
            ctk.CTkRadioButton(rrow, text=label, variable=admin_var, value=n,
                               text_color=C["t1"],
                               fg_color=C["blue"],
                               hover_color=C["blue_h"]).pack(side="left", padx=16)

        adm_pw = ctk.CTkEntry(parent, width=330,
                              placeholder_text="Administrator password",
                              fg_color=C["card2"], border_color=C["bdr2"],
                              text_color=C["t1"], show="●", corner_radius=10)
        adm_pw.pack(pady=(0, 10))

        vlt_pw = ctk.CTkEntry(parent, width=330,
                              placeholder_text="Vault master password",
                              fg_color=C["card2"], border_color=C["bdr2"],
                              text_color=C["t1"], show="●", corner_radius=10)
        vlt_pw.pack(pady=(0, 10))

        err_lbl = ctk.CTkLabel(parent, text="", text_color=C["err"],
                               font=ctk.CTkFont(size=11), wraplength=300)
        err_lbl.pack()

        def _do_login(_e=None):
            info = admin_auth.authenticate(admin_var.get(), adm_pw.get())
            if info is None:
                err_lbl.configure(text="Invalid administrator credentials."); return
            if not auth.verify_master_password(vlt_pw.get()):
                err_lbl.configure(text="Invalid vault master password."); return
            self.admin_info = info
            self.master_password = vlt_pw.get()
            self._show_dashboard()

        adm_pw.bind("<Return>", _do_login)
        vlt_pw.bind("<Return>", _do_login)

        _pill(parent, "🔓  Unlock Administrator Dashboard",
              C["blue"], C["blue_h"], _do_login,
              w=330, h=44).pack(pady=(14, 0))

    # ══════════════════════════════════════════════════════════════════════════
    #                           DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    def _show_dashboard(self):
        self._clear()
        name = self.admin_info["name"]
        no   = self.admin_info["number"]
        self.root.title("SecureVault — CNS Project")

        # ── TOPBAR ────────────────────────────────────────────────────────────
        topbar = ctk.CTkFrame(self.container, fg_color=C["nav"],
                              corner_radius=0, height=50)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        ctk.CTkLabel(topbar, text="🔐  SecureVault",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["cyan"]).pack(side="left", padx=(18, 0))
        ctk.CTkLabel(topbar, text="│  CNS Project",
                     font=ctk.CTkFont(size=12), text_color=C["t3"]
                     ).pack(side="left", padx=(6, 0))

        # crypto badges
        for tag in ("AES-256-GCM", "ECDH", "Ed25519"):
            ctk.CTkLabel(topbar, text=tag,
                         font=ctk.CTkFont(size=9, weight="bold"),
                         text_color=C["cyan"], fg_color=C["cyan_d"],
                         corner_radius=5, padx=6, pady=2
                         ).pack(side="left", padx=3)

        # admin badge + logout
        ctk.CTkLabel(topbar,
                     text=f"  Admin {no}  {name}  ",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["cyan"],
                     fg_color=C["blue_d"], corner_radius=10
                     ).pack(side="right", padx=(0, 8), pady=10)

        _pill(topbar, "⏻  Logout", C["err"], C["err_h"], self._logout,
              w=96, h=32, r=10).pack(side="right", padx=6, pady=10)

        # ── WELCOME BAR ───────────────────────────────────────────────────────
        wbar = ctk.CTkFrame(self.container, fg_color="transparent")
        wbar.pack(fill="x", padx=24, pady=(12, 0))

        ctk.CTkLabel(wbar, text=f"Welcome back, {name}  👋",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C["t1"]).pack(side="left")
        ctk.CTkLabel(wbar,
                     text=f"Admin {no} Dashboard  •  Encrypted Vault  •  Secure File Transfer"
                          "   Ctrl+N Add   Ctrl+F Search   Ctrl+G Gen",
                     font=ctk.CTkFont(size=10), text_color=C["t3"]
                     ).pack(side="left", padx=14)

        # ── STAT CARDS ────────────────────────────────────────────────────────
        stats_fr = ctk.CTkFrame(self.container, fg_color="transparent")
        stats_fr.pack(fill="x", padx=24, pady=(12, 0))

        all_creds = db_manager.get_all_credentials()
        n_total = len(all_creds)

        score_txt = "—/100"
        n_weak = 0
        last_upd = "N/A"
        if n_total:
            strong = 0
            for r in all_creds:
                try:
                    pw = encryption.decrypt_password(r[3], self.master_password)
                    s = password_gen.evaluate_strength(pw)
                    if s == "Strong": strong += 1
                    if s in ("Weak", "Medium"): n_weak += 1
                except: pass
            score_txt = f"{int(strong/n_total*100)}/100"
            last_upd = all_creds[0][6][:10] if all_creds[0][6] else "N/A"

        stat_defs = [
            ("🔑", str(n_total), "Total Passwords",  C["blue_l"]),
            ("🛡",  score_txt,    "Security Score",   C["ok"]),
            ("📅",  last_upd,     "Last Updated",     C["t2"]),
            ("⚠",  str(n_weak),  "Need Attention",   C["warn"]),
        ]
        for col_i, (icon, val, lbl, vcol) in enumerate(stat_defs):
            sc = _card(stats_fr, corner_radius=12)
            sc.grid(row=0, column=col_i, padx=(0 if col_i == 0 else 8, 0), sticky="ew")
            stats_fr.columnconfigure(col_i, weight=1)

            top = ctk.CTkFrame(sc, fg_color="transparent")
            top.pack(anchor="w", padx=16, pady=(14, 2))
            ctk.CTkLabel(top, text="●", text_color=vcol,
                         font=ctk.CTkFont(size=10)).pack(side="left")
            ctk.CTkLabel(top, text=f"  {icon}",
                         font=ctk.CTkFont(size=16), text_color=C["t2"]).pack(side="left")

            ctk.CTkLabel(sc, text=val,
                         font=ctk.CTkFont(size=22, weight="bold"),
                         text_color=vcol).pack(anchor="w", padx=16)
            ctk.CTkLabel(sc, text=lbl,
                         font=ctk.CTkFont(size=11), text_color=C["t3"]
                         ).pack(anchor="w", padx=16, pady=(0, 14))
            _card_hover(sc)

        # ── SEARCH BAR ────────────────────────────────────────────────────────
        srch_card = ctk.CTkFrame(self.container, fg_color=C["card2"],
                                 corner_radius=12, border_width=1,
                                 border_color=C["bdr2"])
        srch_card.pack(fill="x", padx=24, pady=(12, 0))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh_credentials())

        self._srch_entry = ctk.CTkEntry(srch_card,
                                        textvariable=self._search_var,
                                        placeholder_text="🔍  Search by website or username…",
                                        fg_color="transparent",
                                        border_width=0,
                                        text_color=C["t1"],
                                        font=ctk.CTkFont(size=13))
        self._srch_entry.pack(fill="x", padx=14, pady=9)

        # ── MAIN AREA: use grid so sidebar is guaranteed its column ──────────
        main_area = ctk.CTkFrame(self.container, fg_color="transparent")
        main_area.pack(fill="both", expand=True, padx=24, pady=(10, 0))
        main_area.columnconfigure(0, weight=1)   # left treeview expands
        main_area.columnconfigure(1, weight=0)   # sidebar fixed
        main_area.rowconfigure(0, weight=1)

        # ── TREEVIEW CARD (left) ──────────────────────────────────────────────
        tree_card = _card(main_area, corner_radius=14)
        tree_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self._setup_treeview_style()
        self._tree = ttk.Treeview(
            tree_card,
            columns=("id", "website", "username", "password", "notes", "created", "strength"),
            show="headings", selectmode="browse", style="V.Treeview")

        col_defs = [
            ("id",       "ID",           45,  False),
            ("website",  "Website / App",160, True),
            ("username", "Username",     120, True),
            ("password", "Password",     110, False),
            ("notes",    "Notes",        120, True),
            ("created",  "Created",      90,  False),
            ("strength", "Str",          45,  False),
        ]
        for cid, heading, w, stretch in col_defs:
            self._tree.heading(cid, text=heading,
                               command=lambda c=cid: self._sort_tree(c))
            self._tree.column(cid, width=w, minwidth=30, stretch=stretch)

        vsb = ttk.Scrollbar(tree_card, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        vsb.pack(side="right", fill="y", pady=10, padx=(0, 6))

        self._tree.bind("<Double-1>", lambda _: self._copy_password())
        self._tree_sort_col  = ""
        self._tree_sort_asc  = True

        # ── SIDEBAR (right) ───────────────────────────────────────────────────
        sidebar = _card(main_area, corner_radius=14, fg_color=C["card"])
        sidebar.grid(row=0, column=1, sticky="ns")

        sb = ctk.CTkFrame(sidebar, fg_color="transparent")
        sb.pack(fill="both", expand=True, padx=10, pady=12)

        # title
        ctk.CTkLabel(sb, text="ACTIONS",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C["t3"]).pack(anchor="w", pady=(0, 6))

        def sb_btn(text, bg, hbg, cmd, fg_c=None):
            b = _pill(sb, text, bg, hbg, cmd, w=172, h=37, r=18, fg=fg_c)
            b.pack(pady=3, fill="x")
            return b

        # ── Vault Management buttons ──
        sb_btn("➕  Add Password",    C["blue"],   C["blue_h"],   self._add_credential)
        sb_btn("✏️  Edit Entry",      C["card2"],  C["card3"],    self._edit_credential)
        sb_btn("🗑️  Delete Entry",    C["err"],    C["err_h"],    self._delete_credential)
        sb_btn("📋  Copy Password",   C["ok"],     C["ok_h"],     self._copy_password, "#fff")
        sb_btn("🎲  Generator",       C["card2"],  C["card3"],    self._open_generator)

        # divider
        ctk.CTkFrame(sb, height=1, fg_color=C["bdr2"]).pack(fill="x", pady=8)

        ctk.CTkLabel(sb, text="SECURE TRANSFER",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C["t3"]).pack(anchor="w", pady=(0, 6))

        # ── Cryptographic Sharing buttons ──
        sb_btn("🔐  Secure Sharing",  C["purple"], C["purple_h"], self._open_secure_sharing)
        sb_btn("📤  Encrypt & Share", C["peach"],  C["peach_h"],  self._encrypt_file, "#1a0a00")
        sb_btn("📥  Decrypt & Import",C["card2"],  C["card3"],    self._decrypt_file)
        sb_btn("🧾  File History",    C["card2"],  C["card3"],    self._show_history)

        # ── FOOTER ────────────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self.container, fg_color=C["nav"],
                              corner_radius=0, height=28)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self._status_lbl = ctk.CTkLabel(footer, text="",
                                        font=ctk.CTkFont(size=10),
                                        text_color=C["t3"])
        self._status_lbl.pack(side="left", padx=16, pady=5)

        ctk.CTkLabel(footer,
                     text="🔒 AES-256-GCM  •  ECDH  •  Ed25519  •  PBKDF2",
                     font=ctk.CTkFont(size=9),
                     text_color=C["t3"]).pack(side="right", padx=16, pady=5)

        # ── KEYBOARD SHORTCUTS ────────────────────────────────────────────────
        self.root.bind("<Control-n>", lambda _: self._add_credential())
        self.root.bind("<Control-N>", lambda _: self._add_credential())
        self.root.bind("<Control-f>", lambda _: self._srch_entry.focus())
        self.root.bind("<Control-F>", lambda _: self._srch_entry.focus())
        self.root.bind("<Control-g>", lambda _: self._open_generator())
        self.root.bind("<Control-G>", lambda _: self._open_generator())
        self.root.bind("<Delete>",    lambda _: self._delete_credential())

        self._refresh_credentials()

    # ── Treeview style ─────────────────────────────────────────────────────────
    def _setup_treeview_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("V.Treeview",
                        background=C["card"],
                        foreground=C["t1"],
                        rowheight=30,
                        fieldbackground=C["card"],
                        bordercolor=C["bdr"],
                        borderwidth=0,
                        font=("Segoe UI", 11))
        style.configure("V.Treeview.Heading",
                        background=C["card2"],
                        foreground=C["cyan"],
                        relief="flat",
                        font=("Segoe UI", 11, "bold"))
        style.map("V.Treeview",
                  background=[("selected", C["blue_d"])],
                  foreground=[("selected", C["cyan"])])
        style.map("V.Treeview.Heading",
                  background=[("active", C["card3"])])

    # ── Treeview helpers ───────────────────────────────────────────────────────
    def _refresh_credentials(self):
        q = self._search_var.get().strip() if hasattr(self, "_search_var") else ""
        rows = db_manager.search_credentials(q) if q else db_manager.get_all_credentials()

        for item in self._tree.get_children():
            self._tree.delete(item)

        for row in rows:
            cid, website, username, enc_pass, notes, created, _upd = row
            try:
                plain = encryption.decrypt_password(enc_pass, self.master_password)
                disp  = "●" * min(len(plain), 10)
                strength = password_gen.evaluate_strength(plain)
                badge = {"Strong": "✅", "Medium": "⚠️", "Weak": "❌"}.get(strength, "")
            except:
                disp = "⚠ error"; badge = "?"
            cshort = created[:10] if created else "—"
            self._tree.insert("", "end", iid=str(cid),
                              values=(cid, website, username, disp,
                                      notes or "—", cshort, badge))

        n = len(self._tree.get_children())
        total = len(db_manager.get_all_credentials())
        if hasattr(self, "_status_lbl"):
            self._status_lbl.configure(
                text=f"Showing {n} of {total} credentials stored.")

    def _sort_tree(self, col):
        if self._tree_sort_col == col:
            self._tree_sort_asc = not self._tree_sort_asc
        else:
            self._tree_sort_col = col; self._tree_sort_asc = True
        rows = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]
        rows.sort(reverse=not self._tree_sort_asc)
        for idx, (_, k) in enumerate(rows):
            self._tree.move(k, "", idx)

    def _get_selected_credential(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a credential first.")
            return None
        return db_manager.get_credential(int(sel[0]))

    # ══════════════════════════════════════════════════════════════════════════
    #                       CREDENTIAL ACTIONS
    # ══════════════════════════════════════════════════════════════════════════
    def _add_credential(self):
        self._credential_dialog("Add Password", None)

    def _edit_credential(self):
        cred = self._get_selected_credential()
        if cred:
            self._credential_dialog("Edit Entry", cred)

    def _credential_dialog(self, title, cred):
        dlg = ctk.CTkToplevel(self.root)
        dlg.title(f"SecureVault — {title}")
        dlg.geometry("470x560")
        dlg.configure(fg_color=C["bg"])
        dlg.transient(self.root)
        dlg.grab_set()

        ctk.CTkLabel(dlg,
                     text=f"{'➕' if cred is None else '✏️'}  {title}",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=C["cyan"]).pack(pady=(22, 4))

        card = _card(dlg, corner_radius=16, border_color=C["bdr_b"])
        card.pack(fill="both", expand=True, padx=26, pady=10)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=24, pady=20, fill="both", expand=True)

        fields = {}
        for key, label, show, default in [
            ("website",  "Website / App",  "",  cred[1] if cred else ""),
            ("username", "Username",       "",  cred[2] if cred else ""),
            ("password", "Password",       "●", ""),
            ("notes",    "Notes",          "",  cred[4] if cred else ""),
        ]:
            ctk.CTkLabel(inner, text=label, font=ctk.CTkFont(size=11),
                         text_color=C["t2"], anchor="w").pack(fill="x")
            e = ctk.CTkEntry(inner, width=390,
                             fg_color=C["card2"], border_color=C["bdr2"],
                             text_color=C["t1"], show=show, corner_radius=10)
            if default: e.insert(0, default)
            e.pack(pady=(0, 10))
            fields[key] = e

        if cred:
            try:
                fields["password"].insert(
                    0, encryption.decrypt_password(cred[3], self.master_password))
            except: pass

        # strength bar
        str_lbl = ctk.CTkLabel(inner, text="Strength: —",
                               font=ctk.CTkFont(size=11), text_color=C["t2"])
        str_lbl.pack(anchor="w")
        str_bar = ctk.CTkProgressBar(inner, width=390, progress_color=C["ok"])
        str_bar.set(0)
        str_bar.pack(pady=(2, 8))

        def _on_pw(*_a):
            pw = fields["password"].get()
            s  = password_gen.evaluate_strength(pw)
            cm = {"Strong": C["ok"], "Medium": C["warn"], "Weak": C["err"]}
            vm = {"Strong": 1.0,     "Medium": 0.5,       "Weak": 0.2}
            str_lbl.configure(text=f"Strength: {s}", text_color=cm.get(s, C["t2"]))
            str_bar.configure(progress_color=cm.get(s, C["ok"]))
            str_bar.set(vm.get(s, 0))

        fields["password"].bind("<KeyRelease>", _on_pw)

        err_lbl = ctk.CTkLabel(inner, text="", text_color=C["err"],
                               font=ctk.CTkFont(size=11), wraplength=340)
        err_lbl.pack()

        def _gen():
            pw = password_gen.generate_password(16)
            fields["password"].delete(0, "end")
            fields["password"].insert(0, pw)
            _on_pw()

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 0))
        _pill(btn_row, "🎲 Generate", C["card2"], C["card3"], _gen,
              w=130, h=34).pack(side="left")

        def _save():
            w = fields["website"].get().strip()
            u = fields["username"].get().strip()
            p = fields["password"].get()
            n = fields["notes"].get().strip()
            if not w or not u or not p:
                err_lbl.configure(text="Website, username and password are required."); return
            enc = encryption.encrypt_password(p, self.master_password)
            if cred:
                db_manager.update_credential(cred[0], w, u, enc, n)
            else:
                db_manager.insert_credential(w, u, enc, n)
            self._refresh_credentials()
            dlg.destroy()

        _pill(btn_row, "💾  Save", C["blue"], C["blue_h"], _save,
              w=130, h=34).pack(side="right")

    def _delete_credential(self):
        cred = self._get_selected_credential()
        if cred is None: return
        if messagebox.askyesno("Delete Entry",
                               f"Delete '{cred[1]}' ({cred[2]})?  This cannot be undone."):
            db_manager.delete_credential(cred[0])
            self._refresh_credentials()

    def _copy_password(self):
        cred = self._get_selected_credential()
        if cred is None: return
        try:
            pw = encryption.decrypt_password(cred[3], self.master_password)
            self.root.clipboard_clear()
            self.root.clipboard_append(pw)
            messagebox.showinfo("Copied", f"Password for '{cred[1]}' copied to clipboard.")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    # ── Password Generator ─────────────────────────────────────────────────────
    def _open_generator(self):
        dlg = ctk.CTkToplevel(self.root)
        dlg.title("SecureVault — Password Generator")
        dlg.geometry("450x500")
        dlg.configure(fg_color=C["bg"])
        dlg.transient(self.root)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="🎲  Password Generator",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=C["cyan"]).pack(pady=(22, 4))

        card = _card(dlg, corner_radius=16, border_color=C["bdr_b"])
        card.pack(fill="both", expand=True, padx=26, pady=10)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=24, pady=20, fill="both", expand=True)

        ctk.CTkLabel(inner, text="Length:", text_color=C["t2"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w")
        len_var = tk.IntVar(value=16)
        len_lbl = ctk.CTkLabel(inner, text="16", text_color=C["cyan"],
                               font=ctk.CTkFont(size=14, weight="bold"))
        len_lbl.pack(anchor="w")
        ctk.CTkSlider(inner, from_=8, to=64, variable=len_var,
                      progress_color=C["blue"], button_color=C["cyan"],
                      button_hover_color=C["cyan_h"],
                      command=lambda v: len_lbl.configure(text=str(int(v)))
                      ).pack(fill="x", pady=(0, 14))

        use_upper  = tk.BooleanVar(value=True)
        use_digits = tk.BooleanVar(value=True)
        use_sym    = tk.BooleanVar(value=True)
        for lbl, var in [("Uppercase (A-Z)", use_upper),
                         ("Digits (0-9)", use_digits),
                         ("Symbols (!@#…)", use_sym)]:
            ctk.CTkCheckBox(inner, text=lbl, variable=var,
                            text_color=C["t1"], fg_color=C["blue"],
                            hover_color=C["blue_h"]).pack(anchor="w", pady=4)

        pw_var = tk.StringVar()
        pw_entry = ctk.CTkEntry(inner, textvariable=pw_var, width=370,
                                fg_color=C["card2"], border_color=C["bdr2"],
                                text_color=C["cyan"],
                                font=ctk.CTkFont(size=14, weight="bold"),
                                corner_radius=10)
        pw_entry.pack(pady=(14, 6))

        str_lbl = ctk.CTkLabel(inner, text="Strength: —",
                               font=ctk.CTkFont(size=11), text_color=C["t2"])
        str_lbl.pack(anchor="w")
        str_bar = ctk.CTkProgressBar(inner, width=370, progress_color=C["ok"])
        str_bar.set(0)
        str_bar.pack(pady=(2, 12))

        def _gen():
            pw = password_gen.generate_password(
                len_var.get(), use_upper.get(), use_digits.get(), use_sym.get())
            pw_var.set(pw)
            s  = password_gen.evaluate_strength(pw)
            cm = {"Strong": C["ok"], "Medium": C["warn"], "Weak": C["err"]}
            vm = {"Strong": 1.0,     "Medium": 0.5,       "Weak": 0.2}
            str_lbl.configure(text=f"Strength: {s}", text_color=cm.get(s, C["t2"]))
            str_bar.configure(progress_color=cm.get(s, C["ok"]))
            str_bar.set(vm.get(s, 0))

        def _copy():
            pw = pw_var.get()
            if pw:
                self.root.clipboard_clear(); self.root.clipboard_append(pw)
                messagebox.showinfo("Copied", "Password copied to clipboard.")

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x")
        _pill(btn_row, "🎲 Generate", C["blue"], C["blue_h"], _gen,
              w=160, h=36).pack(side="left")
        _pill(btn_row, "📋 Copy", C["peach"], C["peach_h"], _copy,
              w=130, h=36, fg="#1a0a00").pack(side="right")

        _gen()

    # ── Secure Sharing (ECDH) ──────────────────────────────────────────────────
    def _open_secure_sharing(self):
        SecureSharingDialog(self)

    # ── Admin Identity Helpers ─────────────────────────────────────────────────
    def _ensure_admin_identity(self, admin_number: int, password: str):
        ident_dir = Path("data/admin_identities") / f"admin{admin_number}"
        private_file = ident_dir / "identity_private.enc"
        public_file = ident_dir / "identity_public.json"
        if not (private_file.exists() and public_file.exists()):
            ident_dir.mkdir(parents=True, exist_ok=True)
            identity = identity_keys.create_identity(password, ident_dir)
            identity_keys.export_public_identity(identity, public_file)
            return identity
        return identity_keys.load_identity(password, ident_dir)

    def _get_admin_public_identity(self, admin_number: int):
        pub_file = Path("data/admin_identities") / f"admin{admin_number}" / "identity_public.json"
        if not pub_file.exists():
            raise FileNotFoundError(f"Admin {admin_number} public identity not found at {pub_file}.")
        return identity_keys.load_public_identity(pub_file)

    # ── File Encrypt ───────────────────────────────────────────────────────────
    def _encrypt_file(self):
        if self.admin_info["number"] != 1:
            messagebox.showwarning("Access Denied",
                                   "Only Admin 1 (Sender) can encrypt files.")
            return
        src = filedialog.askopenfilename(
            title="Select file to encrypt & share",
            filetypes=[("All files", "*.*")])
        if not src: return
        dst = filedialog.asksaveasfilename(
            title="Save encrypted .svf package",
            defaultextension=".svf",
            initialfile="encrypted_for_admin2.svf",
            filetypes=[("SecureVault File", "*.svf")])
        if not dst: return
        try:
            sender_id = self._ensure_admin_identity(1, self.admin_info["password"])
            recipient_pub = self._get_admin_public_identity(2)
            file_sharing.create_file_package(src, dst, sender_id, recipient_pub)

            orig_name = Path(src).name
            pkg_name = Path(dst).name
            db_manager.insert_file_history(
                sender_admin=1,
                recipient_admin=2,
                original_filename=orig_name,
                package_filename=pkg_name,
                operation="encrypt",
                status="success")
            messagebox.showinfo("Done",
                                f"File encrypted successfully!\nSaved to:\n{dst}\n\n"
                                "Transfer this .svf package to Admin 2.")
        except Exception as ex:
            messagebox.showerror("Encryption Error", str(ex))

    # ── File Decrypt ───────────────────────────────────────────────────────────
    def _decrypt_file(self):
        if self.admin_info["number"] != 2:
            messagebox.showwarning("Access Denied",
                                   "Only Admin 2 (Receiver) can decrypt files.")
            return
        src = filedialog.askopenfilename(
            title="Select .svf encrypted package",
            filetypes=[("SecureVault File", "*.svf"), ("All files", "*.*")])
        if not src: return
        dst = filedialog.asksaveasfilename(
            title="Save restored file",
            filetypes=[("All files", "*.*")])
        if not dst: return
        try:
            receiver_id = self._ensure_admin_identity(2, self.admin_info["password"])
            sender_pub = self._get_admin_public_identity(1)
            file_sharing.open_file_package(src, dst, receiver_id, sender_pub)

            orig_name = Path(dst).name
            pkg_name = Path(src).name
            db_manager.insert_file_history(
                sender_admin=1,
                recipient_admin=2,
                original_filename=orig_name,
                package_filename=pkg_name,
                operation="decrypt",
                status="success")
            messagebox.showinfo("Done",
                                f"File decrypted & signature verified successfully!\nRestored to:\n{dst}")
        except Exception as ex:
            messagebox.showerror("Decryption Error", str(ex))

    # ── File History ───────────────────────────────────────────────────────────
    def _show_history(self):
        dlg = ctk.CTkToplevel(self.root)
        dlg.title("SecureVault — File Sharing History")
        dlg.geometry("760x440")
        dlg.configure(fg_color=C["bg"])
        dlg.transient(self.root)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="🧾  File Sharing History",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=C["cyan"]).pack(pady=(20, 8))

        card = _card(dlg, corner_radius=14, border_color=C["bdr_b"])
        card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self._setup_treeview_style()
        cols = ("sender", "recipient", "original", "package", "op", "status", "date")
        htree = ttk.Treeview(card, columns=cols, show="headings", style="V.Treeview")
        for c, h, w in zip(cols,
                           ("Sender", "Recipient", "Original", "Package", "Op", "Status", "Date"),
                           (70, 80, 160, 160, 70, 70, 120)):
            htree.heading(c, text=h)
            htree.column(c, width=w, minwidth=40)

        for r in db_manager.get_file_history(self.admin_info["number"]):
            htree.insert("", "end", values=(
                f"Admin {r[0]}", f"Admin {r[1]}", r[2], r[3], r[4], r[5],
                r[6][:16] if r[6] else "—"))

        vsb = ttk.Scrollbar(card, orient="vertical", command=htree.yview)
        htree.configure(yscrollcommand=vsb.set)
        htree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
        vsb.pack(side="right", fill="y", pady=10, padx=(0,6))

    # ── Logout ─────────────────────────────────────────────────────────────────
    def _logout(self):
        self.master_password = None
        self.admin_info = None
        self._show_login()
