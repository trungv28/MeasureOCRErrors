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

**Step 1 - NER annotation on GT**
- Three annotators: GPT-4.1-mini, Llama-3.1-8B, GLiNER2
- Accept if 2/3 agree, same label, span overlap >= 0.8
- Labels: pers, org, loc, prod

**Step 2 - Project GT spans to OCR**
- Genalog NW alignment at line level, difflib fallback
- eval set = entities HMBert detects correctly on GT (clean ceiling)
- failed set = entities in eval set that fail on OCR

**Step 3 - Run HMBert on GT and OCR**
- Detection = span overlap >= 0.8 with correct label
- Outcomes per entity in eval set:
  - correct: detected with right label
  - miss: not detected
  - wrong type: detected with wrong label

Metrics:
- detection rate = correct / |eval set|
- miss rate = miss / |eval set|
- wrong-type rate = wrong type / |eval set|

**Step 4 - Corruption level per error span**

Align GT vs OCR with difflib word-level opcodes. One opcode block = one error span.

- corruption = Lev(gt, ocr) / max(|gt|, |ocr|)
- Multi-word blocks: join with space first
- 0 = unchanged, 1 = fully deleted

**Step 5 - Token importance (LIME/SHAP)**

For each entity in eval set: mask tokens in GT line with underscores (preserves char offsets), rerun HMBert, fit weighted ridge regression over N=30 samples.

**Step 6 - Weighted damage**

Per error span:
- impact = importance * corruption

Entity-level summary:
- damage score = sum(impact) / sum(importance)

**Step 7 - Repair trajectory (RQ3)**

For each entity in failed set:
1. Collect error spans in its line window
2. Rank by strategy: impact / corruption-only / importance-only / mention-first / random
3. Apply top-k repairs (replace OCR span with GT text), rerun HMBert at each k
4. recovery(k) = fraction of failed set recovered at budget k

RepairAUC = integral of recovery(r) dr
K@a = min k s.t. recovery(k) >= a * recovery(full)

**Entity linking annotation pipeline**

For each projected consensus entity with label pers/loc/org/prod, a candidate QID pool is built from three sources:

1. **entity-fishing**: forced-span disambiguation with nbest=true, returning multiple scored Wikidata candidates per entity
2. **Wikidata search API** (wbsearchentities): surface-form search, high recall
3. **Wikidata reconciliation API** (wikidata.reconci.link): type-aware matching with type hints (Q5=person, Q2221906=location, Q43229=org)

Candidates from all three sources are deduplicated by QID and merged into a single pool.

Two LLM verifiers independently select one QID from the pool given the entity mention, its label, and sentence context:
- GPT-4.1-mini: structured output (Pydantic), temperature 0
- Llama-3.1-8B-Instruct: vllm batch inference, temperature 0

2/2 agreement on the same QID = accepted reference QID. Both output NIL = NIL. Disagreement = excluded from reference set.

**Retrieval annotation pipeline**

We could use Entity link to annotate the retrieval.

- Consider 1 sentence as 1 unit to retrieve.
- For each sentence containing >= 2 entity with linking, extract it and create query from the pair of entities.
- All sentences containing the entity ID from the query will be considered relevant.
- The query (input) to the model will be the concatenation of canonical entity names 


---

## Results

**NER outcomes (test set)**

HMBert precision against projected consensus annotations on GT and OCR text (span overlap >= 0.8, exact label match). Recall not reported since the consensus set is incomplete by design (>=2/3 agreement only).

| label | GT P | OCR P |
|-------|------|-------|
| pers  | 0.580 | 0.564 |
| loc   | 0.611 | 0.606 |
| org   | 0.385 | 0.357 |
| prod  | 0.222 | 0.237 |
| time  | 0.496 | 0.504 |
| **total** | **0.573** | **0.565** |

NEF (entity retention) = fraction of eval set entities still correctly detected on OCR. eval set = entities correctly detected on GT. entity_loss = miss + label_err.

| label | n (eval) | NEF | miss | label_err | entity_loss |
|-------|----------|-----|------|-----------|-------------|
| pers  | 872  | 0.968 | 0.019 | 0.013 | 0.032 |
| loc   | 1899 | 0.961 | 0.032 | 0.008 | 0.039 |
| org   | 129  | 0.814 | 0.093 | 0.093 | 0.186 |
| prod  | 30   | 0.800 | 0.133 | 0.067 | 0.200 |
| time  | 126  | 0.976 | 0.024 | 0.000 | 0.024 |
| **total** | **3056** | **0.955** | **0.031** | **0.013** | **0.045** |


**RQ1: CER/WER vs entity loss rate (test, n=437 docs, all datasets)**

| predictor | Spearman r | p |
|-----------|-----------|---|
| CER | 0.165 | 5.4e-4 |
| WER | 0.141 | 3.2e-3 |

CER bin:

| CER range | n docs | mean loss rate |
|-----------|--------|---------------|
| 0-5%   | 331 | 0.040 |
| 5-15%  | 102 | 0.072 |
| 15-30% |   4 | 0.156 |

Statistically significant but practically weak (r ~= 0.17).


**RQ2: predicting entity failure (test, n=3056, failed=136)**

Attribution computed with NLTK sentence-level context.

| predictor | AUROC | AP |
|-----------|-------|----|
| record CER | 0.637 | 0.072 |
| corruption | 0.614 | 0.059 |
| importance | 0.715 | 0.100 |
| mention CER | **0.735** | **0.124** |
| damage score | 0.726 | 0.100 |

Mention CER beats damage score on both AUROC and AP. Damage score is best among attribution-based metrics (0.726 > importance 0.715 > corruption 0.614).


**RQ3: Repair trajectory (test, n=61 entities in E^loss with edit units)**

| strategy | RepairAUC | K@0.8 | K@0.9 |
|----------|-----------|-------|-------|
| mention_first | 0.869 | 1.61 | 1.61 |
| AWD (impact) | 0.838 | 1.67 | 1.67 |
| A (importance) | 0.835 | 1.72 | 1.72 |
| D (corruption) | 0.766 | 1.98 | 1.98 |
| random | 0.766 | 2.49 | 2.67 |

AWD outperforms D and A in isolation. mention_first is strongest. n=61 is small; could include dev set.


**IAA: inter-annotator agreement (test, n=550 docs)**

Pairwise span F1 (overlap >= 0.8, same label):

| pair | overall | pers | loc | org | prod | time |
|------|---------|------|-----|-----|------|------|
| GPT vs Llama | 0.606 | 0.700 | 0.672 | 0.411 | 0.388 | 0.415 |
| GPT vs GLiNER | 0.595 | 0.623 | 0.715 | 0.394 | 0.030 | 0.618 |
| Llama vs GLiNER | 0.501 | 0.591 | 0.586 | 0.252 | 0.007 | 0.420 |

Consensus rate (>=2/3 agree):

| label | rate | consensus | total |
|-------|------|-----------|-------|
| pers | 0.540 | 1918 | 3555 |
| loc | 0.653 | 2388 | 3659 |
| org | 0.322 | 595 | 1846 |
| prod | 0.232 | 217 | 937 |
| time | 0.527 | 453 | 860 |
| **overall** | **0.513** | **5571** | **10857** |

GLiNER nearly ignores prod (F1 ~= 0.03 vs both others).


## Further directions

**Retrieval (BM25)**
- Index GT and OCR separately, query = entity surface
- Recall@k(OCR) / Recall@k(GT)
- Per-term damage = BM25 contribution * corruption
