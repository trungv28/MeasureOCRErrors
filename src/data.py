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


def lines(rec):
    gt_text = rec["ground_truth"]["transcription_unit"]
    ocr_text = rec["ocr_hypothesis"]["transcription_unit"]
    gt_offs = rec["ground_truth"]["line_offsets"]
    ocr_offs = rec["ocr_hypothesis"]["line_offsets"]
    if not gt_offs or not ocr_offs or len(gt_offs) != len(ocr_offs):
        return []
    return [
        (gt_text[s1:e1], ocr_text[s2:e2])
        for (s1, e1), (s2, e2) in zip(gt_offs, ocr_offs)
    ]


if __name__ == '__main__':
    records = load('train')

    rec = records[0]
    meta = rec['document_metadata']
    print('date:', meta['date'])
    print('scope:', meta['transcription_unit_scope'])

    print(rec['ground_truth']['transcription_unit'][:121])
    print(rec['ocr_hypothesis']['transcription_unit'][:121])

    rec_lines = lines(rec)
    for gt_line, ocr_line in rec_lines[:11]:
        print('gt:', gt_line)
        print('ocr:', ocr_line)
        print()
