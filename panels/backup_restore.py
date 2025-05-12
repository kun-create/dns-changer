import os
import tkinter as tk
from tkinter import ttk
from ui import fa_icon

def build(parent: tk.Frame, *, root, logic, show_success, show_error, update_dns_info):
    """
    Build the Backup/Restore tab: create, list, restore, and delete DNS backups.
    """
    # icons
    icon_backup  = fa_icon("box-archive",      size=14)
    icon_clean   = fa_icon("trash",            size=14)
    icon_refresh = fa_icon("arrows-rotate",    size=14)
    icon_restore = fa_icon("arrow-rotate-left",size=14)
    icon_delete  = fa_icon("trash-can",        size=14)

    # callbacks
    def create_backup():
        try:
            name = logic.backup_resolved()
            listbox.insert(0, name)
            show_success(root, f"Backup created: {name}")
        except Exception as e:
            show_error(root, str(e))

    def clean_backups():
        try:
            logic.clean_backups()
            listbox.delete(0, tk.END)
            show_success(root, "All backups removed.")
        except Exception as e:
            show_error(root, str(e))

    def refresh_list():
        listbox.delete(0, tk.END)
        if os.path.isdir(logic.BACKUPS_DIR):
            for fname in sorted(os.listdir(logic.BACKUPS_DIR), reverse=True):
                listbox.insert(tk.END, fname)

    def restore_selected():
        sel = listbox.curselection()
        if not sel:
            show_error(root, "Select a backup first.")
            return
        fname = listbox.get(sel[0])
        try:
            logic.restore_backup(fname)
            update_dns_info()
            show_success(root, "Backup restored.")
        except Exception as e:
            show_error(root, str(e))

    def delete_selected():
        sel = listbox.curselection()
        if not sel:
            show_error(root, "Select a backup first.")
            return
        fname = listbox.get(sel[0])
        try:
            os.remove(os.path.join(logic.BACKUPS_DIR, fname))
            listbox.delete(sel[0])
            show_success(root, "Backup deleted.")
        except Exception as e:
            show_error(root, str(e))

    # layout
    frame = ttk.Frame(parent, padding=10)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    actions = ttk.Frame(frame)
    actions.pack(fill="x", pady=(0, 10))
    ttk.Button(actions, text="Create Backup", image=icon_backup,
               compound="left", command=create_backup).pack(side="left", expand=True, fill="x", padx=(0,5))
    ttk.Button(actions, text="Clean Backups", image=icon_clean,
               compound="left", command=clean_backups).pack(side="left", expand=True, fill="x", padx=(5,0))

    hdr = ttk.Frame(frame)
    hdr.pack(fill="x")
    ttk.Label(hdr, text="Available Backups", font=("Satoshi", 10, "bold")).pack(side="left")
    ttk.Button(hdr, image=icon_refresh, width=4, command=refresh_list).pack(side="right")

    list_frame = ttk.Frame(frame)
    list_frame.pack(fill="both", expand=True)
    listbox = tk.Listbox(list_frame, height=8)
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)

    footer = ttk.Frame(frame)
    footer.pack(fill="x", pady=(10,0))
    ttk.Button(footer, text="Restore Selected", image=icon_restore,
               compound="left", command=restore_selected).pack(side="left", expand=True, fill="x", padx=(0,5))
    ttk.Button(footer, text="Delete Selected", image=icon_delete,
               compound="left", command=delete_selected).pack(side="left", expand=True, fill="x", padx=(5,0))

    refresh_list()
