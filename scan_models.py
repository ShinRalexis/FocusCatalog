# scan_models.py — FocusCatalog v6.2 (ASCII-safe)
# Scansiona cartelle di modelli (Checkpoint/LoRA), preserva metadati esistenti,
# rimuove voci di file scomparsi e genera public/index.json.
# -*- coding: utf-8 -*-

import argparse
import json
import re
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
from PIL import Image

MODEL_EXT = {".safetensors", ".ckpt", ".pt", ".bin", ".gguf"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}

# ========== Utility di base ==========
def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "-", name.strip())
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or str(abs(hash(name)) % (10**10))

def nice_name(file: Path) -> str:
    base = file.stem
    base = re.sub(r"\s*\([0-9a-f]{5,}\)\s*$", "", base, flags=re.I)
    base = re.sub(r"\s*\[[0-9a-f]{5,}\]\s*$", "", base, flags=re.I)
    base = re.sub(r"\.[0-9a-f]{5,}$", "", base, flags=re.I)
    return base.strip() or file.stem

def detect_type(file: Path) -> str:
    p = file.as_posix().lower()
    if "lora" in p or "loras" in p or "lora" in file.parent.name.lower():
        return "LoRA"
    if "checkpoint" in p or "checkpoints" in p:
        return "Checkpoint"
    return "Model"

def find_local_previews(file: Path) -> List[Path]:
    out: List[Path] = []
    for ext in IMG_EXT:
        direct = file.with_suffix(ext)
        if direct.exists():
            out.append(direct)
    if not out:
        for ext in IMG_EXT:
            cand = file.parent / (file.stem + ext)
            if cand.exists():
                out.append(cand)
    return out

def ensure_thumb(infile: Path, outfile: Path, size=(640, 640)) -> bool:
    try:
        outfile.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(infile) as im:
            im.thumbnail(size)
            if im.mode in ("RGBA", "LA") or getattr(im, "info", {}).get("transparency"):
                im.save(outfile.with_suffix(".png"))
            else:
                im = im.convert("RGB")
                im.save(outfile.with_suffix(".jpg"), quality=90, optimize=True)
        return True
    except Exception:
        return False

def load_existing_index(index_path: Path) -> Dict[str, Dict[str, Any]]:
    m: Dict[str, Dict[str, Any]] = {}
    if index_path.exists():
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            for it in data.get("items", []):
                slug = it.get("slug")
                if not slug:
                    continue
                m[slug] = {
                    "display_name": it.get("display_name"),
                    "civitai_url": it.get("civitai_url"),
                    "previews": it.get("previews", []),
                    # NEW: manteniamo eventuali triggerWords già presenti
                    "triggerWords": it.get("triggerWords"),
                    "triggerWordsChecked": it.get("triggerWordsChecked"),
                    "triggerWordsNotFound": it.get("triggerWordsNotFound"),
                }
        except Exception:
            pass
    return m

# ========== Funzioni Trigger Words Civitai ==========
def _civitai_model_id(url: str):
    if not url:
        return None
    m = re.search(r"/models/(\d+)", url)
    return m.group(1) if m else None

def _fetch_civitai_trigger_words(model_id: str, timeout=12) -> List[str]:
    api = f"https://civitai.com/api/v1/models/{model_id}"
    r = requests.get(api, timeout=timeout, headers={
        "User-Agent": "FocusCatalog/1.0 (+local)"
    })
    r.raise_for_status()
    data = r.json()
    words = set()
    for v in (data.get("modelVersions") or []):
        for w in (v.get("trainedWords") or []):
            w = (w or "").strip()
            if w:
                words.add(w)
    return sorted(words)

# ========== MAIN ==========
def main():
    ap = argparse.ArgumentParser(description="Scansiona modelli (Checkpoint/LoRA) e genera public/index.json")
    ap.add_argument("--roots", nargs="+", required=True, help="Percorsi da scansionare (es. checkpoints, loras)")
    ap.add_argument("--out", default="public", help="Cartella output (conterrà index.json e assets/previews)")
    ap.add_argument("--new-days", type=int, default=30, help="Giorni per marcare come NUOVO")
    ap.add_argument("--gc-previews", action="store_true", help="Rimuove cartelle previews di modelli non più presenti")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "index.json"
    previews_root = out_dir / "assets" / "previews"

    existing_meta = load_existing_index(index_path)

    now = datetime.now()
    cutoff = now - timedelta(days=args.new_days)
    items: List[Dict[str, Any]] = []
    seen_slugs: set = set()

    for root in args.roots:
        rootp = Path(root)
        if not rootp.exists():
            print("[!] Skip: {} non esiste".format(root))
            continue

        for f in rootp.rglob("*"):
            if not (f.is_file() and f.suffix.lower() in MODEL_EXT):
                continue

            name = nice_name(f)
            slug = slugify(name)
            mtype = detect_type(f)
            st = f.stat()
            size_mb = round(st.st_size / (1024 * 1024), 2)
            mtime = datetime.fromtimestamp(st.st_mtime)

            previews_rel: List[str] = []
            if slug in existing_meta:
                for rel in existing_meta[slug].get("previews", []):
                    p = out_dir / rel
                    if p.exists():
                        previews_rel.append(str(p.relative_to(out_dir)).replace("\\", "/"))

            for p in find_local_previews(f):
                dest_base = previews_root / slug / p.name
                if ensure_thumb(p, dest_base):
                    saved_dir = (previews_root / slug)
                    for cand in saved_dir.glob(p.stem + ".*"):
                        rel = str(cand.relative_to(out_dir)).replace("\\", "/")
                        if rel not in previews_rel:
                            previews_rel.append(rel)

            ex = existing_meta.get(slug, {})
            item: Dict[str, Any] = {
                "name": name,
                "display_name": ex.get("display_name"),
                "slug": slug,
                "type": mtype,
                "filename": str(f),
                "folder": str(f.parent),
                "size_mb": size_mb,
                "modified": mtime.isoformat(timespec="seconds"),
                "previews": previews_rel,
                "civitai_url": ex.get("civitai_url"),
                "is_new": mtime >= cutoff,
                # Manteniamo eventuali dati trigger words
                "triggerWords": ex.get("triggerWords"),
                "triggerWordsChecked": ex.get("triggerWordsChecked"),
                "triggerWordsNotFound": ex.get("triggerWordsNotFound"),
            }

            # --- NEW: Fetch Trigger Words solo per LoRA con link Civitai ---
            try:
                is_lora = (mtype.lower() == "lora")
                civitai_url = (item.get("civitai_url") or "").strip()
                already_has_triggers = bool(item.get("triggerWords"))
                already_checked = bool(item.get("triggerWordsChecked"))

                if is_lora and civitai_url and (not already_has_triggers) and (not already_checked):
                    mid = _civitai_model_id(civitai_url)
                    if mid:
                        tw = _fetch_civitai_trigger_words(mid)
                        if tw:
                            item["triggerWords"] = tw
                            item["triggerWordsChecked"] = True
                            item["triggerWordsNotFound"] = False
                        else:
                            item["triggerWords"] = []
                            item["triggerWordsChecked"] = True
                            item["triggerWordsNotFound"] = True
                    else:
                        item["triggerWordsChecked"] = True
            except Exception as e:
                item["triggerWordsError"] = str(e)[:200]

            items.append(item)
            seen_slugs.add(slug)

    if args.gc_previews and previews_root.exists():
        for d in previews_root.iterdir():
            try:
                if d.is_dir() and d.name not in seen_slugs:
                    for p in d.rglob("*"):
                        try: p.unlink()
                        except Exception: pass
                    try: d.rmdir()
                    except Exception: pass
            except Exception:
                pass

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "counts": {
            "total": len(items),
            "checkpoints": sum(1 for x in items if x["type"] == "Checkpoint"),
            "loras": sum(1 for x in items if x["type"] == "LoRA"),
        },
        "items": items,
    }

    index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[OK] Generato {} ({} modelli).".format(index_path, len(items)))
    if args.gc_previews:
        print("[i] Garbage-collect delle anteprime completato.")

if __name__ == "__main__":
    main()
