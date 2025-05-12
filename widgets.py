import tkinter as tk
from tkinter import ttk
from ui import create_circle_image, fa_icon

def create_provider_row(parent, name: str, connect_callback, remove_callback=None, is_custom=False):
    """
    Build a row with status dot, name label, connect button, and optional remove button.
    Returns widget references.
    """
    frame = ttk.Frame(parent)
    frame.pack(fill="x", pady=5)

    circle = ttk.Label(frame)
    circle.pack(side="left", padx=5)

    label = ttk.Label(frame, text=name, font=("Satoshi", 10))
    label.pack(side="left", padx=10)

    ttk.Frame(frame).pack(side="left", expand=True, fill="x")

    btn_connect = ttk.Button(
        frame,
        text="Connect",
        compound="left",
        width=12,
        command=lambda n=name: connect_callback(n),
    )
    btn_connect.pack(side="right", padx=5)

    widgets = {
        "frame": frame,
        "circle": circle,
        "button": btn_connect,
        "label": label,
    }

    if is_custom and remove_callback:
        icon_remove = fa_icon("trash-can", size=14)
        btn_remove = ttk.Button(
            frame,
            image=icon_remove,
            text="Remove",
            compound="left",
            width=8,
            command=lambda n=name: remove_callback(n),
        )
        btn_remove.pack(side="right", padx=(5, 0))
        widgets["remove_button"] = btn_remove

    dot = create_circle_image(20, "#615382")
    circle.config(image=dot)
    circle.image = dot

    return widgets
