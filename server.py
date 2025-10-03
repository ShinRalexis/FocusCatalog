# server.py — FocusCatalog (API + static) v2.4
# Supporta link Civitai con modelVersionId per scegliere la versione precisa.
# Integra estrazione Trigger Words per modelli LoRA.
# Aggiunge persistenza dei percorsi (checkpoint/LoRA) su public/config.json
# -*- coding: utf-8 -*-
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Tuple, Optional
from urllib.parse import urlparse, parse_qs

import requests
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

OUT_DIR: Path = None
INDEX_PATH: Path = None
ROOTS: List[str] = []
SCAN_SCRIPT: Path = None

# === Config persistente dei percorsi ===
CONFIG_PATH: Path = None  # inizializzato in main()

def log(msg: str):
    print(f"[server] {msg}", flush=True)

def load_index():
    if INDEX_PATH.exists():
        try:
            return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            log(f"Errore lettura index.json: {e}")
    return {"generated_at": "", "items": []}

def save_index(data):
    data["generated_at"] = datetime.now().isoformat(timespec="seconds")
    INDEX_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def parse_civitai_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Ritorna (model_id, model_version_id) dalla URL Civitai.
    Esempi:
      https://civitai.com/models/443821?modelVersionId=2178176 -> ("443821", "2178176")
      https://civitai.com/models/443821                           -> ("443821", None)
    """
    try:
        u = urlparse(url)
        parts = u.path.strip("/").split("/")
        model_id = parts[1] if len(parts) >= 2 and parts[0].lower() == "models" else None
        q = parse_qs(u.query)
        version_id = q.get("modelVersionId", [None])[0]
        return model_id, version_id
    except Exception:
        return None, None

def civitai_fetch_model(model_id: str):
    r = requests.get(
        f"https://civitai.com/api/v1/models/{model_id}",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=25,
    )
    r.raise_for_status()
    return r.json()

def civitai_fetch_model_version(version_id: str):
    r = requests.get(
        f"https://civitai.com/api/v1/model-versions/{version_id}",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=25,
    )
    r.raise_for_status()
    return r.json()

# --- helper per estrarre trigger words da dati modello/versione ---
def extract_trigger_words(mdata: dict) -> List[str]:
    words = set()
    for ver in (mdata.get("modelVersions") or []):
        for w in (ver.get("trainedWords") or []):
            if w:
                words.add(w.strip())
    return sorted(words)

def extract_trigger_words_version(vdata: dict) -> List[str]:
    words = set()
    for w in (vdata.get("trainedWords") or []):
        if w:
            words.add(w.strip())
    return sorted(words)

def save_image_smart(raw: bytes, dest: Path) -> Path:
    try:
        img = Image.open(BytesIO(raw)); img.load()
    except Exception:
        return None
    ext = ".png" if (img.mode in ("RGBA", "LA") or getattr(img, "info", {}).get("transparency")) else ".jpg"
    dest = dest.with_suffix(ext)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        if ext == ".jpg":
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(dest, quality=92, optimize=True)
        else:
            img.save(dest, optimize=True)
        return dest
    except Exception:
        try:
            img = img.convert("RGB")
            dest = dest.with_suffix(".png")
            img.save(dest, optimize=True)
            return dest
        except Exception:
            return None

def resolve_scan_script(candidate: Path, out_dir: Path) -> Path:
    if candidate and candidate.exists():
        return candidate
    here = Path(__file__).resolve().parent / "scan_models.py"
    if here.exists():
        return here
    base = out_dir.parent / "scan_models.py"
    if base.exists():
        return base
    return candidate

# === Persistenza/config helpers ===
def norm_path(p: str) -> str:
    if not p:
        return ""
    p = os.path.expanduser(p.strip().strip('"').strip("'"))
    try:
        return str(Path(p).resolve())
    except Exception:
        return p

def load_config() -> dict:
    if CONFIG_PATH and CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            log(f"Errore lettura config.json: {e}")
    return {}

def save_config(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

# -------------------------- API --------------------------

@app.route("/api/health", methods=["GET"])
def api_health():
    ok = INDEX_PATH.exists()
    return jsonify({
        "ok": True,
        "index_exists": ok,
        "out_dir": str(OUT_DIR),
        "roots": ROOTS
    })

@app.route("/api/index", methods=["GET"])
def api_index():
    return send_from_directory(str(OUT_DIR), "index.json")

# === NEW: Config endpoints ===
@app.route("/api/config", methods=["GET"])
def api_get_config():
    cfg = load_config()
    return jsonify({
        "checkpointDir": cfg.get("checkpointDir", ""),
        "loraDir": cfg.get("loraDir", ""),
        "roots": ROOTS
    })

@app.route("/api/config", methods=["POST"])
def api_set_config():
    data = request.get_json(force=True, silent=True) or {}
    checkpoint = norm_path(data.get("checkpointDir", "") or "")
    lora = norm_path(data.get("loraDir", "") or "")

    # Validazione minima: se impostati, devono essere directory esistenti
    for label, p in [("checkpointDir", checkpoint), ("loraDir", lora)]:
        if p and not Path(p).is_dir():
            return jsonify({"ok": False, "error": f"{label} non esiste o non è una cartella: {p}"}), 400

    cfg = {
        "checkpointDir": checkpoint,
        "loraDir": lora,
    }
    save_config(cfg)

    # Aggiorna i ROOTS a runtime (senza riavvio)
    global ROOTS
    ROOTS = [p for p in [checkpoint, lora] if p]

    return jsonify({"ok": True, "roots": ROOTS})

@app.route("/api/set_link_and_fetch", methods=["POST"])
def api_set_link_and_fetch():
    """
    Body JSON: { "slug": "...", "civitai_url": "https://civitai.com/models/ID?modelVersionId=VID" }
    - Se modelVersionId è presente: scarica solo le immagini di quella versione.
    - Altrimenti: usa la prima versione disponibile del modello.
    Aggiorna: civitai_url, display_name, previews e (se LoRA) triggerWords.
    """
    data = request.json or {}
    slug = (data.get("slug") or "").strip()
    url  = (data.get("civitai_url") or "").strip()
    if not slug or not url:
        return jsonify({"ok": False, "error": "slug e civitai_url richiesti"}), 400

    model_id, version_id = parse_civitai_url(url)
    if not model_id:
        return jsonify({"ok": False, "error": "Link Civitai non valido"}), 400

    idx = load_index()
    item = next((it for it in idx.get("items", []) if it.get("slug") == slug), None)
    if not item:
        return jsonify({"ok": False, "error": "Slug non trovato in index.json"}), 404

    try:
        previews_rel = []
        display_name = item.get("display_name") or item.get("name")
        trigger_words: List[str] = []

        if version_id:
            # Caso: versione specifica
            vdata = civitai_fetch_model_version(version_id)
            mname = (vdata.get("model") or {}).get("name") or ""
            vname = vdata.get("name") or ""
            display_name = (mname or display_name)
            if vname:
                display_name = f'{display_name} [{vname}]'
            urls = [im.get("url") for im in vdata.get("images", []) if im.get("url")]
            trigger_words = extract_trigger_words_version(vdata)
        else:
            # Caso: modello generico → prima versione
            mdata = civitai_fetch_model(model_id)
            mname = mdata.get("name") or display_name
            display_name = mname
            urls = []
            for ver in mdata.get("modelVersions", []):
                vname = ver.get("name") or ""
                if vname:
                    display_name = f'{mname} [{vname}]'
                for im in ver.get("images", []):
                    u = im.get("url")
                    if u: urls.append(u)
                if urls:
                    break
            trigger_words = extract_trigger_words(mdata)

        urls = urls[:3]  # massimo 3 preview
        for i,u in enumerate(urls):
            r = requests.get(u, headers={"User-Agent":"Mozilla/5.0","Referer":"https://civitai.com/"}, timeout=25)
            r.raise_for_status()
            saved = save_image_smart(r.content, OUT_DIR/"assets"/"previews"/slug/f"civitai_{i+1}")
            if saved:
                rel = str(saved.relative_to(OUT_DIR)).replace("\\","/")
                if rel not in previews_rel:
                    previews_rel.append(rel)
            time.sleep(0.15)

        # Aggiorna item
        item["civitai_url"] = url
        if display_name:
            item["display_name"] = display_name
        for rel in previews_rel:
            if rel not in item["previews"]:
                item["previews"].append(rel)

        # --- salva trigger words se modello è LoRA ---
        if (item.get("type") or "").lower() == "lora":
            if trigger_words:
                item["triggerWords"] = trigger_words
                item["triggerWordsChecked"] = True
                item["triggerWordsNotFound"] = False
            else:
                item["triggerWords"] = []
                item["triggerWordsChecked"] = True
                item["triggerWordsNotFound"] = True

        save_index(idx)
        return jsonify({
            "ok": True,
            "display_name": item.get("display_name"),
            "previews": item.get("previews"),
            "triggerWords": item.get("triggerWords", []),
        })
    except Exception as e:
        log(f"set_link_and_fetch error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    script = resolve_scan_script(SCAN_SCRIPT, OUT_DIR)
    if not script or not script.exists():
        msg = f"scan_models.py non trovato. Cercato in: {SCAN_SCRIPT}, {Path(__file__).parent/'scan_models.py'}, {OUT_DIR.parent/'scan_models.py'}"
        log(msg)
        return jsonify({"ok": False, "error": msg}), 500
    try:
        cmd = [
            sys.executable, str(script),
            "--out", str(OUT_DIR),
            "--gc-previews",
            "--new-days", "30",
            "--roots"
        ] + ROOTS
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        log(f"Eseguo refresh: {cmd}")
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                             cwd=str(script.parent), env=env)
        if res.returncode != 0:
            log(f"scan_models.py stderr:\n{res.stderr}")
            return jsonify({"ok": False, "error": "scan_models.py ha fallito", "stderr": res.stderr}), 500
        idx = load_index()
        return jsonify({"ok": True, "counts": idx.get("counts", {}), "generated_at": idx.get("generated_at")})
    except Exception as e:
        log(f"refresh error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# -------------------------- static --------------------------

@app.route("/")
def root():
    return send_from_directory(str(OUT_DIR), "index.html")

@app.route("/index.html")
def index_html():
    return send_from_directory(str(OUT_DIR), "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    fpath = OUT_DIR / filename
    if not fpath.exists() or not fpath.is_file():
        abort(404)
    return send_from_directory(str(OUT_DIR), filename)

# -------------------------- entry --------------------------

def main():
    global OUT_DIR, INDEX_PATH, ROOTS, SCAN_SCRIPT, CONFIG_PATH
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="public", help="Cartella che contiene index.html e index.json")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--roots", nargs="+", default=[
        r"D:\Stable Diffusion\Fooocus_win64_2-1-831\Fooocus\models\checkpoints",
        r"D:\Stable Diffusion\Fooocus_win64_2-1-831\Fooocus\models\loras",
    ], help="Cartelle da scansionare")
    ap.add_argument("--scan-script", default="scan_models.py", help="Percorso a scan_models.py")
    args = ap.parse_args()

    OUT_DIR = Path(args.out).resolve()
    INDEX_PATH = OUT_DIR / "index.json"
    CONFIG_PATH = OUT_DIR / "config.json"  # <--- qui vivrà la config persistente
    ROOTS = [str(Path(r).resolve()) for r in args.roots]
    SCAN_SCRIPT = Path(args.scan_script).resolve()

    # Applica override da config.json se presente
    _cfg = load_config()
    cp = norm_path(_cfg.get("checkpointDir", "") or "")
    lr = norm_path(_cfg.get("loraDir", "") or "")
    _override = [x for x in [cp, lr] if x]
    if _override:
        ROOTS = _override
        log(f"Override ROOTS da config.json: {ROOTS}")

    log(f"OUT_DIR = {OUT_DIR}")
    log(f"INDEX_PATH = {INDEX_PATH}")
    log(f"CONFIG_PATH = {CONFIG_PATH}")
    log(f"ROOTS = {ROOTS}")
    log(f"SCAN_SCRIPT (candidate) = {SCAN_SCRIPT}")

    app.run(host=args.host, port=args.port, debug=False, threaded=True)

if __name__ == "__main__":
    main()
