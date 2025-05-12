import tkinter as tk
from tkinter import ttk
import logic
from ui import create_circle_image, fa_icon

def build(parent, show_add_dns_popup, list_dns_names, remove_callback, connect_callback):
    """
    Build the ADD tab UI: list custom DNS entries with connect/remove buttons,
    and an 'Add Custom DNS' button at the bottom. Returns a refresh function.
    """
    icon_plus = fa_icon("plus", size=14)

    container = ttk.Frame(parent, padding=10)
    container.pack(fill="both", expand=True, padx=5, pady=10)

    rows_frame = ttk.Frame(container)
    rows_frame.pack(fill="both", expand=True)

    add_btn = ttk.Button(
        container,
        image=icon_plus,
        text="Add Custom DNS",
        compound="left",
        command=lambda: [show_add_dns_popup(), refresh()],
    )
    add_btn.pack(side="bottom", fill="x")

    def truncate(text: str, limit: int = 24) -> str:
        return text if len(text) <= limit else text[: limit - 1] + "…"

    def make_row(name: str):
        active = (name == logic.get_current_dns())
        color = "#66f859" if active else "#615382"

        row = ttk.Frame(rows_frame)
        row.pack(fill="x", pady=3)
        row.columnconfigure(1, weight=1)

        # status dot
        circ = ttk.Label(row)
        circ.grid(column=0, row=0, padx=5)
        img = create_circle_image(20, color)
        circ.config(image=img)
        circ.image = img

        # provider name
        ttk.Label(
            row,
            text=truncate(name),
            font=("Satoshi", 10),
            anchor="w"
        ).grid(column=1, row=0, sticky="ew")

        # connect button
        connect_text = "Connected" if active else "Connect"
        connect_state = "disabled" if active else "normal"
        ttk.Button(
            row,
            text=connect_text,
            state=connect_state,
            width=10,
            command=lambda n=name: [connect_callback(n), refresh()],
        ).grid(column=2, row=0, padx=5)

        # remove button
        ttk.Button(
            row,
            text="Remove",
            width=8,
            command=lambda n=name: [remove_callback(n), refresh()],
        ).grid(column=3, row=0)

    empty_label = None

    def refresh():
        nonlocal empty_label
        for w in rows_frame.winfo_children():
            w.destroy()

        names = list_dns_names()
        if not names:
            empty_label = ttk.Label(
                rows_frame,
                text="(empty)",
                foreground="#888888",
                font=("Satoshi", 10, "italic")
            )
            empty_label.pack(pady=20)
        else:
            empty_label = None
            for n in names:
                make_row(n)

    refresh()
    return refresh
