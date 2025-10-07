![FocusCatalog Screenshot](public/sample1.jpg)
### ❤️ FocusCatalog (Fooocus Tool)

Find your LoRA or Checkpoint instantly, copy, paste, and generate in Fooocus for a seamless workflow.

🧭 Overview

FocusCatalog is a lightweight local web app designed to organize your Fooocus LoRA and Checkpoint models, complete with thumbnails, metadata, and trigger words ready to copy and paste.

It was born out of necessity.
Working with Fooocus quickly becomes frustrating: dozens (or even hundreds) of models and LoRA files pile up, often with cryptic names and no previews.
This chaos makes it nearly impossible to keep a clean workflow, remember what each model does, or quickly find the right LoRA for a project.

FocusCatalog fixes that.
It brings clarity and structure to your model library: scans your folders, generates an index with thumbnails, shows file size and date, and — if desired — fetches previews and trigger words directly from Civitai.
What used to be a messy folder now becomes a clear, searchable visual catalog.

✨ Features

🧩 Automatic scan of Checkpoints and LoRA folders

🗂️ JSON index generation with full metadata

🖼️ Local preview support (just drop an image next to the model file)

🌐 Civitai integration for display name, previews, and trigger words

🆕 “NEW” badge for recently added models

❤️ Favorites and NSFW toggle filtering

⚙️ Configurable folders and persistent settings via options.html

💻 Runs entirely locally — simple Flask web server, no external dependencies

🌍 Supported languages: Italian, English, Spanish, French

![FocusCatalog Screenshot](public/sample2.png)

📖 Documentation

A full Prompt Manual is included in help.html, covering:
Key prompt principles
Recommended structure
Negative prompts
Trigger words
Troubleshooting

---

## 🚀 Quick Start

### 🧩 Run locally with Python
Requirements: Python 3.9+

```bash
pip install flask flask-cors pillow requests
python server.py --out public
```
Open: http://127.0.0.1:8765

### 🐳 Run with Docker (recommended)
```bash
docker build -t focuscatalog .
docker run -it -p 8765:8765 -v /path/to/models:/models focuscatalog
```
Replace /path/to/models with the folder containing your Fooocus models.
Example (Windows):
```bash
docker run -it -p 8765:8765 -v "D:\Stable Diffusion\Fooocus_win64_2-1-831\Fooocus\models:/models" focuscatalog
```
🧰 Advanced: Custom Compose Setup (optional)
For power users who prefer full control, here’s a sample docker-compose.yml:
```bash
services:
  focuscatalog:
    build: .
    ports:
      - "8765:8765"
    environment:
      OUT_DIR: "/app/public"
      ROOT_CHECKPOINTS: "/models/checkpoints"
      ROOT_LORAS: "/models/loras"
    volumes:
      - "./:/app"
      - "D:/Stable Diffusion/Fooocus_win64_2-1-831/Fooocus/models/checkpoints:/models/checkpoints:ro"
      - "D:/Stable Diffusion/Fooocus_win64_2-1-831/Fooocus/models/loras:/models/loras:ro"
```
## 📦 License

FocusCatalog © 2025 MetaDarko

This work is licensed under the **Creative Commons Attribution-ShareAlike 4.0 International License (CC-BY-SA 4.0)**.

You are free to share and adapt the material for any purpose, even commercially,  
as long as you **give appropriate credit to MetaDarko**,  
and distribute your contributions under the same license.

> In short: anyone can improve or fork FocusCatalog,  
> but the authorship remains with **MetaDarko**, and all derivatives must remain open.

