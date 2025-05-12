import re
import tkinter as tk
from tkinter import ttk
import webbrowser
from ui import fa_icon
def edit_promo_nextdns(root: tk.Tk, logic, show_success, center_window):
    """
    Open a dialog to edit a single 6-line NextDNS [Resolve] block.
    """
    BLOCK_LINES = 6
    DNS_RE = re.compile(r"^DNS=.*#([0-9a-fA-F]{6})\.dns\.nextdns\.io$", re.I)
    TLS_RE = re.compile(r"^DNSOverTLS=yes$", re.I)

    def is_valid(block: str) -> bool:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if len(lines) != BLOCK_LINES or lines[0].lower() != "[resolve]" or not TLS_RE.fullmatch(lines[-1]):
            return False
        ids = [DNS_RE.fullmatch(ln).group(1).lower() for ln in lines[1:-1] if DNS_RE.fullmatch(ln)]
        return len(ids) == 4 and len(set(ids)) == 1

    pop = tk.Toplevel(root)
    pop.title("Edit NextDNS Block")
    pop.transient(root); pop.grab_set(); pop.resizable(False, False)

    frm = ttk.Frame(pop, padding=20)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text="Paste 6-line [Resolve] block:", font=("Satoshi", 10, "bold")).pack(anchor="w")

    txt = tk.Text(frm, width=60, height=8, font=("Courier New", 9))
    txt.pack(fill="both", expand=True, pady=(6,4))
    current = logic.load_promo_nextdns_config().get("resolve", "").strip()
    if current:
        txt.insert("1.0", current)

    status = ttk.Label(frm, font=("Satoshi", 9, "italic"))
    status.pack(anchor="w", pady=(2,6))

    btn_frame = ttk.Frame(frm)
    btn_frame.pack(fill="x")
    btn_frame.columnconfigure((0,1), weight=1)

    icon_save   = fa_icon("check",   size=14)
    icon_cancel = fa_icon("xmark",   size=14)

    save_btn = ttk.Button(btn_frame, image=icon_save, text="Save", compound="left", state="disabled")
    save_btn.grid(row=0, column=0, sticky="e", padx=(0,5))
    ttk.Button(btn_frame, image=icon_cancel, text="Cancel", compound="left", command=pop.destroy)\
        .grid(row=0, column=1, sticky="w")

    def on_modify(*_):
        block = txt.get("1.0", "end-1c").strip()
        if is_valid(block):
            status.config(text="Block is valid", foreground="#66f859")
            save_btn.config(state="normal")
        else:
            status.config(text="Invalid block (expect header + 4 DNS + DNSOverTLS=yes)", foreground="#ff5555")
            save_btn.config(state="disabled")

    txt.bind("<<Modified>>", lambda e: (txt.edit_modified(False), on_modify()))
    on_modify()

    def on_save():
        logic.save_promo_nextdns_config({"resolve": txt.get("1.0", "end-1c").strip()})
        show_success(root, "NextDNS block saved.")
        pop.destroy()

    save_btn.config(command=on_save)

    center_window(root, pop, 640, 320)
    pop.wait_window()


def connect_promo_nextdns(root: tk.Tk, logic, show_success, show_error, update_dns_info):
    """
    Apply stored NextDNS block, or open signup URL if none exists.
    """
    raw = logic.load_promo_nextdns_config().get("resolve", "").strip()
    if not raw:
        webbrowser.open("https://nextdns.io/?from=unf5m96x")
        return

    block = raw if raw.lstrip().lower().startswith("[resolve]") else f"[Resolve]\nDNS={raw}\nDNSOverTLS=yes\n"

    try:
        logic.write_config(block)
        update_dns_info()
        show_success(root, "Connected to NextDNS.")
    except Exception as e:
        show_error(root, str(e))
