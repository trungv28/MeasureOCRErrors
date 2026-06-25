# Notes

## Main idea

CER/WER don't capture which errors matter. Goal: measure how much each OCR error contributes to downstream task failure, and rank repairs by expected impact.

Test task: NER with HMBert.

---

## RQs

**RQ1.** Do CER/WER correlate with entity detection loss?

**RQ2.** Does the weighted damage score predict entity failure better than raw CER? Compare: record CER, mention CER, context CER, corruption-only, weighted damage. Metric: AUROC.

**RQ3.** Repair faithfulness: does ranking repairs by weighted damage recover entities faster? Metric: RepairAUC, K@0.8.

---

## Pipeline

**Step 1 — NER annotation on GT**
- Three annotators: GPT-4.1-mini, Llama-3.1-8B, GLiNER2
- Accept if ≥ 2/3 agree, same label, span overlap ≥ 0.8
- Labels: pers, org, loc, prod

**Step 2 — Project GT spans to OCR**
- Genalog NW alignment at line level, difflib fallback
- eval set = entities HMBert detects correctly on GT (clean ceiling)
- failed set = entities in eval set that fail on OCR

**Step 3 — Run HMBert on GT and OCR**
- Detection = span overlap ≥ 0.8 with correct label
- Outcomes per entity in eval set:
  - correct: detected with right label
  - miss: not detected
  - wrong type: detected with wrong label

Metrics:
- detection rate = correct / |eval set|
- miss rate = miss / |eval set|
- wrong-type rate = wrong type / |eval set|

**Step 4 — Corruption level per error span**

Align GT vs OCR with difflib word-level opcodes. One opcode block = one error span.

- corruption = Lev(gt, ocr) / max(|gt|, |ocr|)
- Multi-word blocks: join with space first
- 0 = unchanged, 1 = fully deleted

**Step 5 — Token importance (LIME/SHAP)**

For each entity in eval set: mask tokens in GT line with underscores (preserves char offsets), rerun HMBert, fit weighted ridge regression over N=30 samples.

**Step 6 — Weighted damage**

Per error span:
- impact = importance × corruption

Entity-level summary:
- damage score = Σ impact / Σ importance  — normalized so entity size doesn't inflate the score

**Step 7 — Repair trajectory (RQ3)**

For each entity in failed set:
1. Collect error spans in its line window
2. Rank by strategy: impact / corruption-only / importance-only / mention-first / random
3. Apply top-k repairs (replace OCR span with GT text), rerun HMBert at each k
4. recovery(k) = fraction of failed set recovered at budget k

RepairAUC = ∫ recovery(r) dr 
K@α = min k s.t. recovery(k) ≥ α × recovery(full)

---

## Results

**NER outcomes**

| type | eval | detection rate | miss rate | wrong-type rate |
|------|------|---------------|-----------|-----------------|
| pers | 872  | 0.968 | 0.019 | 0.013 |
| loc  | 1899 | 0.961 | 0.032 | 0.008 |
| org  | 129  | 0.814 | 0.093 | 0.093 |
| prod | 30   | 0.800 | 0.133 | 0.067 |
| time | 126  | 0.976 | 0.024 | 0.000 |
| **overall** | **3056** | **0.955** | **0.031** | **0.013** |


**RQ1: CER/WER vs entity loss rate**

| predictor | Spearman r | p |
|-----------|-----------|---|
| CER | 0.209 | 7.4e-4 |
| WER | 0.185 | 2.8e-3 |

CER bin:

| CER range | n docs | mean loss rate |
|-----------|--------|---------------|
| 0–5%   | 174 | 0.045 |
| 5–15%  | 79  | 0.071 |
| 15–30% | 5   | 0.125 |

Interpretation: statistically significant but practically weak (r ≈ 0.2).



**RQ2: predicting entity failure**

| predictor | AUROC | AP |
|-----------|-------|----|
| record CER | 0.587 | 0.085 |
| corruption | 0.668 | 0.099 |
| importance | 0.704 | 0.110 |
| mention CER | 0.721 | 0.140 |
| damage score | 0.745 | 0.162 |

Damage score beats all baselines.

**RQ3: Repair trajectory**

| strategy | RepairAUC | K@0.8 |
|----------|-----------|-------|
| mention-first | 0.954 | 1.10 |
| importance | 0.943 | 1.17 |
| impact | 0.931 | 1.17 |
| random | 0.844 | 1.72 |
| corruption | 0.762 | 1.59 |

This fail because the number of samples is very small for now (could add dev set ?)


## Further directions

**Entity linking**
- Outcomes: correct QID / NIL / wrong QID
- Need QID ground truth: entity-fishing + LLM verifier (≥2/3 agree on Wikidata QID)
- Importance target: LIME/SHAP on linker score for reference QID


**Retrieval (BM25)**
- Index GT and OCR separately, query = entity surface
- Recall@k(OCR) / Recall@k(GT)
- Per-term damage = BM25 contribution × corruption
