"""
gui.py – KeyShield / SecureVault GUI  v6.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Midnight Cyber / Futuristic Cybersecurity Edition
• 3-Pane Enterprise Layout (Navigation | Vault List | Inspector)
• Animated Midnight Cyber Network Mesh (Nodes, Cyan/Blue Connections, Pulses)
• Vault Health & Password Hygiene (Duplicate/Weak/Old analysis)
• Real-Time Security Audit Console (Monospace Live Cryptographic Feed)
• Inactivity Auto-Lock (10-minute countdown with session lock screen)
• Clipboard Auto-Clear with Live Countdown & Instant Wipe
• Drag-and-Drop / Quick File Encryption Dropzone (AES-256-GCM + Ed25519)
• One-Click Password Eye Toggle with 10s Auto-Remasking
"""

from __future__ import annotations

import hashlib
import math
import os
import random
import time
import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

import admin_auth
import auth
import db_manager
import encryption
import file_sharing
import identity_keys
import password_gen
from sharing_ui import SecureSharingDialog

# ═══════════════════════════  MIDNIGHT CYBER PALETTE  ══════════════════════════
C = {
    # backgrounds
    "bg":        "#071321",   # primary dark canvas (deep midnight navy)
    "bg2":       "#0D1528",   # secondary panels
    "card":      "#0F172A",   # glassmorphic card base
    "card2":     "#16223B",   # elevated card / inputs
    "card3":     "#1E2E4E",   # hover / active state
    "nav":       "#060A14",   # topbar & sidebar background
    # accents
    "blue":      "#2563EB",   # electric blue
    "blue_h":    "#1D4ED8",
    "blue_d":    "#172554",
    "cyan":      "#06B6D4",   # cyber cyan
    "cyan_h":    "#0891B2",
    "cyan_d":    "#083344",
    "cyan_glow": "#22D3EE",
    "purple":    "#8B5CF6",   # cyber purple
    "purple_h":  "#7C3AED",
    "purple_d":  "#3B0764",
    # semantics
    "ok":        "#10B981",   # emerald success
    "ok_h":      "#059669",
    "warn":      "#F59E0B",   # amber warning
    "warn_h":    "#D97706",
    "err":       "#EF4444",   # crimson alert
    "err_h":     "#DC2626",
    # typography
    "t1":        "#F8FAFC",   # primary text
    "t2":        "#94A3B8",   # secondary text
    "t3":        "#64748B",   # muted / timestamps
    # borders
    "bdr":       "#1E293B",   # subtle edge
    "bdr_b":     "#2563EB",   # blue focus
    "bdr_c":     "#06B6D4",   # cyan highlight
}


# ═══════════════════════════  ANIMATED BACKGROUND  ═════════════════════════════
class ParticleBG:
    """
    Midnight Cyber v2 — Dense Irregular Network Mesh (Image 2 Reference Match).

    Visual layers (bottom → top):
      L1  Deep midnight navy base fill (#071321)
      L2  Large atmospheric blue-teal radial glow orbs (slowly drifting)
      L3  Soft background micro-particles (blurred distant stars)
      L4  Dynamic network connections (varying cyan/teal by alpha)
      L5  Network nodes (small dim + medium + large bright glowing) + light pulses
    """

    # ── Tuning constants ───────────────────────────────────────────────────────
    N_NODES   = 60     # ~60 nodes → dense irregular triangular topology
    N_PULSES  = 10     # simultaneous light pulses
    N_MICRO   = 18     # background micro-particle stars
    N_ORBS    = 5      # atmospheric glow orbs
    SPEED     = 0.35   # max drift speed (px/frame)
    CONN_D    = 150    # connection distance threshold (px)
    CUR_D     = 190    # cursor attraction radius (px)
    FRAME_MS  = 34     # ~29 FPS

    # Node tier breakdown (by index)
    # 0 .. 41  → small dim   (42 nodes, 70%)
    # 42 .. 53 → medium      (12 nodes, 20%)
    # 54 .. 59 → large bright (6 nodes, 10%)
    _TIER_MED   = 42
    _TIER_LARGE = 54

    def __init__(self, canvas: tk.Canvas, w: int, h: int) -> None:
        self.cv   = canvas
        self.w    = max(w, 10)
        self.h    = max(h, 10)
        self.mx   = w // 2
        self.my   = h // 2
        self._alive  = True
        self._nodes  : list[dict] = []
        self._pulses : list[dict] = []
        self._orbs   : list[dict] = []
        self._micro  : list[dict] = []
        self._init_elements()
        self._animate()

    # ── Initialisation ──────────────────────────────────────────────────────────
    def _init_elements(self) -> None:
        w, h = self.w, self.h
        self._nodes = []

        for i in range(self.N_NODES):
            # Choose tier
            if i < self._TIER_MED:
                # Small dim — cluster-biased distribution (irregular)
                zone = random.choice(["left", "centre", "right", "top", "bottom"])
                if zone == "left":
                    x = random.uniform(0.03 * w, 0.38 * w)
                    y = random.uniform(0.05 * h, 0.95 * h)
                elif zone == "right":
                    x = random.uniform(0.62 * w, 0.97 * w)
                    y = random.uniform(0.05 * h, 0.95 * h)
                elif zone == "top":
                    x = random.uniform(0.05 * w, 0.95 * w)
                    y = random.uniform(0.04 * h, 0.35 * h)
                elif zone == "bottom":
                    x = random.uniform(0.05 * w, 0.95 * w)
                    y = random.uniform(0.65 * h, 0.96 * h)
                else:  # centre
                    x = random.uniform(0.3 * w, 0.7 * w)
                    y = random.uniform(0.2 * h, 0.8 * h)
                r     = random.uniform(1.8, 3.6)
                color = random.choice(["#1A6080", "#0E4D6B", "#0B3F5E", "#16587A"])
                glow  = False

            elif i < self._TIER_LARGE:
                # Medium — distributed more centrally
                x     = random.uniform(0.08 * w, 0.92 * w)
                y     = random.uniform(0.08 * h, 0.92 * h)
                r     = random.uniform(3.5, 5.5)
                color = C["cyan"]    # #06B6D4
                glow  = False

            else:
                # Large bright — prominent cyan anchor nodes
                x     = random.uniform(0.1 * w, 0.9 * w)
                y     = random.uniform(0.1 * h, 0.9 * h)
                r     = random.uniform(6.0, 9.5)
                color = C["cyan_glow"]  # #22D3EE
                glow  = True

            angle = random.uniform(0, 2 * math.pi)
            sp    = random.uniform(0.10, self.SPEED)
            self._nodes.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * sp,
                "vy": math.sin(angle) * sp,
                "r": r, "color": color, "glow": glow,
                "phase": random.uniform(0, math.pi * 2),  # for glow pulsing
            })

        # ── Atmospheric glow orbs (layered, asymmetrically placed) ─────────────
        # Each orb has concentric rings drawn outward → inward (additive glow feel)
        self._orbs = [
            # Central blue-teal dominant orb
            {"x": w * 0.50, "y": h * 0.48, "r": 280, "c": "#102D40",
             "vx": 0.04, "vy": 0.03},
            # Left mid teal orb
            {"x": w * 0.18, "y": h * 0.55, "r": 220, "c": "#0B3445",
             "vx": -0.05, "vy": 0.04},
            # Right lower orb
            {"x": w * 0.82, "y": h * 0.65, "r": 200, "c": "#0B3445",
             "vx": 0.03, "vy": -0.04},
            # Top right subtle orb
            {"x": w * 0.72, "y": h * 0.22, "r": 170, "c": "#091827",
             "vx": -0.04, "vy": 0.05},
            # Bottom left subtle orb
            {"x": w * 0.28, "y": h * 0.80, "r": 160, "c": "#091827",
             "vx": 0.05, "vy": -0.03},
        ]

        # ── Micro background particles (soft blurred stars) ─────────────────────
        self._micro = []
        for _ in range(self.N_MICRO):
            self._micro.append({
                "x": random.uniform(0, w),
                "y": random.uniform(0, h),
                "r": random.uniform(1.0, 2.5),
                "c": random.choice(["#1A4060", "#1B5A78", "#0D3550", "#22D3EE"]),
                "alpha_phase": random.uniform(0, math.pi * 2),
                "vx": random.uniform(-0.12, 0.12),
                "vy": random.uniform(-0.12, 0.12),
            })

        # ── Light pulses (spawn on valid connections) ───────────────────────────
        self._pulses = []
        for _ in range(self.N_PULSES):
            fi = random.randint(0, self.N_NODES - 1)
            ti = random.randint(0, self.N_NODES - 1)
            self._pulses.append({
                "from_idx": fi, "to_idx": ti,
                "t": random.random(),
                "speed": random.uniform(0.010, 0.030),
                "r": random.uniform(2.0, 3.5),
            })

        self._frame_count = 0

    # ── Resize / event callbacks ────────────────────────────────────────────────
    def resize(self, w: int, h: int) -> None:
        self.w = max(w, 10)
        self.h = max(h, 10)

    def on_motion(self, x: int, y: int) -> None:
        self.mx = x
        self.my = y

    def stop(self) -> None:
        self._alive = False

    # ── Animation loop ──────────────────────────────────────────────────────────
    def _animate(self) -> None:
        if not self._alive:
            return
        self._update()
        self._draw()
        try:
            self.cv.after(self.FRAME_MS, self._animate)
        except Exception:
            pass

    def _update(self) -> None:
        self._frame_count += 1
        mx, my = self.mx, self.my
        w, h   = self.w, self.h

        # ── Update nodes ────────────────────────────────────────────────────────
        for nd in self._nodes:
            dx = mx - nd["x"]
            dy = my - nd["y"]
            dist = math.hypot(dx, dy)
            if 0 < dist < self.CUR_D:
                force = (1.0 - dist / self.CUR_D) * 0.012
                nd["vx"] += (dx / dist) * force
                nd["vy"] += (dy / dist) * force

            v = math.hypot(nd["vx"], nd["vy"])
            if v > self.SPEED * 1.5:
                nd["vx"] = (nd["vx"] / v) * (self.SPEED * 1.5)
                nd["vy"] = (nd["vy"] / v) * (self.SPEED * 1.5)

            nd["x"] += nd["vx"]
            nd["y"] += nd["vy"]
            nd["phase"] += 0.04  # glow pulse advance

            # Edge bounce
            if nd["x"] < 8:        nd["x"] = 8;        nd["vx"] *= -1
            if nd["x"] > w - 8:    nd["x"] = w - 8;    nd["vx"] *= -1
            if nd["y"] < 8:        nd["y"] = 8;         nd["vy"] *= -1
            if nd["y"] > h - 8:    nd["y"] = h - 8;     nd["vy"] *= -1

        # ── Update atmospheric orbs (slow drift, wrap edges) ────────────────────
        for ob in self._orbs:
            ob["x"] += ob["vx"]
            ob["y"] += ob["vy"]
            if ob["x"] < -ob["r"]:      ob["x"] = w + ob["r"]
            if ob["x"] > w + ob["r"]:   ob["x"] = -ob["r"]
            if ob["y"] < -ob["r"]:      ob["y"] = h + ob["r"]
            if ob["y"] > h + ob["r"]:   ob["y"] = -ob["r"]

        # ── Update micro particles ───────────────────────────────────────────────
        for mp in self._micro:
            mp["x"] += mp["vx"]
            mp["y"] += mp["vy"]
            mp["alpha_phase"] += 0.025
            if mp["x"] < 0:  mp["x"] = w
            if mp["x"] > w:  mp["x"] = 0
            if mp["y"] < 0:  mp["y"] = h
            if mp["y"] > h:  mp["y"] = 0

        # ── Update pulses ────────────────────────────────────────────────────────
        for p in self._pulses:
            p["t"] += p["speed"]
            if p["t"] >= 1.0:
                p["t"] = 0.0
                # Find a valid connection to travel
                for _ in range(20):
                    fi = random.randint(0, self.N_NODES - 1)
                    ti = random.randint(0, self.N_NODES - 1)
                    if fi != ti:
                        a = self._nodes[fi]; b = self._nodes[ti]
                        if math.hypot(a["x"] - b["x"], a["y"] - b["y"]) < self.CONN_D:
                            p["from_idx"] = fi; p["to_idx"] = ti
                            break

    # ── Draw frame ──────────────────────────────────────────────────────────────
    def _draw(self) -> None:
        cv = self.cv
        try:
            cv.delete("p")
        except Exception:
            return

        w, h   = self.w, self.h
        mx, my = self.mx, self.my
        fc     = self._frame_count

        # ── L1: Deep midnight navy base ─────────────────────────────────────────
        cv.create_rectangle(0, 0, w + 2, h + 2, fill="#071321", outline="", tags="p")

        # ── L2: Atmospheric layered radial glow orbs ────────────────────────────
        # Each orb rendered as 4 concentric ovals: outer dim → inner bright
        for ob in self._orbs:
            ox, oy, br = ob["x"], ob["y"], ob["r"]
            layers = [
                (1.00, ob["c"],   ""),
                (0.60, "#133A52", ""),
                (0.30, "#1A5068", ""),
                (0.12, "#22D3EE", ""),
            ]
            for ratio, fc_col, _ in layers:
                r2 = br * ratio
                cv.create_oval(ox - r2, oy - r2, ox + r2, oy + r2,
                               fill=fc_col, outline="", tags="p")

        # ── L3: Micro background star-particles ─────────────────────────────────
        for mp in self._micro:
            # Simulate alpha fade via colour dimming (Tkinter has no native alpha)
            pulse = 0.45 + 0.35 * math.sin(mp["alpha_phase"])
            r2    = mp["r"] * (0.7 + 0.3 * pulse)
            cv.create_oval(mp["x"] - r2, mp["y"] - r2,
                           mp["x"] + r2, mp["y"] + r2,
                           fill=mp["c"], outline="", tags="p")

        # ── L4: Network connection lines ─────────────────────────────────────────
        nodes = self._nodes
        N     = self.N_NODES
        CD    = self.CONN_D
        for i in range(N):
            a = nodes[i]
            for j in range(i + 1, N):
                b    = nodes[j]
                dist = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
                if dist >= CD:
                    continue
                alpha = 1.0 - (dist / CD)

                # Near-cursor boost
                near = (math.hypot(a["x"] - mx, a["y"] - my) < self.CUR_D or
                        math.hypot(b["x"] - mx, b["y"] - my) < self.CUR_D)

                if near:
                    if alpha > 0.65:   col = "#22D3EE"  # bright cyan
                    elif alpha > 0.38: col = "#0B6080"  # medium teal
                    else:              col = "#0A3550"  # dark teal
                    lw = max(0.5, alpha * 2.0)
                else:
                    if alpha > 0.65:   col = "#0D5570"  # medium-bright cyan line
                    elif alpha > 0.38: col = "#0A3D58"  # medium teal line
                    else:              col = "#091E30"  # barely visible dark line
                    lw = max(0.4, alpha * 1.4)

                cv.create_line(a["x"], a["y"], b["x"], b["y"],
                               fill=col, width=lw, tags="p")

        # ── L5a: Light pulses along connections ──────────────────────────────────
        for p in self._pulses:
            a = nodes[p["from_idx"]]
            b = nodes[p["to_idx"]]
            if math.hypot(a["x"] - b["x"], a["y"] - b["y"]) < CD:
                t  = p["t"]
                px = a["x"] + (b["x"] - a["x"]) * t
                py = a["y"] + (b["y"] - a["y"]) * t
                pr = p["r"]
                # Outer glow halo
                cv.create_oval(px - pr - 2, py - pr - 2, px + pr + 2, py + pr + 2,
                               fill="#0E5F7A", outline="", tags="p")
                # Bright core
                cv.create_oval(px - pr, py - pr, px + pr, py + pr,
                               fill="#22D3EE", outline="", tags="p")

        # ── L5b: Network nodes ───────────────────────────────────────────────────
        for nd in nodes:
            nx, ny, r  = nd["x"], nd["y"], nd["r"]
            d_cur      = math.hypot(nx - mx, ny - my)
            near       = d_cur < self.CUR_D
            pulse_sin  = 0.85 + 0.15 * math.sin(nd["phase"])

            if nd["glow"]:
                # Large bright node: outer glow ring + pulsing core
                rr = r * pulse_sin * (1.4 if near else 1.0)
                # Glow halo (3 concentric rings)
                cv.create_oval(nx - rr - 7, ny - rr - 7, nx + rr + 7, ny + rr + 7,
                               fill="#082030", outline="", tags="p")
                cv.create_oval(nx - rr - 3, ny - rr - 3, nx + rr + 3, ny + rr + 3,
                               fill="#0D4F6A", outline="", tags="p")
                cv.create_oval(nx - rr, ny - rr, nx + rr, ny + rr,
                               fill="#22D3EE", outline="", tags="p")
                # Bright centre dot
                cv.create_oval(nx - rr * 0.4, ny - rr * 0.4,
                               nx + rr * 0.4, ny + rr * 0.4,
                               fill="#A8F0FF", outline="", tags="p")

            elif nd["color"] == C["cyan"]:
                # Medium node
                rr = r * (1.3 if near else 1.0)
                cv.create_oval(nx - rr - 2, ny - rr - 2, nx + rr + 2, ny + rr + 2,
                               fill="#0A3B54", outline="", tags="p")
                cv.create_oval(nx - rr, ny - rr, nx + rr, ny + rr,
                               fill="#06B6D4", outline="", tags="p")

            else:
                # Small dim node
                rr = r * (1.5 if near else 1.0)
                cv.create_oval(nx - rr, ny - rr, nx + rr, ny + rr,
                               fill=nd["color"], outline="", tags="p")

            # Near-cursor: glow ring + cursor line
            if near:
                cv.create_oval(nx - rr - 6, ny - rr - 6, nx + rr + 6, ny + rr + 6,
                               outline="#06B6D4", width=1, tags="p")
                cv.create_line(nx, ny, mx, my, fill="#0891B2",
                               width=max(0.3, (1.0 - d_cur / self.CUR_D) * 1.2),
                               tags="p")

        # ── Subtle cursor crosshair dot ───────────────────────────────────────────
        cv.create_oval(mx - 3, my - 3, mx + 3, my + 3,
                       fill="#22D3EE", outline="#06B6D4", width=1, tags="p")


# ═══════════════════════════  UI FACTORY HELPERS  ═════════════════════════════
def _btn_gradient(parent, text: str, cmd, w: int = 160, h: int = 38,
                  fg: str = C["blue"], hover: str = C["blue_h"],
                  text_color: str = C["t1"], icon: str = "") -> ctk.CTkButton:
    full_text = f"{icon}  {text}".strip() if icon else text
    return ctk.CTkButton(
        parent, text=full_text, command=cmd,
        width=w, height=h, corner_radius=10,
        fg_color=fg, hover_color=hover,
        text_color=text_color,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    )


def _card(parent, **kw) -> ctk.CTkFrame:
    defaults = dict(fg_color=C["card"], corner_radius=14,
                    border_width=1, border_color=C["bdr"])
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


# ═══════════════════════════  MAIN APPLICATION  ═══════════════════════════════
class PasswordManagerApp:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title("KeyShield — Midnight Cyber CNS Platform")
        self.root.geometry("1240x790")
        self.root.minsize(1080, 680)
        self.root.configure(fg_color=C["bg"])

        # Cryptographic session state
        self.master_password: str | None = None
        self.admin_info: dict | None = None

        # Feature states
        self._active_tab = "vault"         # "vault", "health", "transfer", "console", "history"
        self._selected_cred: tuple | None = None
        self._all_cached_creds: list[tuple] = []
        self._filter_tag: str | None = None

        # Clipboard auto-clear state
        self._clipboard_expiry: float = 0.0
        self._clipboard_job = None

        # Inactivity auto-lock (10 minutes = 600s)
        self.INACTIVITY_TIMEOUT = 600
        self._last_activity = time.time()
        self._is_locked = False

        # Real-time Security Console Audit entries
        self._console_logs: list[tuple[str, str, str]] = []  # (time, tag, msg)
        self._log_security_event("SYSTEM", "KeyShield platform initialized. Cryptographic engine ready.")

        # Root container
        self.container = ctk.CTkFrame(self.root, fg_color=C["bg"], corner_radius=0)
        self.container.pack(fill="both", expand=True)

        # Background particle network
        self._pcanvas: tk.Canvas | None = None
        self._particles: ParticleBG | None = None
        self._init_particles()

        # Global event listeners
        self.root.bind("<Motion>", self._on_user_interaction)
        self.root.bind("<Key>", self._on_user_interaction)
        self.root.bind("<Configure>", self._on_resize)

        # Start periodic background monitor
        self._start_session_timers()

        # Launch initial screen
        self._show_login()

    # ── Background Particles ──────────────────────────────────────────────────
    def _init_particles(self) -> None:
        if self._particles:
            self._particles.stop()
        if self._pcanvas:
            try: self._pcanvas.destroy()
            except Exception: pass
        w = max(self.root.winfo_width(), 1240)
        h = max(self.root.winfo_height(), 790)
        cv = tk.Canvas(self.container, bg=C["bg"], highlightthickness=0,
                       bd=0, relief="flat")
        cv.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Misc.lower(cv)
        self._pcanvas = cv
        self._particles = ParticleBG(cv, w, h)

    def _on_resize(self, e: tk.Event) -> None:
        if e.widget is self.root and self._particles:
            self._particles.resize(e.width, e.height)

    def _clear_container(self) -> None:
        for w in list(self.container.winfo_children()):
            try: w.destroy()
            except Exception: pass
        self._pcanvas = None
        self._particles = None
        self._init_particles()

    # ── Activity & Session Security Timers ────────────────────────────────────
    def _on_user_interaction(self, e: tk.Event = None) -> None:
        if not self._is_locked:
            self._last_activity = time.time()
        if self._particles and hasattr(e, "x_root"):
            try:
                cx = e.x_root - self.container.winfo_rootx()
                cy = e.y_root - self.container.winfo_rooty()
                self._particles.on_motion(cx, cy)
            except Exception: pass

    def _start_session_timers(self) -> None:
        self._tick_timers()

    def _tick_timers(self) -> None:
        now = time.time()
        # 1. Inactivity monitor
        if self.master_password and not self._is_locked:
            elapsed = now - self._last_activity
            remaining = max(0, int(self.INACTIVITY_TIMEOUT - elapsed))
            if hasattr(self, "_lbl_autolock"):
                mins, secs = divmod(remaining, 60)
                self._lbl_autolock.configure(text=f"⏱ {mins:02d}:{secs:02d}")
            if elapsed >= self.INACTIVITY_TIMEOUT:
                self._lock_session()

        # 2. Clipboard auto-clear monitor
        if self._clipboard_expiry > 0:
            clip_rem = max(0, int(self._clipboard_expiry - now))
            if hasattr(self, "_lbl_clip"):
                if clip_rem > 0:
                    self._lbl_clip.configure(text=f"📋 Wipe: {clip_rem}s")
                    self._btn_wipe_now.pack(side="left", padx=4)
                else:
                    self._wipe_clipboard()
        self.root.after(1000, self._tick_timers)

    def _copy_with_autoclear(self, text: str, label_name: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._clipboard_expiry = time.time() + 30.0
        self._log_security_event("CLIP", f"Copied {label_name} to clipboard. Auto-clear armed (30s).")
        if hasattr(self, "_lbl_clip"):
            self._lbl_clip.configure(text="📋 Wipe: 30s")
            self._btn_wipe_now.pack(side="left", padx=4)
        messagebox.showinfo("Copied", f"{label_name} copied to clipboard.\nWill auto-wipe in 30 seconds.")

    def _wipe_clipboard(self) -> None:
        self.root.clipboard_clear()
        self._clipboard_expiry = 0.0
        self._log_security_event("CLIP", "Clipboard memory wiped cleanly.")
        if hasattr(self, "_lbl_clip"):
            self._lbl_clip.configure(text="")
            self._btn_wipe_now.pack_forget()

    def _lock_session(self) -> None:
        if self._is_locked or not self.master_password:
            return
        self._is_locked = True
        self._log_security_event("LOCK", "Inactivity timeout reached (10 min). Vault locked.")
        self._show_lock_overlay()

    def _show_lock_overlay(self) -> None:
        self._clear_container()
        wrap = ctk.CTkFrame(self.container, fg_color="transparent")
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        card = _card(wrap, corner_radius=22, border_color=C["cyan"])
        card.pack(padx=20, pady=20)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=45, pady=40)

        ctk.CTkLabel(inner, text="🔒  SESSION LOCKED",
                     font=ctk.CTkFont(family="Space Grotesk", size=24, weight="bold"),
                     text_color=C["cyan"]).pack()
        ctk.CTkLabel(inner, text="Vault locked due to 10 minutes of inactivity.\nEnter master password to resume.",
                     font=ctk.CTkFont(size=12), text_color=C["t2"]).pack(pady=(4, 20))

        pw_e = ctk.CTkEntry(inner, width=320, height=42, show="●",
                            placeholder_text="Vault Master Password",
                            fg_color=C["card2"], border_color=C["bdr"],
                            text_color=C["t1"], corner_radius=10)
        pw_e.pack(pady=(0, 12))
        pw_e.focus()

        err_lbl = ctk.CTkLabel(inner, text="", text_color=C["err"], font=ctk.CTkFont(size=11))
        err_lbl.pack()

        def _do_unlock(_e=None):
            if auth.verify_master_password(pw_e.get()):
                self._is_locked = False
                self._last_activity = time.time()
                self._log_security_event("AUTH", f"Session resumed by Admin {self.admin_info['number']}.")
                self._show_dashboard()
            else:
                err_lbl.configure(text="Incorrect vault master password.")

        pw_e.bind("<Return>", _do_unlock)
        _btn_gradient(inner, "Unlock Vault", _do_unlock, w=320, h=44,
                      fg=C["blue"], hover=C["blue_h"]).pack(pady=(12, 0))

    def _log_security_event(self, tag: str, message: str) -> None:
        t_str = datetime.now().strftime("%H:%M:%S")
        self._console_logs.append((t_str, tag, message))
        if hasattr(self, "_refresh_console_view"):
            self._refresh_console_view()

    # ══════════════════════════════════════════════════════════════════════════
    #                           LOGIN SCREENS
    # ══════════════════════════════════════════════════════════════════════════
    def _show_login(self) -> None:
        self._clear_container()
        self.root.title("KeyShield — Midnight Cyber Login")

        is_first = auth.is_first_run()
        needs_admin = admin_auth.count_accounts() == 0

        wrap = ctk.CTkFrame(self.container, fg_color="transparent")
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        # Top cryptographic badges
        b_row = ctk.CTkFrame(wrap, fg_color="transparent")
        b_row.pack(pady=(0, 14))
        for tag, color in [("AES-256-GCM", C["cyan"]), ("ECDH SECP256R1", C["blue"]),
                           ("Ed25519", C["purple"]), ("PBKDF2-310K", C["ok"])]:
            ctk.CTkLabel(b_row, text=tag,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=color, fg_color=C["card2"], corner_radius=6,
                         padx=8, pady=3).pack(side="left", padx=4)

        card = _card(wrap, corner_radius=22, border_color=C["bdr_c"])
        card.pack()
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=45, pady=38)

        # Title
        ctk.CTkLabel(inner, text="🛡️  KeyShield",
                     font=ctk.CTkFont(family="Space Grotesk", size=32, weight="bold"),
                     text_color=C["cyan_glow"]).pack()
        ctk.CTkLabel(inner, text="Enterprise Vault & Authenticated Cryptosystem",
                     font=ctk.CTkFont(size=12), text_color=C["t2"]).pack(pady=(4, 24))

        if needs_admin:
            self._build_admin_setup(inner, is_first)
        elif is_first:
            self._build_vault_setup(inner)
        else:
            self._build_login_form(inner)

    def _build_admin_setup(self, parent, is_first_vault: bool) -> None:
        ctk.CTkLabel(parent, text="FIRST RUN – Setup Administrator Accounts",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["cyan"]).pack(pady=(0, 16))

        fields = {}
        for lbl, key, show in [
            ("Admin 1 Name",     "a1n", ""),
            ("Admin 1 Password", "a1p", "●"),
            ("Admin 2 Name",     "a2n", ""),
            ("Admin 2 Password", "a2p", "●"),
        ]:
            ctk.CTkLabel(parent, text=lbl, font=ctk.CTkFont(size=11),
                         text_color=C["t2"], anchor="w").pack(fill="x")
            e = ctk.CTkEntry(parent, width=330, fg_color=C["card2"],
                             border_color=C["bdr"], text_color=C["t1"],
                             show=show, corner_radius=10)
            e.pack(pady=(0, 10))
            fields[key] = e

        err_lbl = ctk.CTkLabel(parent, text="", text_color=C["err"], font=ctk.CTkFont(size=11), wraplength=310)
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
                self._log_security_event("AUTH", "Administrator accounts & identity keys generated successfully.")
            except ValueError as ex:
                err_lbl.configure(text=str(ex)); return
            self._show_login()

        _btn_gradient(parent, "Initialize Accounts", _do, w=330, h=44, fg=C["blue"], hover=C["blue_h"]).pack(pady=(12, 0))

    def _build_vault_setup(self, parent) -> None:
        ctk.CTkLabel(parent, text="Setup Vault Master Password",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["cyan"]).pack(pady=(0, 14))

        pw1 = ctk.CTkEntry(parent, width=330, placeholder_text="Choose Master Password",
                           fg_color=C["card2"], border_color=C["bdr"],
                           text_color=C["t1"], show="●", corner_radius=10)
        pw1.pack(pady=(0, 10))
        pw2 = ctk.CTkEntry(parent, width=330, placeholder_text="Confirm Master Password",
                           fg_color=C["card2"], border_color=C["bdr"],
                           text_color=C["t1"], show="●", corner_radius=10)
        pw2.pack(pady=(0, 10))

        err_lbl = ctk.CTkLabel(parent, text="", text_color=C["err"], font=ctk.CTkFont(size=11), wraplength=310)
        err_lbl.pack()

        def _do():
            if pw1.get() != pw2.get():
                err_lbl.configure(text="Passwords do not match."); return
            ok, msg = auth.setup_master_password(pw1.get())
            if not ok:
                err_lbl.configure(text=msg); return
            self._log_security_event("AUTH", "Vault master password initialized with PBKDF2 salt.")
            self._show_login()

        _btn_gradient(parent, "Set Master Password", _do, w=330, h=44, fg=C["blue"], hover=C["blue_h"]).pack(pady=(12, 0))

    def _build_login_form(self, parent) -> None:
        admin_var = tk.IntVar(value=1)
        rrow = ctk.CTkFrame(parent, fg_color="transparent")
        rrow.pack(pady=(0, 18))
        for n, label in ((1, "Admin 1 (Sender)"), (2, "Admin 2 (Receiver)")):
            ctk.CTkRadioButton(rrow, text=label, variable=admin_var, value=n,
                               text_color=C["t1"], fg_color=C["cyan"],
                               hover_color=C["cyan_h"]).pack(side="left", padx=14)

        adm_pw = ctk.CTkEntry(parent, width=340, height=42,
                              placeholder_text="Administrator Password",
                              fg_color=C["card2"], border_color=C["bdr"],
                              text_color=C["t1"], show="●", corner_radius=10)
        adm_pw.pack(pady=(0, 12))

        vlt_pw = ctk.CTkEntry(parent, width=340, height=42,
                              placeholder_text="Vault Master Password",
                              fg_color=C["card2"], border_color=C["bdr"],
                              text_color=C["t1"], show="●", corner_radius=10)
        vlt_pw.pack(pady=(0, 12))

        err_lbl = ctk.CTkLabel(parent, text="", text_color=C["err"], font=ctk.CTkFont(size=11), wraplength=320)
        err_lbl.pack()

        def _do_login(_e=None):
            info = admin_auth.authenticate(admin_var.get(), adm_pw.get())
            if info is None:
                err_lbl.configure(text="Invalid administrator credentials.")
                self._log_security_event("ALERT", f"Failed authentication attempt for Admin {admin_var.get()}.")
                return
            if not auth.verify_master_password(vlt_pw.get()):
                err_lbl.configure(text="Invalid vault master password.")
                self._log_security_event("ALERT", "Failed vault master password verification.")
                return

            self.admin_info = info
            self.master_password = vlt_pw.get()
            self._last_activity = time.time()
            self._is_locked = False
            self._log_security_event("AUTH", f"Admin {info['number']} ({info['name']}) unlocked dashboard.")
            self._log_security_event("CRYPTO", "Vault master key derived (PBKDF2-HMAC-SHA256, 200,000 iterations).")
            self._show_dashboard()

        adm_pw.bind("<Return>", _do_login)
        vlt_pw.bind("<Return>", _do_login)

        _btn_gradient(parent, "Unlock Cyber Dashboard", _do_login, w=340, h=46,
                      fg=C["blue"], hover=C["blue_h"], icon="⚡").pack(pady=(16, 0))

    # ══════════════════════════════════════════════════════════════════════════
    #                         DASHBOARD & 3-PANE LAYOUT
    # ══════════════════════════════════════════════════════════════════════════
    def _show_dashboard(self) -> None:
        self._clear_container()
        name = self.admin_info["name"]
        no = self.admin_info["number"]
        self.root.title(f"KeyShield — Admin {no} ({name}) — Midnight Cyber")

        # ── TOPBAR ────────────────────────────────────────────────────────────
        topbar = ctk.CTkFrame(self.container, fg_color=C["nav"], corner_radius=0, height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        # Brand on left
        ctk.CTkLabel(topbar, text="🛡️  KeyShield",
                     font=ctk.CTkFont(family="Space Grotesk", size=17, weight="bold"),
                     text_color=C["cyan_glow"]).pack(side="left", padx=(20, 6))
        ctk.CTkLabel(topbar, text="│ Midnight Cyber",
                     font=ctk.CTkFont(size=11), text_color=C["t3"]).pack(side="left", padx=(0, 14))

        # Status badge
        ctk.CTkLabel(topbar, text="● AES-256 ENCRYPTED",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C["ok"], fg_color=C["card2"],
                     corner_radius=8, padx=10, pady=3).pack(side="left", padx=4)

        # Inactivity countdown pill
        self._lbl_autolock = ctk.CTkLabel(
            topbar, text="⏱ 10:00",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C["cyan"], fg_color=C["cyan_d"],
            corner_radius=8, padx=10, pady=4
        )
        self._lbl_autolock.pack(side="left", padx=10)

        # Clipboard auto-clear pill & wipe button
        self._lbl_clip = ctk.CTkLabel(topbar, text="",
                                      font=ctk.CTkFont(size=11, weight="bold"),
                                      text_color=C["warn"], fg_color=C["card2"],
                                      corner_radius=8, padx=8, pady=3)
        self._lbl_clip.pack(side="left", padx=4)

        self._btn_wipe_now = ctk.CTkButton(
            topbar, text="Wipe", width=46, height=26, corner_radius=6,
            fg_color=C["warn"], hover_color=C["warn_h"], text_color="#1a0a00",
            font=ctk.CTkFont(size=10, weight="bold"),
            command=self._wipe_clipboard
        )

        # Right side: Admin profile & Lock / Logout
        _btn_gradient(topbar, "Logout", self._logout, w=84, h=32,
                      fg=C["err"], hover=C["err_h"], icon="⏻").pack(side="right", padx=(6, 18), pady=10)

        _btn_gradient(topbar, "Lock", self._lock_session, w=76, h=32,
                      fg=C["card2"], hover=C["card3"], icon="🔒").pack(side="right", padx=6, pady=10)

        # Profile avatar
        prof_card = ctk.CTkFrame(topbar, fg_color=C["card2"], corner_radius=10)
        prof_card.pack(side="right", padx=10, pady=8)
        initials = name[:2].upper()
        ctk.CTkLabel(prof_card, text=f" {initials} ",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["cyan_glow"], fg_color=C["blue_d"],
                     corner_radius=6, padx=4, pady=2).pack(side="left", padx=6, pady=4)
        ctk.CTkLabel(prof_card, text=f"Admin {no}  {name} ",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["t1"]).pack(side="left", padx=(0, 8), pady=4)

        # ── MAIN BODY (3-Pane or Content Area) ────────────────────────────────
        body = ctk.CTkFrame(self.container, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # 1. LEFT NAVIGATION SIDEBAR (~200px)
        self._build_left_sidebar(body)

        # 2. CONTENT CONTAINER (Switched by active tab)
        self.content_area = ctk.CTkFrame(body, fg_color="transparent")
        self.content_area.pack(side="left", fill="both", expand=True, padx=(10, 16), pady=12)

        # Render active tab
        self._switch_tab(self._active_tab)

    # ── Left Navigation Sidebar ───────────────────────────────────────────────
    def _build_left_sidebar(self, parent) -> None:
        sidebar = _card(parent, width=205, corner_radius=0, fg_color=C["nav"])
        sidebar.pack(side="left", fill="y", padx=(0, 0))
        sidebar.pack_propagate(False)

        inner = ctk.CTkFrame(sidebar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=14)

        ctk.CTkLabel(inner, text="VAULT MANAGEMENT",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C["t3"]).pack(anchor="w", pady=(4, 6))

        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        def _add_nav(tab_key: str, label: str, icon: str):
            btn = ctk.CTkButton(
                inner, text=f"{icon}  {label}",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w", height=38, corner_radius=10,
                fg_color=C["blue_d"] if self._active_tab == tab_key else "transparent",
                hover_color=C["card2"],
                text_color=C["cyan_glow"] if self._active_tab == tab_key else C["t2"],
                command=lambda k=tab_key: self._switch_tab(k)
            )
            btn.pack(fill="x", pady=2)
            self._nav_buttons[tab_key] = btn

        _add_nav("vault",    "All Passwords",   "🔐")
        _add_nav("health",   "Vault Health",    "🛡️")
        _add_nav("transfer", "File Transfer",   "📤")
        _add_nav("console",  "Security Console","📜")

        # Divider
        ctk.CTkFrame(inner, height=1, fg_color=C["bdr"]).pack(fill="x", pady=12)

        ctk.CTkLabel(inner, text="TOOLS & AUDIT",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C["t3"]).pack(anchor="w", pady=(0, 6))

        _add_nav("generator", "Generator",      "🎲")
        _add_nav("identities","ECDH Identity",  "🔑")
        _add_nav("history",   "Audit History",  "🧾")

        # Quick Add Button at bottom of sidebar
        ctk.CTkFrame(inner, fg_color="transparent").pack(fill="both", expand=True)
        _btn_gradient(inner, "New Password", self._open_add_dialog,
                      w=180, h=40, fg=C["blue"], hover=C["blue_h"], icon="➕").pack(side="bottom", pady=4)

    def _switch_tab(self, tab_key: str) -> None:
        self._active_tab = tab_key
        # Update sidebar button states
        for k, btn in self._nav_buttons.items():
            if k == tab_key:
                btn.configure(fg_color=C["blue_d"], text_color=C["cyan_glow"])
            else:
                btn.configure(fg_color="transparent", text_color=C["t2"])

        # Clear content area
        for w in list(self.content_area.winfo_children()):
            try: w.destroy()
            except Exception: pass

        if tab_key == "vault":
            self._render_vault_3pane()
        elif tab_key == "health":
            self._render_health_tab()
        elif tab_key == "transfer":
            self._render_transfer_tab()
        elif tab_key == "console":
            self._render_console_tab()
        elif tab_key == "generator":
            self._render_generator_tab()
        elif tab_key == "identities":
            self._render_identities_tab()
        elif tab_key == "history":
            self._render_history_tab()

    # ══════════════════════════════════════════════════════════════════════════
    #                   TAB 1: VAULT LIST & INSPECTOR (3-PANE)
    # ══════════════════════════════════════════════════════════════════════════
    def _render_vault_3pane(self) -> None:
        pane = self.content_area

        # Middle Pane: List & Search (~380px)
        mid_pane = _card(pane, width=380, corner_radius=14)
        mid_pane.pack(side="left", fill="y", padx=(0, 10))
        mid_pane.pack_propagate(False)

        # Right Pane: Credential Detail Inspector (Expands)
        self.inspector_pane = _card(pane, corner_radius=14)
        self.inspector_pane.pack(side="left", fill="both", expand=True)

        # ── Middle Pane Content ───────────────────────────────────────────────
        mid_top = ctk.CTkFrame(mid_pane, fg_color="transparent")
        mid_top.pack(fill="x", padx=14, pady=(14, 6))

        # Search Bar
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh_item_tiles())

        srch_frame = ctk.CTkFrame(mid_top, fg_color=C["card2"], corner_radius=10,
                                  border_width=1, border_color=C["bdr"])
        srch_frame.pack(fill="x", pady=(0, 8))
        ctk.CTkEntry(srch_frame, textvariable=self._search_var,
                     placeholder_text="🔍  Search accounts or usernames…",
                     fg_color="transparent", border_width=0,
                     text_color=C["t1"], font=ctk.CTkFont(size=12)).pack(fill="x", padx=10, pady=7)

        # Filter Pills Row
        pill_row = ctk.CTkFrame(mid_top, fg_color="transparent")
        pill_row.pack(fill="x")
        self._btn_all = ctk.CTkButton(
            pill_row, text="All", width=50, height=24, corner_radius=6,
            fg_color=C["blue"] if not self._filter_tag else C["card2"],
            text_color=C["t1"], font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._set_filter(None)
        )
        self._btn_all.pack(side="left", padx=(0, 4))

        self._btn_fav = ctk.CTkButton(
            pill_row, text="⭐ Starred", width=75, height=24, corner_radius=6,
            fg_color=C["blue"] if self._filter_tag == "fav" else C["card2"],
            text_color=C["t1"], font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._set_filter("fav")
        )
        self._btn_fav.pack(side="left", padx=4)

        self._btn_weak = ctk.CTkButton(
            pill_row, text="⚠ Weak", width=65, height=24, corner_radius=6,
            fg_color=C["err"] if self._filter_tag == "weak" else C["card2"],
            text_color=C["t1"], font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._set_filter("weak")
        )
        self._btn_weak.pack(side="left", padx=4)

        # Scrollable Tile Container
        self._tiles_container = ctk.CTkScrollableFrame(mid_pane, fg_color="transparent")
        self._tiles_container.pack(fill="both", expand=True, padx=8, pady=(6, 10))

        # Initial render of middle list
        self._refresh_item_tiles()

        # Initial render of Inspector
        self._render_inspector_card(self._selected_cred)

    def _set_filter(self, tag: str | None) -> None:
        self._filter_tag = tag
        self._refresh_item_tiles()

    def _refresh_item_tiles(self) -> None:
        for w in list(self._tiles_container.winfo_children()):
            try: w.destroy()
            except Exception: pass

        q = self._search_var.get().strip() if hasattr(self, "_search_var") else ""
        raw_rows = db_manager.search_credentials(q) if q else db_manager.get_all_credentials()
        self._all_cached_creds = raw_rows

        displayed = 0
        for row in raw_rows:
            cid, site, user, enc_pass, notes, created, upd = row

            # Evaluate strength & tags
            is_fav = notes and "[FAV]" in notes
            try:
                plain = encryption.decrypt_password(enc_pass, self.master_password)
                strength = password_gen.evaluate_strength(plain)
            except Exception:
                strength = "Unknown"

            # Apply tag filter
            if self._filter_tag == "fav" and not is_fav:
                continue
            if self._filter_tag == "weak" and strength == "Strong":
                continue

            displayed += 1
            is_selected = self._selected_cred and self._selected_cred[0] == cid

            tile = ctk.CTkFrame(
                self._tiles_container,
                fg_color=C["card3"] if is_selected else C["card2"],
                border_width=1,
                border_color=C["cyan"] if is_selected else C["bdr"],
                corner_radius=10, height=58
            )
            tile.pack(fill="x", pady=4, padx=2)
            tile.pack_propagate(False)

            # Circular Monogram
            initial = site[:1].upper() if site else "K"
            circle_col = C["blue"] if hash(site) % 2 == 0 else C["purple"]
            mono = ctk.CTkLabel(tile, text=f" {initial} ", width=36, height=36,
                                fg_color=circle_col, text_color="#fff",
                                font=ctk.CTkFont(size=14, weight="bold"),
                                corner_radius=18)
            mono.pack(side="left", padx=10, pady=10)

            # Labels container
            txt_box = ctk.CTkFrame(tile, fg_color="transparent")
            txt_box.pack(side="left", fill="both", expand=True, pady=8)

            title_row = ctk.CTkFrame(txt_box, fg_color="transparent")
            title_row.pack(fill="x")
            ctk.CTkLabel(title_row, text=site,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=C["t1"], anchor="w").pack(side="left")
            if is_fav:
                ctk.CTkLabel(title_row, text="★", text_color=C["warn"],
                             font=ctk.CTkFont(size=12)).pack(side="left", padx=4)

            ctk.CTkLabel(txt_box, text=user, font=ctk.CTkFont(size=11),
                         text_color=C["t3"], anchor="w").pack(fill="x")

            # Strength indicator badge on right
            str_col = C["ok"] if strength == "Strong" else (C["warn"] if strength == "Medium" else C["err"])
            ctk.CTkLabel(tile, text="●", text_color=str_col,
                         font=ctk.CTkFont(size=14)).pack(side="right", padx=12)

            # Bind selection click to tile and all children
            def _select_row(_e=None, r=row):
                self._selected_cred = r
                self._refresh_item_tiles()
                self._render_inspector_card(r)

            for w in [tile, mono, txt_box, title_row]:
                w.bind("<Button-1>", _select_row)

        if displayed == 0:
            ctk.CTkLabel(self._tiles_container, text="No credentials match criteria.",
                         text_color=C["t3"], font=ctk.CTkFont(size=12)).pack(pady=30)

    # ── Detail Inspector Pane (Right Column) ──────────────────────────────────
    def _render_inspector_card(self, cred: tuple | None) -> None:
        for w in list(self.inspector_pane.winfo_children()):
            try: w.destroy()
            except Exception: pass

        if cred is None:
            # Empty state card
            empty = ctk.CTkFrame(self.inspector_pane, fg_color="transparent")
            empty.place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(empty, text="🔐", font=ctk.CTkFont(size=48)).pack(pady=(0, 10))
            ctk.CTkLabel(empty, text="Select an account to view credentials",
                         font=ctk.CTkFont(size=16, weight="bold"), text_color=C["t1"]).pack()
            ctk.CTkLabel(empty, text="All credentials encrypted at rest with AES-128-CBC and PBKDF2.",
                         font=ctk.CTkFont(size=11), text_color=C["t3"]).pack(pady=4)
            return

        cid, site, user, enc_pass, notes, created, upd = cred
        is_fav = notes and "[FAV]" in notes
        clean_notes = notes.replace("[FAV]", "").strip() if notes else ""

        try:
            plain_pass = encryption.decrypt_password(enc_pass, self.master_password)
            strength = password_gen.evaluate_strength(plain_pass)
        except Exception:
            plain_pass = ""
            strength = "Error"

        # Content wrapper
        wrap = ctk.CTkScrollableFrame(self.inspector_pane, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=24, pady=20)

        # Top Header (Monogram + Title + Actions)
        top = ctk.CTkFrame(wrap, fg_color="transparent")
        top.pack(fill="x", pady=(0, 18))

        mono = ctk.CTkLabel(top, text=f" {site[:1].upper()} ", width=46, height=46,
                            fg_color=C["blue"], text_color="#fff",
                            font=ctk.CTkFont(size=18, weight="bold"), corner_radius=23)
        mono.pack(side="left", padx=(0, 14))

        info_b = ctk.CTkFrame(top, fg_color="transparent")
        info_b.pack(side="left")
        ctk.CTkLabel(info_b, text=site, font=ctk.CTkFont(family="Space Grotesk", size=22, weight="bold"),
                     text_color=C["t1"]).pack(anchor="w")
        ctk.CTkLabel(info_b, text=f"Created on {created[:10] if created else '—'} • ID #{cid}",
                     font=ctk.CTkFont(size=11), text_color=C["t3"]).pack(anchor="w")

        # Favorite star toggle button
        def _toggle_fav():
            new_notes = clean_notes if is_fav else f"[FAV] {clean_notes}".strip()
            db_manager.update_credential(cid, site, user, enc_pass, new_notes)
            self._selected_cred = (cid, site, user, enc_pass, new_notes, created, upd)
            self._refresh_item_tiles()
            self._render_inspector_card(self._selected_cred)

        _btn_gradient(top, "★ Favorite" if is_fav else "☆ Star", _toggle_fav,
                      w=90, h=32, fg=C["card2"], hover=C["card3"],
                      text_color=C["warn"] if is_fav else C["t2"]).pack(side="right", padx=4)

        # ── Credentials Section ───────────────────────────────────────────────
        ctk.CTkLabel(wrap, text="ACCOUNT CREDENTIALS", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["cyan"]).pack(anchor="w", pady=(10, 6))

        # Username Card
        u_card = _card(wrap, fg_color=C["card2"])
        u_card.pack(fill="x", pady=4)
        u_inner = ctk.CTkFrame(u_card, fg_color="transparent")
        u_inner.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(u_inner, text="USERNAME / EMAIL", font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=C["t3"]).pack(anchor="w")
        ctk.CTkLabel(u_inner, text=user, font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C["t1"]).pack(side="left")
        _btn_gradient(u_inner, "Copy", lambda: self._copy_with_autoclear(user, "Username"),
                      w=64, h=28, fg=C["card3"], hover=C["blue"], icon="📋").pack(side="right")

        # Password Card (with Reveal Eye & Auto-Masking Timer)
        p_card = _card(wrap, fg_color=C["card2"])
        p_card.pack(fill="x", pady=6)
        p_inner = ctk.CTkFrame(p_card, fg_color="transparent")
        p_inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(p_inner, text="PASSWORD", font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=C["t3"]).pack(anchor="w")

        pw_disp_lbl = ctk.CTkLabel(p_inner, text="●●●●●●●●●●●●",
                                   font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
                                   text_color=C["cyan_glow"])
        pw_disp_lbl.pack(side="left", pady=4)

        btn_box = ctk.CTkFrame(p_inner, fg_color="transparent")
        btn_box.pack(side="right")

        # Reveal state
        is_revealed = [False]
        mask_timer_job = [None]

        def _remask():
            is_revealed[0] = False
            pw_disp_lbl.configure(text="●●●●●●●●●●●●")
            eye_btn.configure(text="👁 Reveal")

        def _toggle_reveal():
            if not is_revealed[0]:
                is_revealed[0] = True
                pw_disp_lbl.configure(text=plain_pass)
                eye_btn.configure(text="🔒 Hide")
                self._log_security_event("VAULT", f"Temporarily revealed password for {site} (10s auto-mask).")
                # Cancel existing timer if any
                if mask_timer_job[0]:
                    self.root.after_cancel(mask_timer_job[0])
                # Auto re-mask after 10 seconds
                mask_timer_job[0] = self.root.after(10000, _remask)
            else:
                _remask()

        eye_btn = _btn_gradient(btn_box, "👁 Reveal", _toggle_reveal,
                                w=84, h=28, fg=C["card3"], hover=C["cyan_d"])
        eye_btn.pack(side="left", padx=4)

        _btn_gradient(btn_box, "Copy", lambda: self._copy_with_autoclear(plain_pass, "Password"),
                      w=64, h=28, fg=C["blue"], hover=C["blue_h"], icon="📋").pack(side="left", padx=4)

        # ── Password Strength Gauge ───────────────────────────────────────────
        gauge_col = C["ok"] if strength == "Strong" else (C["warn"] if strength == "Medium" else C["err"])
        score_val = 1.0 if strength == "Strong" else (0.5 if strength == "Medium" else 0.2)

        s_bar = ctk.CTkProgressBar(wrap, height=6, progress_color=gauge_col)
        s_bar.set(score_val)
        s_bar.pack(fill="x", pady=(2, 6))

        s_meta = ctk.CTkFrame(wrap, fg_color="transparent")
        s_meta.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(s_meta, text=f"Strength: {strength}", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=gauge_col).pack(side="left")
        ctk.CTkLabel(s_meta, text=f"Entropy: {len(plain_pass)*4} bits", font=ctk.CTkFont(size=11),
                     text_color=C["t3"]).pack(side="right")

        # ── Notes & Details ───────────────────────────────────────────────────
        if clean_notes:
            ctk.CTkLabel(wrap, text="SECURE NOTES", font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=C["cyan"]).pack(anchor="w", pady=(10, 4))
            n_card = _card(wrap, fg_color=C["card2"])
            n_card.pack(fill="x", pady=4)
            ctk.CTkLabel(n_card, text=clean_notes, wraplength=400, justify="left",
                         font=ctk.CTkFont(size=12), text_color=C["t2"]).pack(anchor="w", padx=14, pady=10)

        # ── Actions Row ───────────────────────────────────────────────────────
        act_row = ctk.CTkFrame(wrap, fg_color="transparent")
        act_row.pack(fill="x", pady=(20, 0))

        _btn_gradient(act_row, "Edit", lambda: self._open_edit_dialog(cred),
                      w=100, h=36, fg=C["card2"], hover=C["card3"], icon="✏️").pack(side="left", padx=(0, 6))

        _btn_gradient(act_row, "Share (ECDH)", lambda: SecureSharingDialog(self),
                      w=130, h=36, fg=C["purple"], hover=C["purple_h"], icon="🔐").pack(side="left", padx=6)

        _btn_gradient(act_row, "Delete", lambda: self._delete_credential(cred),
                      w=100, h=36, fg=C["err"], hover=C["err_h"], icon="🗑️").pack(side="right")

    # ══════════════════════════════════════════════════════════════════════════
    #                   TAB 2: VAULT HEALTH & HYGIENE
    # ══════════════════════════════════════════════════════════════════════════
    def _render_health_tab(self) -> None:
        wrap = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(wrap, text="🛡️  Vault Security Health & Hygiene",
                     font=ctk.CTkFont(family="Space Grotesk", size=24, weight="bold"),
                     text_color=C["cyan_glow"]).pack(anchor="w")
        ctk.CTkLabel(wrap, text="Comprehensive analysis of password entropy, duplicates, and breach risk.",
                     font=ctk.CTkFont(size=12), text_color=C["t2"]).pack(anchor="w", pady=(2, 16))

        # Calculate metrics
        all_creds = db_manager.get_all_credentials()
        n_total = len(all_creds)
        n_strong = 0
        n_weak = 0
        pass_counts: dict[str, list[str]] = {}
        n_old = 0

        for r in all_creds:
            try:
                p = encryption.decrypt_password(r[3], self.master_password)
                s = password_gen.evaluate_strength(p)
                if s == "Strong": n_strong += 1
                elif s in ("Weak", "Medium"): n_weak += 1
                pass_counts.setdefault(p, []).append(r[1])
            except Exception: pass

        # Reused passwords
        reused_groups = {k: v for k, v in pass_counts.items() if len(v) > 1}
        n_reused = sum(len(v) for v in reused_groups.values())

        score = int((n_strong / max(n_total, 1)) * 100) if n_total else 100
        score_col = C["ok"] if score >= 80 else (C["warn"] if score >= 50 else C["err"])

        # Health Banner Card
        banner = _card(wrap, fg_color=C["card2"], border_color=score_col)
        banner.pack(fill="x", pady=(0, 16))
        b_inner = ctk.CTkFrame(banner, fg_color="transparent")
        b_inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(b_inner, text=f"{score}/100", font=ctk.CTkFont(size=36, weight="bold"),
                     text_color=score_col).pack(side="left", padx=(0, 20))

        b_txt = ctk.CTkFrame(b_inner, fg_color="transparent")
        b_txt.pack(side="left")
        status_msg = "EXCELLENT SECURITY" if score >= 80 else ("ATTENTION RECOMMENDED" if score >= 50 else "CRITICAL VULNERABILITIES")
        ctk.CTkLabel(b_txt, text=status_msg, font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=score_col).pack(anchor="w")
        ctk.CTkLabel(b_txt, text=f"{n_strong} strong passwords out of {n_total} stored credentials.",
                     font=ctk.CTkFont(size=12), text_color=C["t2"]).pack(anchor="w")

        # 4 Interactive Breakdown Cards
        grid_fr = ctk.CTkFrame(wrap, fg_color="transparent")
        grid_fr.pack(fill="x", pady=6)
        for i in range(4): grid_fr.columnconfigure(i, weight=1)

        def _stat_tile(col, title, val, col_accent, filter_cmd):
            card = _card(grid_fr, fg_color=C["card2"])
            card.grid(row=0, column=col, padx=(0 if col == 0 else 8, 0), sticky="ew")
            ci = ctk.CTkFrame(card, fg_color="transparent")
            ci.pack(fill="both", padx=14, pady=14)
            ctk.CTkLabel(ci, text=val, font=ctk.CTkFont(size=26, weight="bold"),
                         text_color=col_accent).pack(anchor="w")
            ctk.CTkLabel(ci, text=title, font=ctk.CTkFont(size=11), text_color=C["t2"]).pack(anchor="w")
            _btn_gradient(ci, "Filter", filter_cmd, w=80, h=26,
                          fg=C["card3"], hover=col_accent).pack(anchor="w", pady=(8, 0))

        _stat_tile(0, "Strong Credentials", str(n_strong), C["ok"],
                   lambda: self._go_vault_filtered(None))
        _stat_tile(1, "Weak / Medium", str(n_weak), C["err"],
                   lambda: self._go_vault_filtered("weak"))
        _stat_tile(2, "Reused Across Sites", str(n_reused), C["warn"],
                   lambda: self._go_vault_filtered(None))
        _stat_tile(3, "Total Vault Accounts", str(n_total), C["cyan"],
                   lambda: self._go_vault_filtered(None))

        # Reused Passwords Warning List
        if reused_groups:
            ctk.CTkLabel(wrap, text="⚠  DUPLICATE PASSWORD VULNERABILITIES",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=C["warn"]).pack(anchor="w", pady=(24, 8))
            for p_hash, sites in reused_groups.items():
                rc = _card(wrap, fg_color=C["card2"])
                rc.pack(fill="x", pady=4)
                ri = ctk.CTkFrame(rc, fg_color="transparent")
                ri.pack(fill="x", padx=16, pady=10)
                ctk.CTkLabel(ri, text=f"Shared Password across {len(sites)} accounts:",
                             font=ctk.CTkFont(size=11, weight="bold"), text_color=C["t2"]).pack(anchor="w")
                ctk.CTkLabel(ri, text=" • ".join(sites),
                             font=ctk.CTkFont(size=13, weight="bold"), text_color=C["cyan"]).pack(anchor="w")

    def _go_vault_filtered(self, tag: str | None) -> None:
        self._filter_tag = tag
        self._switch_tab("vault")

    # ══════════════════════════════════════════════════════════════════════════
    #               TAB 3: SECURE FILE TRANSFER (DROPZONE)
    # ══════════════════════════════════════════════════════════════════════════
    def _render_transfer_tab(self) -> None:
        wrap = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=24, pady=16)

        no = self.admin_info["number"]
        name = self.admin_info["name"]

        ctk.CTkLabel(wrap, text="📤  Recipient-Bound Encrypted File Sharing",
                     font=ctk.CTkFont(family="Space Grotesk", size=24, weight="bold"),
                     text_color=C["cyan_glow"]).pack(anchor="w")
        ctk.CTkLabel(wrap, text="Hybrid Cryptosystem: Ephemeral ECDH (P-256) + HKDF-SHA256 + AES-256-GCM + Ed25519 Signature",
                     font=ctk.CTkFont(size=11), text_color=C["t3"]).pack(anchor="w", pady=(2, 16))

        # Dropzone Container
        dz_card = _card(wrap, fg_color=C["card2"], border_color=C["bdr_c"])
        dz_card.pack(fill="x", pady=6)
        dz_inner = ctk.CTkFrame(dz_card, fg_color="transparent")
        dz_inner.pack(fill="both", padx=28, pady=26)

        if no == 1:
            # Sender Dropzone (Admin 1 -> Admin 2)
            ctk.CTkLabel(dz_inner, text="📥  ENCRYPTION DROPZONE (ADMIN 1 SENDER)",
                         font=ctk.CTkFont(size=15, weight="bold"), text_color=C["cyan"]).pack()
            ctk.CTkLabel(dz_inner, text="Select any sensitive file to encrypt and sign for Admin 2 (Karthik).",
                         font=ctk.CTkFont(size=12), text_color=C["t2"]).pack(pady=4)

            selected_file = [None]
            file_lbl = ctk.CTkLabel(dz_inner, text="No file selected.", font=ctk.CTkFont(size=11), text_color=C["t3"])
            file_lbl.pack(pady=10)

            def _choose_src():
                p = filedialog.askopenfilename(title="Select File to Encrypt", filetypes=[("All files", "*.*")])
                if p:
                    selected_file[0] = p
                    sz = os.path.getsize(p)
                    file_lbl.configure(text=f"Selected: {Path(p).name} ({sz:,} bytes)", text_color=C["ok"])

            _btn_gradient(dz_inner, "Browse Source File", _choose_src, w=200, h=38,
                          fg=C["card3"], hover=C["cyan_d"], icon="📁").pack(pady=6)

            def _do_encrypt():
                if not selected_file[0]:
                    messagebox.showwarning("File Required", "Please browse and select a file first."); return
                src = selected_file[0]
                dst = filedialog.asksaveasfilename(
                    title="Save Encrypted Package", defaultextension=".svf",
                    initialfile="encrypted_for_admin2.svf",
                    filetypes=[("SecureVault File", "*.svf")])
                if not dst: return

                try:
                    sender_id = self._ensure_admin_identity(1, self.admin_info["password"])
                    recip_pub = self._get_admin_public_identity(2)
                    header = file_sharing.create_file_package(src, dst, sender_id, recip_pub)

                    orig_name = Path(src).name
                    pkg_name = Path(dst).name
                    db_manager.insert_file_history(1, 2, orig_name, pkg_name, "encrypt", "success")

                    self._log_security_event("ECDH", "Derived ephemeral shared secret via SECP256R1.")
                    self._log_security_event("AEAD", f"Encrypted {orig_name} ({header['size']:,} bytes) into {header['chunks']} AES-GCM chunks.")
                    self._log_security_event("SIGN", "Signed package header using Ed25519 private key.")

                    messagebox.showinfo("Success", f"File encrypted and signed successfully!\nSaved to:\n{dst}")
                except Exception as ex:
                    messagebox.showerror("Encryption Error", str(ex))

            _btn_gradient(dz_inner, "⚡ Encrypt & Sign for Admin 2", _do_encrypt, w=280, h=44,
                          fg=C["blue"], hover=C["blue_h"]).pack(pady=(12, 0))

        else:
            # Receiver Dropzone (Admin 2 Receiver)
            ctk.CTkLabel(dz_inner, text="📦  DECRYPTION & VERIFICATION DROPZONE (ADMIN 2)",
                         font=ctk.CTkFont(size=15, weight="bold"), text_color=C["ok"]).pack()
            ctk.CTkLabel(dz_inner, text="Import a .svf package sent by Admin 1 (Prakhar).",
                         font=ctk.CTkFont(size=12), text_color=C["t2"]).pack(pady=4)

            def _do_decrypt():
                src = filedialog.askopenfilename(
                    title="Select .svf Package", filetypes=[("SecureVault File", "*.svf"), ("All files", "*.*")])
                if not src: return
                dst = filedialog.asksaveasfilename(title="Save Restored Plaintext File", filetypes=[("All files", "*.*")])
                if not dst: return

                try:
                    receiver_id = self._ensure_admin_identity(2, self.admin_info["password"])
                    sender_pub = self._get_admin_public_identity(1)
                    res = file_sharing.open_file_package(src, dst, receiver_id, sender_pub)

                    orig_name = Path(dst).name
                    pkg_name = Path(src).name
                    db_manager.insert_file_history(1, 2, orig_name, pkg_name, "decrypt", "success")

                    self._log_security_event("SIGN", "Verified Admin 1 Ed25519 digital signature (Integrity OK).")
                    self._log_security_event("AEAD", f"Decrypted {res['size']:,} bytes with AES-256-GCM. Package intact.")

                    messagebox.showinfo("Success", f"Signature verified and file decrypted successfully!\nRestored to:\n{dst}")
                except Exception as ex:
                    self._log_security_event("ALERT", f"Decryption/verification failed: {ex}")
                    messagebox.showerror("Decryption Error", str(ex))

            _btn_gradient(dz_inner, "🔓 Import, Verify & Decrypt .svf", _do_decrypt, w=300, h=44,
                          fg=C["ok"], hover=C["ok_h"]).pack(pady=(16, 0))

    # ══════════════════════════════════════════════════════════════════════════
    #               TAB 4: REAL-TIME SECURITY AUDIT CONSOLE
    # ══════════════════════════════════════════════════════════════════════════
    def _render_console_tab(self) -> None:
        wrap = ctk.CTkFrame(self.content_area, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=20, pady=16)

        top = ctk.CTkFrame(wrap, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(top, text="📜  Real-Time Security Audit Console",
                     font=ctk.CTkFont(family="Space Grotesk", size=22, weight="bold"),
                     text_color=C["cyan_glow"]).pack(side="left")

        # Controls
        def _clear_console():
            self._console_logs.clear()
            self._log_security_event("SYSTEM", "Console buffer cleared by user.")

        def _export_logs():
            p = filedialog.asksaveasfilename(title="Save Audit Logs", defaultextension=".log",
                                             initialfile="security_audit.log", filetypes=[("Log files", "*.log")])
            if p:
                with open(p, "w", encoding="utf-8") as f:
                    for t, tag, msg in self._console_logs:
                        f.write(f"[{t}] [{tag:6s}] {msg}\n")
                messagebox.showinfo("Exported", f"Security logs exported to:\n{p}")

        _btn_gradient(top, "Export Log", _export_logs, w=100, h=30, fg=C["card2"], hover=C["card3"]).pack(side="right", padx=4)
        _btn_gradient(top, "Clear", _clear_console, w=70, h=30, fg=C["card2"], hover=C["err_h"]).pack(side="right", padx=4)

        # Terminal Container
        term_card = _card(wrap, fg_color="#050811", border_color=C["bdr_c"])
        term_card.pack(fill="both", expand=True)

        self._console_text = tk.Text(
            term_card, bg="#050811", fg=C["cyan_glow"],
            font=("Consolas", 11), bd=0, padx=16, pady=14,
            relief="flat", wrap="word"
        )
        vsb = ttk.Scrollbar(term_card, orient="vertical", command=self._console_text.yview)
        self._console_text.configure(yscrollcommand=vsb.set)
        self._console_text.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y", pady=6)

        # Text tags for color highlighting
        self._console_text.tag_config("time", foreground=C["t3"])
        self._console_text.tag_config("AUTH", foreground=C["cyan"])
        self._console_text.tag_config("CRYPTO", foreground=C["blue"])
        self._console_text.tag_config("AEAD", foreground=C["ok"])
        self._console_text.tag_config("ECDH", foreground=C["purple"])
        self._console_text.tag_config("SIGN", foreground=C["cyan_glow"])
        self._console_text.tag_config("ALERT", foreground=C["err"])
        self._console_text.tag_config("CLIP", foreground=C["warn"])
        self._console_text.tag_config("default", foreground=C["t1"])

        self._refresh_console_view()

    def _refresh_console_view(self) -> None:
        if not hasattr(self, "_console_text") or not self._console_text.winfo_exists():
            return
        self._console_text.delete("1.0", "end")
        for t, tag, msg in self._console_logs:
            self._console_text.insert("end", f"[{t}] ", "time")
            self._console_text.insert("end", f"[{tag:6s}] ", tag if tag in ("AUTH", "CRYPTO", "AEAD", "ECDH", "SIGN", "ALERT", "CLIP") else "default")
            self._console_text.insert("end", f"{msg}\n", "default")
        self._console_text.see("end")

    # ══════════════════════════════════════════════════════════════════════════
    #               TAB 5: PASSWORD GENERATOR
    # ══════════════════════════════════════════════════════════════════════════
    def _render_generator_tab(self) -> None:
        wrap = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(wrap, text="🎲  Cryptographically Secure Password Generator",
                     font=ctk.CTkFont(family="Space Grotesk", size=24, weight="bold"),
                     text_color=C["cyan_glow"]).pack(anchor="w")
        ctk.CTkLabel(wrap, text="Entropy generated via Python secrets module (OS-level hardware RNG).",
                     font=ctk.CTkFont(size=11), text_color=C["t3"]).pack(anchor="w", pady=(2, 16))

        card = _card(wrap, fg_color=C["card2"])
        card.pack(fill="x", pady=6)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", padx=24, pady=22)

        # Length slider
        len_var = tk.IntVar(value=18)
        len_lbl = ctk.CTkLabel(inner, text="Length: 18 characters", font=ctk.CTkFont(size=13, weight="bold"), text_color=C["cyan"])
        len_lbl.pack(anchor="w")

        slider = ctk.CTkSlider(inner, from_=8, to=64, variable=len_var,
                               progress_color=C["blue"], button_color=C["cyan"],
                               command=lambda v: len_lbl.configure(text=f"Length: {int(v)} characters"))
        slider.pack(fill="x", pady=(4, 14))

        # Checkboxes
        use_up = tk.BooleanVar(value=True)
        use_num = tk.BooleanVar(value=True)
        use_sym = tk.BooleanVar(value=True)

        cb_row = ctk.CTkFrame(inner, fg_color="transparent")
        cb_row.pack(fill="x", pady=(0, 14))
        for lbl, var in (("Uppercase (A-Z)", use_up), ("Digits (0-9)", use_num), ("Symbols (!@#)", use_sym)):
            ctk.CTkCheckBox(cb_row, text=lbl, variable=var, text_color=C["t1"],
                            fg_color=C["blue"]).pack(side="left", padx=(0, 18))

        # Output entry
        pw_var = tk.StringVar()
        pw_ent = ctk.CTkEntry(inner, textvariable=pw_var, height=44,
                              font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
                              fg_color=C["card"], border_color=C["cyan"], text_color=C["cyan_glow"])
        pw_ent.pack(fill="x", pady=(0, 12))

        def _do_gen():
            pw = password_gen.generate_password(len_var.get(), use_up.get(), use_num.get(), use_sym.get())
            pw_var.set(pw)

        btn_r = ctk.CTkFrame(inner, fg_color="transparent")
        btn_r.pack(fill="x")
        _btn_gradient(btn_r, "Generate Password", _do_gen, w=180, h=38, fg=C["blue"], hover=C["blue_h"], icon="🎲").pack(side="left")
        _btn_gradient(btn_r, "Copy to Clipboard", lambda: self._copy_with_autoclear(pw_var.get(), "Generated Password"),
                      w=180, h=38, fg=C["cyan"], hover=C["cyan_h"], icon="📋").pack(side="left", padx=10)

        _do_gen()

    # ══════════════════════════════════════════════════════════════════════════
    #               TAB 6 & 7: IDENTITIES & HISTORY
    # ══════════════════════════════════════════════════════════════════════════
    def _render_identities_tab(self) -> None:
        wrap = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(wrap, text="🔑  Cryptographic Public-Key Identities",
                     font=ctk.CTkFont(family="Space Grotesk", size=24, weight="bold"),
                     text_color=C["cyan_glow"]).pack(anchor="w", pady=(0, 14))

        for adm_no, adm_name in ((1, "Admin 1 (Sender / Prakhar)"), (2, "Admin 2 (Receiver / Karthik)")):
            c = _card(wrap, fg_color=C["card2"])
            c.pack(fill="x", pady=6)
            ci = ctk.CTkFrame(c, fg_color="transparent")
            ci.pack(fill="x", padx=20, pady=16)

            ctk.CTkLabel(ci, text=f"Administrator #{adm_no}: {adm_name}",
                         font=ctk.CTkFont(size=14, weight="bold"), text_color=C["cyan"]).pack(anchor="w")

            try:
                pub_id = self._get_admin_public_identity(adm_no)
                fp = pub_id.get("fingerprint", "Unknown")
            except Exception:
                fp = "Not generated yet."

            ctk.CTkLabel(ci, text=f"Fingerprint (SHA-256): {fp}", font=ctk.CTkFont(family="Consolas", size=11),
                         text_color=C["t2"]).pack(anchor="w", pady=(4, 8))

    def _render_history_tab(self) -> None:
        wrap = ctk.CTkFrame(self.content_area, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(wrap, text="🧾  Cryptographic Transfer Audit History",
                     font=ctk.CTkFont(family="Space Grotesk", size=22, weight="bold"),
                     text_color=C["cyan_glow"]).pack(anchor="w", pady=(0, 10))

        card = _card(wrap, fg_color=C["card2"])
        card.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Cyber.Treeview", background=C["card"], foreground=C["t1"],
                        rowheight=28, fieldbackground=C["card"], borderwidth=0, font=("Segoe UI", 10))
        style.configure("Cyber.Treeview.Heading", background=C["card2"], foreground=C["cyan"],
                        relief="flat", font=("Segoe UI", 10, "bold"))

        cols = ("sender", "recipient", "orig", "pkg", "op", "status", "date")
        htree = ttk.Treeview(card, columns=cols, show="headings", style="Cyber.Treeview")
        for c, h, w in zip(cols, ("Sender", "Recipient", "Original File", "Package", "Op", "Status", "Timestamp"),
                           (70, 80, 160, 160, 60, 60, 130)):
            htree.heading(c, text=h)
            htree.column(c, width=w, minwidth=40)

        rows = db_manager.get_file_history(self.admin_info["number"])
        for r in rows:
            htree.insert("", "end", values=(f"Admin {r[0]}", f"Admin {r[1]}", r[2], r[3], r[4], r[5], r[6][:16] if r[6] else "—"))

        vsb = ttk.Scrollbar(card, orient="vertical", command=htree.yview)
        htree.configure(yscrollcommand=vsb.set)
        htree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        vsb.pack(side="right", fill="y", pady=10, padx=(0, 6))

    # ══════════════════════════════════════════════════════════════════════════
    #                       ADD / EDIT / DELETE MODALS
    # ══════════════════════════════════════════════════════════════════════════
    def _open_add_dialog(self) -> None:
        self._credential_modal("Add Password", None)

    def _open_edit_dialog(self, cred: tuple) -> None:
        self._credential_modal("Edit Entry", cred)

    def _credential_modal(self, title: str, cred: tuple | None) -> None:
        dlg = ctk.CTkToplevel(self.root)
        dlg.title(f"KeyShield — {title}")
        dlg.geometry("480x560")
        dlg.configure(fg_color=C["bg"])
        dlg.transient(self.root)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text=f"{'➕' if cred is None else '✏️'}  {title}",
                     font=ctk.CTkFont(size=18, weight="bold"), text_color=C["cyan_glow"]).pack(pady=(20, 4))

        card = _card(dlg, corner_radius=16, border_color=C["cyan"])
        card.pack(fill="both", expand=True, padx=24, pady=10)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=22, pady=18, fill="both", expand=True)

        fields: dict[str, ctk.CTkEntry] = {}
        for key, lbl, show, default in [
            ("site", "Website / App Name", "", cred[1] if cred else ""),
            ("user", "Username / Email",   "", cred[2] if cred else ""),
            ("pass", "Password",           "●", ""),
            ("notes","Notes",              "", cred[4] if cred else ""),
        ]:
            ctk.CTkLabel(inner, text=lbl, font=ctk.CTkFont(size=11), text_color=C["t2"], anchor="w").pack(fill="x")
            e = ctk.CTkEntry(inner, width=390, fg_color=C["card2"], border_color=C["bdr"],
                             text_color=C["t1"], show=show, corner_radius=10)
            if default: e.insert(0, default)
            e.pack(pady=(0, 10))
            fields[key] = e

        if cred:
            try:
                fields["pass"].insert(0, encryption.decrypt_password(cred[3], self.master_password))
            except Exception: pass

        err_lbl = ctk.CTkLabel(inner, text="", text_color=C["err"], font=ctk.CTkFont(size=11), wraplength=340)
        err_lbl.pack()

        def _gen_pw():
            pw = password_gen.generate_password(16)
            fields["pass"].delete(0, "end")
            fields["pass"].insert(0, pw)

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(12, 0))
        _btn_gradient(btn_row, "🎲 Generate", _gen_pw, w=120, h=34, fg=C["card3"], hover=C["cyan_d"]).pack(side="left")

        def _save():
            s = fields["site"].get().strip()
            u = fields["user"].get().strip()
            p = fields["pass"].get()
            n = fields["notes"].get().strip()
            if not s or not u or not p:
                err_lbl.configure(text="Website, username and password are required."); return
            enc = encryption.encrypt_password(p, self.master_password)
            if cred:
                db_manager.update_credential(cred[0], s, u, enc, n)
                self._log_security_event("VAULT", f"Updated credential for '{s}'.")
            else:
                db_manager.insert_credential(s, u, enc, n)
                self._log_security_event("VAULT", f"Encrypted and added credential for '{s}'.")
            if self._active_tab == "vault":
                self._refresh_item_tiles()
            dlg.destroy()

        _btn_gradient(btn_row, "Save to Vault", _save, w=140, h=34, fg=C["blue"], hover=C["blue_h"]).pack(side="right")

    def _delete_credential(self, cred: tuple) -> None:
        if messagebox.askyesno("Confirm Delete", f"Delete credential for '{cred[1]}'?\nThis cannot be undone."):
            db_manager.delete_credential(cred[0])
            self._log_security_event("VAULT", f"Deleted credential for '{cred[1]}'.")
            self._selected_cred = None
            self._refresh_item_tiles()
            self._render_inspector_card(None)

    # ── Identity Helpers ──────────────────────────────────────────────────────
    def _ensure_admin_identity(self, admin_number: int, password: str) -> dict:
        ident_dir = Path("data/admin_identities") / f"admin{admin_number}"
        private_file = ident_dir / "identity_private.enc"
        public_file = ident_dir / "identity_public.json"
        if not (private_file.exists() and public_file.exists()):
            ident_dir.mkdir(parents=True, exist_ok=True)
            identity = identity_keys.create_identity(password, ident_dir)
            identity_keys.export_public_identity(identity, public_file)
            return identity
        return identity_keys.load_identity(password, ident_dir)

    def _get_admin_public_identity(self, admin_number: int) -> dict:
        pub_file = Path("data/admin_identities") / f"admin{admin_number}" / "identity_public.json"
        if not pub_file.exists():
            raise FileNotFoundError(f"Admin {admin_number} public identity file not found at {pub_file}.")
        return identity_keys.load_public_identity(pub_file)

    def _logout(self) -> None:
        self._log_security_event("AUTH", f"Admin {self.admin_info['number']} logged out.")
        self.master_password = None
        self.admin_info = None
        self._is_locked = False
        self._selected_cred = None
        self._show_login()
