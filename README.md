# Measuring Historical Information Loss due to OCR Errors in Digitized Newspapers

## 1. Introduction
With the ever-increasing pace of technology, the digitization of historical archives has
experienced a drastic upward trend that profoundly affects the accessibility and long-term
preservation of these documents. Billions of images regarding manuscripts, newspapers, or
old journals have been recorded during this huge revolution in digitization. Through Optical Character Recognition (OCR), scanned newspaper images can be transformed into machine-readable text, allowing researchers to search and analyze large collections more efficiently. However, evaluating OCR quality remains challenging. Common metrics such as Character Error Rate (CER) mainly measure character-level differences between OCR output and reference text, but they do not show how errors affect historically important information such as names, places, organizations, or dates. Therefore, this project views OCR errors not only as technical mismatches, but also as potential losses of historical information, and explores whether named-entity-based analysis can provide a more meaningful way to assess OCR quality. 

Specifically, this project seeks to answer the following **Research Questions (RQs)**:
*   **RQ1 (Named Entity Impact):** Do OCR errors disproportionately affect named entities (persons, places, dates, organisations) compared to common words?
*   **RQ2 (CER vs. Historical Loss):** How well does character-level accuracy (CER/WER) reflect the actual loss of historically meaningful information. Do texts with equal CER always suffer equal historical damage?
*   **RQ3 (Interpretable Measure):** Can we propose a simple, interpretable measure of historical information loss that captures what CER and WER miss?

## 2. Some Examples

The core problem is that CER treats all characters equally so an error in a person's name or a date carries the same weight as an error in a common word. Here we have some qualitative examples from dta19 (en) showing that even low CER does not mean it's a good example where it directly damage crucial historical information

**Date corrupted (CER 0.059)**
```
gt: WAR-OFFICE, March 26, 1805...
ocr: WAR-OFFICE, March 20, 1803...
```

**Newspaper name wrong (CER 0.051)**
```
gt: SAYS the Memphis Avalanche. : For ...
ocr: SAT8 the MemphiH Avalanrhr. : For ...
```

**Person names damaged (CER 0.152)**
```
gt: Edward Juleane, stealing in a dwelling, William
ocr: Ldwird Julcano. stealing In a dwelling, winiam
```

**Institution name wrong (CER 0.217)**
```
gt: THE CONCILIATION AND ARBITRATION ACT.
ocr: TSE CONCILIATION ANV ARM11U TION ACT.
```

## 3. Base Dataset Statistics

Mean CER and WER per dataset:

| dataset | CER | WER |
|---|---|---|
| dta19 (de) | 0.036 | 0.195 |
| icdar2017 (en) | 0.043 | 0.180 |
| icdar2017 (fr) | 0.040 | 0.167 |
| impresso-nzz (de) | 0.061 | 0.248 |
| impresso-snippets (de) | 0.043 | 0.293 |
| impresso-snippets (en) | 0.032 | 0.127 |
| impresso-snippets (fr) | 0.035 | 0.256 |
| overproof-combined (en) | 0.087 | 0.311 |

Error type distribution:

| type | count | percent |
|---|---|---|
| substitutions | 95608 | 81% |
| deletions | 9303 | 7.9% |
| insertions | 12936 | 11% |
