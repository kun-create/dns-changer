import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Tuple
from PIL import Image, ImageDraw, ImageTk
from tkfontawesome import icon_to_image

_icon_cache: Dict[Tuple[str, str, int], ImageTk.PhotoImage] = {}

def fa_icon(name: str, fill: str = "#d0d0d0", size: int = 16) -> ImageTk.PhotoImage:
    """Return a cached Font Awesome icon."""
    key = (name, fill, size)
    if key not in _icon_cache:
        _icon_cache[key] = icon_to_image(name, fill=fill, scale_to_width=size)
    return _icon_cache[key]

_success_icon: Optional[ImageTk.PhotoImage] = None
_error_icon:   Optional[ImageTk.PhotoImage] = None
_shield_icon:  Optional[ImageTk.PhotoImage] = None
_ok_btn_icon:  Optional[ImageTk.PhotoImage] = None
_cancel_btn_icon: Optional[ImageTk.PhotoImage] = None

def _load_core_icons() -> None:
    """Load icons used by popups."""
    global _success_icon, _error_icon, _shield_icon, _ok_btn_icon, _cancel_btn_icon
    if _success_icon is None:
        _success_icon   = fa_icon("circle-check",  fill="#66f859", size=20)
        _error_icon     = fa_icon("circle-xmark",  fill="#ff5555", size=20)
        _shield_icon    = fa_icon("shield-halved", fill="#d0d0d0", size=20)
        _ok_btn_icon    = fa_icon("check",         fill="#ffffff", size=14)
        _cancel_btn_icon= fa_icon("xmark",         fill="#ffffff", size=14)

def center_window(root: tk.Tk, win: tk.Toplevel, width: int = 300, height: int = 150) -> None:
    """Center `win` over `root`."""
    root.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width()  - width)  // 2
    y = root.winfo_rooty() + (root.winfo_height() - height) // 2
    win.geometry(f"{width}x{height}+{max(x,0)}+{max(y,0)}")

def _popup(root: tk.Tk, title: str, message: str, icon: ImageTk.PhotoImage, auto_close: bool=False) -> None:
    """Generic popup window."""
    win = tk.Toplevel(root)
    win.title(title)
    win.transient(root); win.grab_set(); win.resizable(False, False)

    frm = ttk.Frame(win, padding=20)
    frm.pack(fill="both", expand=True)

    hdr = ttk.Frame(frm); hdr.pack(fill="x")
    ttk.Label(hdr, image=icon).pack(side="left", padx=(0,8))
    ttk.Label(hdr, text=message, font=("Satoshi", 11, "bold"), wraplength=240, justify="left").pack(side="left", fill="x", expand=True)

    ttk.Button(frm, text="OK", image=_ok_btn_icon, compound="left", command=win.destroy).pack(fill="x", pady=(14,0))

    center_window(root, win, 320, 160)
    if auto_close:
        win.after(2800, win.destroy)
    win.bind("<Return>",  lambda e: win.destroy())
    win.bind("<Escape>", lambda e: win.destroy())
    win.wait_window()

def show_success(root: tk.Tk, msg: str) -> None:
    """Show a transient success popup."""
    _load_core_icons()
    _popup(root, "Success", msg, _success_icon, auto_close=True)

def show_error(root: tk.Tk, msg: str) -> None:
    """Show an error popup."""
    _load_core_icons()
    _popup(root, "Error", msg, _error_icon)

def prompt_sudo_password(root: tk.Tk) -> Optional[str]:
    """Prompt for sudo password; returns input or None."""
    _load_core_icons()

    win = tk.Toplevel(root)
    win.title("Sudo Authentication")
    win.transient(root); win.grab_set(); win.resizable(False, False)

    frm = ttk.Frame(win, padding=24)
    frm.pack(fill="both", expand=True)

    hdr = ttk.Frame(frm); hdr.pack(fill="x", pady=(0,12))
    ttk.Label(hdr, image=_shield_icon).pack(side="left", padx=(0,8))
    ttk.Label(hdr, text="Enter your sudo password:", font=("Satoshi", 11, "bold")).pack(side="left", fill="x")

    pwd_var = tk.StringVar()
    ttk.Entry(frm, textvariable=pwd_var, show="•", font=("Satoshi", 10)).pack(fill="x")
    frm.after_idle(lambda: frm.focus())

    btns = ttk.Frame(frm); btns.pack(fill="x", pady=(16,0))
    btns.columnconfigure((0,1), weight=1)

    ttk.Button(btns, text="Cancel", image=_cancel_btn_icon, compound="left",
               command=lambda: (pwd_var.set(""), win.destroy())
              ).grid(row=0, column=0, sticky="ew", padx=(0,6))
    ttk.Button(btns, text="OK", image=_ok_btn_icon, compound="left",
               command=win.destroy
              ).grid(row=0, column=1, sticky="ew", padx=(6,0))

    win.bind("<Return>",  lambda e: win.destroy())
    win.bind("<Escape>", lambda e: (pwd_var.set(""), win.destroy()))

    center_window(root, win, 360, 200)
    win.wait_window()
    return pwd_var.get().strip() or None

def create_circle_image(diameter: int, color: str) -> ImageTk.PhotoImage:
    """Return a circular image of given diameter and color."""
    scale = 10
    img = Image.new("RGBA", (diameter*scale, diameter*scale), (0,0,0,0))
    ImageDraw.Draw(img).ellipse((0,0,diameter*scale,diameter*scale), fill=color)
    return ImageTk.PhotoImage(img.resize((diameter, diameter), Image.LANCZOS))
