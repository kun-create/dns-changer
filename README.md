![DNS Changer Hero Image](./assets/photo1.png)

DNS Changer 🚀
==============

Simple, powerful, one-click DNS server changer app made for Linux! A lightweight desktop application to quickly switch between DNS servers (NextDNS, Cloudflare, Google, etc.) with real-time ping testing.

* * *

📌 Features
-----------

*   Change DNS settings with a single command
*   **Built-in & custom DNS provider widgets** for easy selection and management
*   Modular UI components (`widgets.py`, `panels/`) for a clean, extensible interface
*   Backup and restore DNS configurations
*   Lightweight, fast, and Linux-only

* * *

❓ Why use DNS Changer?
----------------------

This app is simple and easy to use—just one click to change your DNS server. It offers built-in ad-blocking and filtering, reduces ping for faster responses, and is designed with a privacy-focused mindset.

* * *

💾 Installation
---------------

1.  **Download the pre-built binary (recommended)**  
    Grab the standalone [dns-changer](https://github.com/kun-create/dns-changer/releases/latest/download/dns-changer) executable from GitHub Releases—no Python or dependencies required. Make it executable and run:
    
        curl -L -o dns-changer https://github.com/kun-create/dns-changer/releases/latest/download/dns-changer
        chmod +x dns-changer
        ./dns-changer
    
2.  **Or build from source with Nuitka**  
    
        python -m nuitka \
         --onefile \
         --follow-imports \
         --enable-plugin=tk-inter \
         --include-package=tksvg \
         --include-package=tkfontawesome \
         --include-package-data=tksvg \
         --include-package-data=tkfontawesome \
         --include-data-files=./logo/logo40.png=./logo/logo40.png \
         --include-data-files=./data/dns_configs.json=./data/dns_configs.json \
         --include-data-files=./data/promo_nextdns.json=./data/promo_nextdns.json \
         --linux-icon=./logo/logo40.png \
         --company-name='Kun Create' \
         --product-name='DNS Changer' \
         --file-description='GUI tool to switch DNS on Linux' \
         --file-version=1.0.0 \
         --product-version=1.0.0 \
         --assume-yes-for-downloads \
         --lto=yes \
         --static-libpython=auto \
         --remove-output \
         --output-filename=dns-changer \
         main.py
    

* * *
![DNS Changer Image](./assets/photo2.png)

🚀 Usage
--------

*   **Launch the GUI**
    
        ./dns-changer
    
*   **Select a provider** via the DNS provider widgets on the main tab
*   Click **Connect** to apply your choice
*   Use the **Backup/Restore** panel to manage snapshots of your DNS configuration

* * *

📦 Releases
-----------

We **strongly recommend** using the pre-built `dns-changer` binary from our [Releases page](https://github.com/kun-create/dns-changer/releases/latest) for the fastest setup:

*   [Download dns-changer](https://github.com/kun-create/dns-changer/releases/latest/download/dns-changer)
*   Make it executable: `chmod +x dns-changer`
*   Run: `./dns-changer`

* * *