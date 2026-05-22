import difflib
import statistics
from collections import defaultdict
from jiwer import cer, wer
from data import label, load

def word_diff(gt, ocr):
    matcher = difflib.SequenceMatcher(None, gt.split(), ocr.split())
    return [
        (op, ' '.join(gt.split()[i1:i2]), ' '.join(ocr.split()[j1:j2]))
        for op, i1, i2, j1, j2 in matcher.get_opcodes()
        if op != 'equal'
    ]

def is_hist_sensitive(token):
    return token and (token[0].isupper() or any(c.isdigit() for c in token))

def first_diff_line(gt, ocr):
    for gt_line, ocr_line in zip(gt.split('\n'), ocr.split('\n')):
        if gt_line.strip() != ocr_line.strip():
            return gt_line, ocr_line
    return gt.split('\n')[0], ocr.split('\n')[0]


def main():
    records = [
        rec for rec in load('train')
        if rec['ground_truth']['transcription_unit']
        and rec['ocr_hypothesis']['transcription_unit']
    ]

    groups = defaultdict(list)
    for rec in records:
        groups[label(rec)].append(rec)

    print('mean CER/WER')
    for dataset, recs in sorted(groups.items()):
        gt_texts  = [rec['ground_truth']['transcription_unit'] for rec in recs]
        ocr_texts = [rec['ocr_hypothesis']['transcription_unit'] for rec in recs]
        mean_cer = statistics.mean(cer(gt, ocr) for gt, ocr in zip(gt_texts, ocr_texts))
        mean_wer = statistics.mean(wer(gt, ocr) for gt, ocr in zip(gt_texts, ocr_texts))
        print(f'{dataset} - {mean_cer} - {mean_wer}')

    print('\nerror dist')
    subs = dels = ins = 0
    for rec in records:
        gt = rec['ground_truth']['transcription_unit']
        ocr = rec['ocr_hypothesis']['transcription_unit']
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, gt, ocr).get_opcodes():
            if op == 'replace':
                subs += max(i2 - i1, j2 - j1)
            elif op == 'delete':
                dels += i2 - i1
            elif op == 'insert':
                ins += j2 - j1
    print(f'subs {subs}')
    print(f'dels {dels}')
    print(f'ins {ins}')

    print('\nsome examples')
    en_records = [rec for rec in records if rec['document_metadata']['language'] == 'en']
    shown = 0
    for rec in sorted(en_records, key=lambda rec: cer(rec['ground_truth']['transcription_unit'], rec['ocr_hypothesis']['transcription_unit']), reverse=True):
        if shown >= 11:
            break
        gt_text = rec['ground_truth']['transcription_unit']
        ocr_text = rec['ocr_hypothesis']['transcription_unit']
        hist_diffs = [
            (op, gt_tok, ocr_tok) for op, gt_tok, ocr_tok in word_diff(gt_text, ocr_text)
            if any(is_hist_sensitive(tok) for tok in (gt_tok + ' ' + ocr_tok).split() if tok)
        ]
        if not hist_diffs:
            continue
        meta = rec['document_metadata']
        rec_cer = cer(gt_text, ocr_text)
        print(meta['primary_dataset_name'], meta['language'], 'CER', rec_cer)
        gt_line, ocr_line = first_diff_line(gt_text, ocr_text)
        print('gt:', gt_line)
        print('ocr:', ocr_line)
        print('-' * 11)
        shown += 1


if __name__ == '__main__':
    main()
