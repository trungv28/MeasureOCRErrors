import json
from pathlib import Path
DATA_DIR = Path("data/raw/data/v0.9")

def load(split="train"):
    records = []
    for path in sorted(DATA_DIR.rglob("*.jsonl")):
        name = path.stem
        if "masked" in name:
            continue
        if "dta19" in name and "unmatched" not in name:
            continue
        if f"_{split}_" not in name and f"_{split}-unmatched_" not in name:
            continue
        with open(path) as f:
            records.extend(json.loads(line) for line in f)
    return records

def label(rec):
    meta = rec["document_metadata"]
    return f"{meta['primary_dataset_name']} ({meta['language']})"
