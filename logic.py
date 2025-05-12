"""
All non‑GUI operations: sudo helpers, DNS handling, backups, ping, persistence.
Stores JSON data and backups in ~/.config/dns-changer/ (XDG‑compliant).
"""

import json
import os
import shutil
import subprocess
from datetime import datetime
from typing import Optional
from subprocess import TimeoutExpired

# ------------------------------------------------------------------#
#  Config directory handling                                         #
# ------------------------------------------------------------------#
PROJECT_ID = "dns-changer"


def _xdg_config_home() -> str:
    """Return $XDG_CONFIG_HOME or fall back to ~/.config."""
    return os.getenv("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))


CONFIG_DIR = os.path.join(_xdg_config_home(), PROJECT_ID)
BACKUPS_DIR = os.path.join(CONFIG_DIR, "backups")  # ← backups live here
LEGACY_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _ensure_config_dir() -> None:
    """Create ~/.config/dns-changer if it doesn't exist."""
    os.makedirs(CONFIG_DIR, exist_ok=True)


def _migrate_legacy_json(file_name: str) -> None:
    """
    If JSON file exists in legacy ./data directory and not yet in CONFIG_DIR,
    copy it over.
    """
    legacy_path = os.path.join(LEGACY_DATA_DIR, file_name)
    new_path = os.path.join(CONFIG_DIR, file_name)
    if not os.path.exists(new_path) and os.path.exists(legacy_path):
        try:
            shutil.copy2(legacy_path, new_path)
        except OSError:
            pass


# ------------------------------------------------------------------#
#  Paths                                                             #
# ------------------------------------------------------------------#
DEFAULT_DNS_FILE = "dns_configs.json"  # (legacy; rarely used now)
CUSTOM_DNS_FILE = "custom_dns.json"
PROMO_NEXTDNS_FILE = "promo_nextdns.json"

DEFAULT_DNS_PATH = os.path.join(CONFIG_DIR, DEFAULT_DNS_FILE)
CUSTOM_DNS_PATH = os.path.join(CONFIG_DIR, CUSTOM_DNS_FILE)
PROMO_NEXTDNS_PATH = os.path.join(CONFIG_DIR, PROMO_NEXTDNS_FILE)

# systemd paths
RESOLVED_CONF_PATH = "/etc/systemd/resolved.conf"

# ------------------------------------------------------------------#
#  In‑memory DNS config cache                                        #
# ------------------------------------------------------------------#
DEFAULT_DNS_CONFIGS = {
    "Google": {
        "config": "[Resolve]\nDNS=8.8.8.8 8.8.4.4\nDNSOverTLS=yes\n",
        "ip": "8.8.8.8",
        "custom": False,
    },
    "Cloudflare": {
        "config": "[Resolve]\nDNS=1.1.1.1 1.0.0.1\nDNSOverTLS=yes\n",
        "ip": "1.1.1.1",
        "custom": False,
    },

    "Quad9": {
        "config": "[Resolve]\nDNS=9.9.9.9 149.112.112.112\nDNSOverTLS=yes\n",
        "ip": "9.9.9.9",
        "custom": False,
    },
    
    "AdGuard": {
        "config": "[Resolve]\nDNS=94.140.14.14 94.140.15.15\nDNSOverTLS=yes\n",
        "ip": "94.140.14.14",
        "custom": False,
    }
}

DNS_CONFIGS: dict[str, dict] = {}
_sudo_password: Optional[str] = None
_root = None  # set by main.py

# ------------------------------------------------------------------#
#  Setup / migration                                                 #
# ------------------------------------------------------------------#
_ensure_config_dir()
for fname in (DEFAULT_DNS_FILE, CUSTOM_DNS_FILE, PROMO_NEXTDNS_FILE):
    _migrate_legacy_json(fname)

# ------------------------------------------------------------------#
#  Public helpers                                                    #
# ------------------------------------------------------------------#
def set_root(root):  # called once from main.py
    global _root
    _root = root


def load_dns_configs():
    global DNS_CONFIGS
    DNS_CONFIGS = DEFAULT_DNS_CONFIGS.copy()

    # always merge in project defaults (data/dns_configs.json) so your additions show up
    try:
        with open(os.path.join(LEGACY_DATA_DIR, DEFAULT_DNS_FILE), "r") as f:
            project_defaults = json.load(f)
        for name, entry in project_defaults.items():
            entry["custom"] = entry.get("custom", False)
            DNS_CONFIGS[name] = entry
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # legacy user file (rare)
    if os.path.exists(DEFAULT_DNS_PATH):
        try:
            with open(DEFAULT_DNS_PATH, "r") as f:
                legacy = json.load(f)
            for name, entry in legacy.items():
                entry["custom"] = entry.get("custom", True)
                DNS_CONFIGS[name] = entry
        except json.JSONDecodeError:
            pass

    # modern custom providers
    if os.path.exists(CUSTOM_DNS_PATH):
        try:
            with open(CUSTOM_DNS_PATH, "r") as f:
                custom = json.load(f)
            for name, entry in custom.items():
                entry["custom"] = True
            DNS_CONFIGS.update(custom)
        except json.JSONDecodeError:
            pass



def save_dns_configs():
    """Persist only custom providers to ~/.config/dns-changer/custom_dns.json."""
    custom_only = {n: d for n, d in DNS_CONFIGS.items() if d.get("custom")}
    with open(CUSTOM_DNS_PATH, "w") as f:
        json.dump(custom_only, f, indent=4)


# ------------------------------------------------------------------#
#  Promo‑NextDNS helpers                                             #
# ------------------------------------------------------------------#
def load_promo_nextdns_config() -> dict:
    if os.path.exists(PROMO_NEXTDNS_PATH):
        try:
            with open(PROMO_NEXTDNS_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_promo_nextdns_config(data: dict) -> None:
    with open(PROMO_NEXTDNS_PATH, "w") as f:
        json.dump(data, f, indent=4)


# ------------------------------------------------------------------#
#  Sudo helpers                                                      #
# ------------------------------------------------------------------#
def _prompt_password():
    from ui import prompt_sudo_password

    if _root is None:
        raise RuntimeError("Root window not set; call set_root() first.")
    return prompt_sudo_password(_root)


def _ask_sudo_password():
    global _sudo_password
    if _sudo_password is None:
        _sudo_password = _prompt_password()
    return _sudo_password


def _run_sudo(cmd: list[str]):
    global _sudo_password
    pwd = _ask_sudo_password()
    if not pwd:
        raise RuntimeError("Sudo password not provided.")
    result = subprocess.run(
        ["sudo", "-S"] + cmd, input=f"{pwd}\n", text=True, capture_output=True
    )
    if result.returncode != 0:
        _sudo_password = None
        if "incorrect password" in result.stderr.lower():
            raise RuntimeError("Wrong password! Please try again.")
        raise RuntimeError(result.stderr.strip())


# ------------------------------------------------------------------#
#  Core DNS / backup operations                                      #
# ------------------------------------------------------------------#
def write_config(cfg: str):
    with open("/tmp/resolved.conf", "w") as tmp:
        tmp.write(cfg)
    _run_sudo(["cp", "/tmp/resolved.conf", RESOLVED_CONF_PATH])
    _run_sudo(["systemctl", "restart", "systemd-resolved"])


def check_dns_connectivity() -> bool:
    """
    Return True if “dig google.com” resolves quickly, otherwise False.
    Never raises – protects the UI from crashes when DNS is broken.
    """
    try:
        res = subprocess.run(
            ["dig", "+short", "google.com"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return bool(res.stdout.strip())
    except (TimeoutExpired, FileNotFoundError, OSError):
        return False


def get_current_dns() -> str:
    try:
        with open(RESOLVED_CONF_PATH) as f:
            content = f.read()

        promo = load_promo_nextdns_config().get("resolve", "").strip()
        if promo:
            block = (
                promo
                if promo.lstrip().lower().startswith("[resolve]")
                else f"[Resolve]\nDNS={promo}\nDNSOverTLS=yes\n"
            )
            if block.strip() in content:
                return "NextDNS"

        for n, d in DNS_CONFIGS.items():
            if d["ip"] and d["ip"] in content:
                return n
    except Exception:
        pass
    return "Unknown"

def get_ping_time(addr: str) -> str:
    if not addr or addr == "N/A":
        return "N/A"
    res = subprocess.run(
        ["ping", "-c", "1", "-W", "1", addr], capture_output=True, text=True
    )
    for line in res.stdout.splitlines():
        if "time=" in line:
            return line.split("time=")[1].split()[0] + " ms"
    return "N/A"


# --------------------------- Backups ---------------------------------#
def ensure_initial_backup() -> bool:
    """
    Create ~/.config/dns-changer/backups/Initial.conf once.
    Returns True if the file was created, False if it already existed.
    """
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    initial_path = os.path.join(BACKUPS_DIR, "Initial.conf")
    if os.path.exists(initial_path):
        return False
    shutil.copy2(RESOLVED_CONF_PATH, initial_path)
    return True


def backup_resolved() -> str:
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fname = f"Backup_{ts}.conf"
    shutil.copy2(RESOLVED_CONF_PATH, os.path.join(BACKUPS_DIR, fname))
    return fname


def restore_backup(fname: str):
    _run_sudo(
        [
            "cp",
            os.path.join(BACKUPS_DIR, fname),
            RESOLVED_CONF_PATH,
        ]
    )
    _run_sudo(["systemctl", "restart", "systemd-resolved"])


def restore_latest():
    if not os.path.exists(BACKUPS_DIR):
        raise RuntimeError("No backups available.")
    latest = sorted(os.listdir(BACKUPS_DIR), reverse=True)
    if not latest:
        raise RuntimeError("No backups available.")
    restore_backup(latest[0])


def clean_backups():
    if not os.path.exists(BACKUPS_DIR):
        raise RuntimeError("No backup directory exists.")
    for f in os.listdir(BACKUPS_DIR):
        os.remove(os.path.join(BACKUPS_DIR, f))
