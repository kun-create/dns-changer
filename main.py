"""
Entry point – builds the GUI, wires callbacks, and starts the Tk main-loop.
Split modules:
    • logic.py            – backend / sudo helpers
    • next_dns_promo.py   – NextDNS-specific dialog + connect logic
    • panels/*.py         – individual tab builders
"""

import sys
import re
import logic
import sv_ttk
import platform
import ipaddress
import tkinter as tk
import next_dns_promo
from pathlib import Path
from typing import Callable, Optional
from widgets import create_provider_row
from tkinter import ttk, PhotoImage, messagebox
from panels import add as add_panel, backup_restore as backup_panel
from ui import center_window, show_error, show_success, create_circle_image, fa_icon

# -- Root window & theme ------------------------------------------------
if platform.system() != "Linux":
    messagebox.showerror("Unsupported OS", "This program runs only on Linux.")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent
root = tk.Tk()
root.iconphoto(False, PhotoImage(file=BASE_DIR / "logo" / "logo40.png"))
root.title("DNS Changer")
root.geometry("410x570")
root.resizable(False, False)
root.attributes("-alpha", 0.9)
sv_ttk.set_theme("dark")
logic.set_root(root)

# -- Icons & styles -----------------------------------------------------
icon_dns    = fa_icon("earth-americas", size=16)
icon_add    = fa_icon("plus",            size=16)
icon_backup = fa_icon("box-archive",     size=16)

style = ttk.Style()
style.configure("Card.TFrame",     background="#333333", relief="ridge", borderwidth=2)
style.configure("PromoCard.TFrame",relief="ridge", borderwidth=2)
style.configure("TNotebook.Tab",   padding=[10,5])

# -- Global UI state ----------------------------------------------------
provider_widgets: dict[str, dict] = {}
promo_circle_label: ttk.Label | None = None
promo_connect_btn: ttk.Button | None = None
add_list_refresh: Optional[Callable[[], None]] = None

# -- Helper utils -------------------------------------------------------
def custom_dns_names() -> list[str]:
    return [n for n, d in logic.DNS_CONFIGS.items() if d.get("custom")]

def update_dns_info(skip_connectivity: bool = False) -> None:
    cur = logic.get_current_dns()

    if cur == "NextDNS":
        name_value.config(text="NextDNS")
        promo = logic.load_promo_nextdns_config().get("resolve", "").strip()
        m = re.search(r"DNS=([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)#", promo)
        ip_addr = m.group(1) if m else "N/A"
        address_value.config(text=ip_addr)
    elif cur in logic.DNS_CONFIGS:
        name_value.config(text=cur)
        address_value.config(text=logic.DNS_CONFIGS[cur]["ip"])
    else:
        name_value.config(text="Unknown")
        address_value.config(text="N/A")

    ok = True if skip_connectivity else logic.check_dns_connectivity()
    status_value.config(
        text="CONNECTED" if ok else "DISCONNECTED",
        foreground="#66f859" if ok else "#ff5555",
    )

    # Update ping
    if cur == "NextDNS":
        ping_target = ip_addr
    elif cur in logic.DNS_CONFIGS:
        ping_target = logic.DNS_CONFIGS[cur]["ip"]
    else:
        ping_target = None

    ping_value.config(
        text=logic.get_ping_time(ping_target) if ping_target else "N/A"
    )

    # Update status dots and buttons for built-ins
    for name, w in provider_widgets.items():
        active = (name == cur)
        color = "#66f859" if active else "#615382"
        dot = create_circle_image(20, color)
        w["circle"].config(image=dot)
        w["circle"].image = dot
        w["button"].config(
            text="Connected" if active else "Connect",
            state="disabled" if active else "normal",
            style="Connected.TButton" if active else "TButton",
        )

    # Update promo row
    if promo_circle_label:
        color = "#66f859" if cur == "NextDNS" else "#615382"
        dot = create_circle_image(20, color)
        promo_circle_label.config(image=dot)
        promo_circle_label.image = dot

    if promo_connect_btn:
        is_next = (cur == "NextDNS")
        promo_connect_btn.config(
            text="Connected" if is_next else "Connect",
            state="disabled" if is_next else "normal",
        )

    # Refresh the ADD-tab list if open
    if add_list_refresh:
        add_list_refresh()



def update_ping() -> None:
    cur = logic.get_current_dns()

    if cur == "NextDNS":
        promo = logic.load_promo_nextdns_config().get("resolve", "").strip()
        m = re.search(r"DNS=([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)#", promo)
        ping_target = m.group(1) if m else None
    elif cur in logic.DNS_CONFIGS:
        ping_target = logic.DNS_CONFIGS[cur]["ip"]
    else:
        ping_target = None

    ping_value.config(
        text=logic.get_ping_time(ping_target) if ping_target else "N/A"
    )
    root.after(1000, update_ping)



# -- DNS operations ----------------------------------------------------
def connect_provider(name: str) -> None:
    try:
        logic.write_config(logic.DNS_CONFIGS[name]["config"])
        update_dns_info()
        show_success(root, f"Switched to {name}.")
    except Exception as e:
        show_error(root, str(e))

def remove_custom_dns(name: str) -> None:
    if logic.DNS_CONFIGS.get(name, {}).get("custom"):
        logic.DNS_CONFIGS.pop(name)
        logic.save_dns_configs()
        show_success(root, "Custom DNS removed.")
        if add_list_refresh:
            add_list_refresh()
        update_dns_info()

# -- Validators --------------------------------------------------------
def _valid_name(txt: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9 _-]{1,40}", txt))

def _valid_ip(addr: str) -> bool:
    if not addr:
        return False
    try:
        ipaddress.ip_address(addr.split("#")[0])
        return True
    except ValueError:
        return False

# -- Add Custom DNS popup ---------------------------------------------
def show_add_dns_popup() -> None:
    popup = tk.Toplevel(root)
    popup.title("Add Custom DNS")
    popup.transient(root); popup.grab_set(); popup.resizable(False, False)

    frm = ttk.Frame(popup, padding=20)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, image=icon_add, text="Create Custom DNS", compound="left",
              font=("Satoshi", 13, "bold")
    ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 15))

    fields = [("Name*", "name"), ("Primary*", "primary"), ("Secondary", "secondary"), ("IPv6", "ipv6")]
    vars_ = {key: tk.StringVar() for _, key in fields}
    tls_var = tk.BooleanVar(value=True)
    status_map: dict[str, tuple[ttk.Label, bool]] = {}
    validators = {
        "name": _valid_name,
        "primary": _valid_ip,
        "secondary": lambda v: (not v) or _valid_ip(v),
        "ipv6":     lambda v: (not v) or _valid_ip(v),
    }

    def set_status(lbl: ttk.Label, ok: bool, req: bool):
        lbl.config(text="✓" if ok else ("✗" if req else ""),
                   foreground="#66f859" if ok else "#ff5555")

    for i, (label, key) in enumerate(fields, start=1):
        req = label.endswith("*")
        font = ("Satoshi", 10, "bold") if req else ("Satoshi", 10)
        ttk.Label(frm, text=label, font=font).grid(row=i, column=0, sticky="e", padx=5, pady=4)
        ttk.Entry(frm, textvariable=vars_[key], width=32).grid(row=i, column=1, sticky="w", padx=5, pady=4)
        lbl = ttk.Label(frm, width=2, font=("Satoshi", 11, "bold"))
        lbl.grid(row=i, column=2, sticky="w")
        status_map[key] = (lbl, req)

    row = len(fields) + 1
    ttk.Label(frm, text="DNS-over-TLS:", font=("Satoshi", 10)).grid(row=row, column=0, sticky="e", padx=5, pady=4)
    ttk.Checkbutton(frm, variable=tls_var).grid(row=row, column=1, sticky="w")
    ttk.Separator(frm).grid(row=row+1, column=0, columnspan=3, sticky="ew", pady=10)

    btns = ttk.Frame(frm)
    btns.grid(row=row+2, column=0, columnspan=3, sticky="e")
    btns.columnconfigure((0, 1), weight=1)

    save_btn = ttk.Button(btns, text="Save", width=12, state="disabled")
    save_btn.grid(row=0, column=0, sticky="e", padx=(0, 5))
    ttk.Button(btns, text="Cancel", command=popup.destroy, width=12).grid(row=0, column=1, sticky="w")

    def validate(*_):
        ok_all = True
        for key, (lbl, req) in status_map.items():
            ok = validators[key](vars_[key].get().strip())
            set_status(lbl, ok, req)
            if req and not ok:
                ok_all = False
        save_btn.config(state="normal" if ok_all else "disabled")

    for v in vars_.values():
        v.trace_add("write", validate)
    validate()

    def save():
        nm = vars_["name"].get().strip()
        p1 = vars_["primary"].get().strip()
        p2 = vars_["secondary"].get().strip()
        p6 = vars_["ipv6"].get().strip()
        if nm in logic.DNS_CONFIGS:
            show_error(root, "A DNS with that name already exists.")
            return
        line = p1 + (f" {p2}" if p2 else "") + (f" {p6}" if p6 else "")
        cfg = f"[Resolve]\nDNS={line}\nDNSOverTLS={'yes' if tls_var.get() else 'no'}\n"
        logic.DNS_CONFIGS[nm] = {"config": cfg, "ip": p1, "custom": True}
        logic.save_dns_configs()
        show_success(root, "Custom DNS added.")
        if add_list_refresh:
            add_list_refresh()
        popup.destroy()

    save_btn.config(command=save)
    center_window(root, popup, 480, 330)
    popup.wait_window()

# -- Notebook & tabs ---------------------------------------------------
main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill="both", expand=True)

notebook = ttk.Notebook(main_frame)
notebook.pack(fill="both", expand=True)

dns_tab = ttk.Frame(notebook)
add_tab = ttk.Frame(notebook)
backup_tab = ttk.Frame(notebook)

notebook.add(dns_tab,    image=icon_dns,    text="DNS",            compound="left")
notebook.add(add_tab,    image=icon_add,    text="ADD",            compound="left")
notebook.add(backup_tab, image=icon_backup, text="Backup", compound="left")

# -- DNS tab – header & promo -----------------------------------------
dns_content = ttk.Frame(dns_tab, padding=5)
dns_content.pack(fill="both", expand=True, padx=5)

card = ttk.Frame(dns_content, padding=10, style="Card.TFrame")
card.pack(fill="x", pady=10)

lbl_f, val_f = ("Satoshi", 10, "bold"), ("Satoshi", 10)
ttk.Label(card, text="Name:",    font=lbl_f).grid(row=0, column=0, sticky="e", padx=10, pady=5)
name_value    = ttk.Label(card, text="Unknown", font=val_f)
name_value.grid(row=0, column=1, sticky="w", padx=10, pady=5)

ttk.Label(card, text="Address:", font=lbl_f).grid(row=0, column=2, sticky="e", padx=10, pady=5)
address_value = ttk.Label(card, text="N/A",      font=val_f)
address_value.grid(row=0, column=3, sticky="w", padx=10, pady=5)

ttk.Label(card, text="Ping:",    font=lbl_f).grid(row=1, column=0, sticky="e", padx=10, pady=5)
ping_value    = ttk.Label(card, text="N/A",      font=val_f)
ping_value.grid(row=1, column=1, sticky="w", padx=10, pady=5)

ttk.Label(card, text="Status:",  font=lbl_f).grid(row=1, column=2, sticky="e", padx=10, pady=5)
status_value  = ttk.Label(card, text="DISCONNECTED", font=val_f, foreground="#615382")
status_value.grid(row=1, column=3, sticky="w", padx=10, pady=5)

promo_card = ttk.Frame(dns_content, padding=10, style="PromoCard.TFrame")
promo_card.pack(fill="x", pady=(0,5))

promo_inner = ttk.Frame(promo_card)
promo_inner.pack(fill="x", expand=True)

promo_circle_label = ttk.Label(promo_inner)
promo_circle_label.pack(side="left", padx=10)

txt_frame = ttk.Frame(promo_inner)
txt_frame.pack(side="left", fill="both", expand=True, padx=10)

ttk.Label(txt_frame, text="NextDNS – Enhanced DNS Protection",
          font=("Satoshi",10,"bold"), foreground="#0060FF").pack(anchor="w")
ttk.Label(txt_frame, text="Block ads & trackers, secure your network",
          font=("Satoshi",9), foreground="#a0a0a0").pack(anchor="w")

btns = ttk.Frame(promo_card)
btns.pack(fill="x", pady=5)
btns.columnconfigure((0,1), weight=1)

ttk.Button(btns, text="Edit",
           command=lambda: next_dns_promo.edit_promo_nextdns(root, logic, show_success, center_window)
          ).grid(row=0, column=0, sticky="ew", padx=(0,5))

promo_connect_btn = ttk.Button(
    btns,
    text="Connect",
    command=lambda: [
        next_dns_promo.connect_promo_nextdns(root, logic, show_success, show_error, update_dns_info),
        update_ping()
    ]
)
promo_connect_btn.grid(row=0, column=1, sticky="ew", padx=(5,0))

# -- Built-in provider list -------------------------------------------
dns_list_frame = ttk.Frame(dns_content, padding=10)
dns_list_frame.pack(fill="both", expand=True, pady=10)

ttk.Button(dns_tab, image=icon_add, text="Add DNS", compound="left",
           command=lambda: notebook.select(add_tab)
          ).pack(side="bottom", fill="x", pady=(0,10), padx=10)

# -- Build other tabs & populate providers ----------------------------
logic.load_dns_configs()

add_list_refresh = add_panel.build(
    add_tab,
    show_add_dns_popup,
    custom_dns_names,
    remove_custom_dns,
    connect_provider,
)

backup_panel.build(
    backup_tab,
    root=root,
    logic=logic,
    show_success=show_success,
    show_error=show_error,
    update_dns_info=update_dns_info,
)

for name, data in logic.DNS_CONFIGS.items():
    if not data.get("custom"):
        provider_widgets[name] = create_provider_row(
            dns_list_frame,
            name,
            connect_callback=connect_provider,
            remove_callback=None,
            is_custom=False,
        )

# -- Kick-off ---------------------------------------------------------
update_dns_info(skip_connectivity=True)
update_ping()
root.after(200, update_dns_info)
root.after(400, lambda: logic.ensure_initial_backup())
root.mainloop()
