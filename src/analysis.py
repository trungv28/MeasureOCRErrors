import difflib
import statistics
from collections import defaultdict
from jiwer import cer, wer
from data import label, lines, load


def is_hist_sensitive(token):
    return token and (token[0].isupper() or any(c.isdigit() for c in token))


def main():
    records = [
        rec
        for rec in load("train")
        if rec["ground_truth"]["transcription_unit"]
        and rec["ocr_hypothesis"]["transcription_unit"]
    ]

    group_lines = defaultdict(list)
    all_line_pairs = []
    for rec in records:
        rec_lines = lines(rec)
        if not rec_lines:
            continue
        for gt_line, ocr_line in rec_lines:
            if gt_line.strip() and ocr_line.strip():
                group_lines[label(rec)].append((gt_line, ocr_line))
                all_line_pairs.append((gt_line, ocr_line, rec))

    print("mean CER/WER per dataset")
    for dataset, pairs in sorted(group_lines.items()):
        mean_cer = statistics.mean(cer(gt, ocr) for gt, ocr in pairs)
        mean_wer = statistics.mean(wer(gt, ocr) for gt, ocr in pairs)
        print(dataset, "-", round(mean_cer, 4), "-", round(mean_wer, 4))

    print("\nerror dist")
    subs = dels = ins = 0
    for gt, ocr, _ in all_line_pairs:
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, gt, ocr).get_opcodes():
            if op == "replace":
                subs += max(i2 - i1, j2 - j1)
            elif op == "delete":
                dels += i2 - i1
            elif op == "insert":
                ins += j2 - j1
    total = subs + dels + ins
    print("subs", subs, round(subs / total, 3))
    print("dels", dels, round(dels / total, 3))
    print("ins", ins, round(ins / total, 3))

    print("\nsome examples")
    en_pairs = [
        (gt, ocr, rec)
        for gt, ocr, rec in all_line_pairs
        if rec["document_metadata"]["language"] == "en"
    ]
    shown = 0
    for gt, ocr, rec in sorted(en_pairs, key=lambda x: cer(x[0], x[1]), reverse=True):
        if shown >= 11:
            break
        if not any(is_hist_sensitive(tok) for tok in (gt + " " + ocr).split() if tok):
            continue
        meta = rec["document_metadata"]
        print(meta["primary_dataset_name"], meta["date"], "CER", round(cer(gt, ocr), 4))
        print("gt:", gt)
        print("ocr:", ocr)
        print()
        shown += 1


if __name__ == "__main__":
    main()
