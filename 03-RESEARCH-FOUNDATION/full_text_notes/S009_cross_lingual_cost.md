# S009 Full-Text Extraction Note

## Record Status

- Study ID: S009
- Screening decision: Included
- Extraction status: Full text extracted
- Extraction date: 2 October 2026
- Review status: Provisional AI-assisted extraction; human verification required before final synthesis
- Evidence stream: C — Cross-Lingual Retrieval

## Citation and Sources

Amiraz, C., Fyodorov, Y., Haramaty, E., Karnin, Z., and Lewin-Eytan, L. (2025). The Cross-Lingual Cost: Retrieval Biases in RAG over Arabic-English Corpora. In *Proceedings of the Third Arabic Natural Language Processing Conference*, 69–83. Association for Computational Linguistics.

- DOI: https://doi.org/10.18653/v1/2025.arabicnlp-main.6
- ACL Anthology record: https://aclanthology.org/2025.arabicnlp-main.6/
- Full text: https://aclanthology.org/2025.arabicnlp-main.6.pdf
- Code and data: https://github.com/chenamiraz/cross-lingual-cost

## Why This Study Was Selected

This is a direct predecessor for the proposed Arabic-question and English-document scientific RAG study. It isolates Arabic–English retrieval behavior in domain-specific corpora, evaluates the complete retrieval–reranking–generation pipeline, and compares direct multilingual retrieval with query translation and language-balanced retrieval.

It does not, however, study scientific literature, small local generators, claim-level evidence sufficiency, citation quality, faithfulness, or abstention. Those omissions define part of the space addressed by the proposed study.

## Research Problem

The paper argues that multilingual RAG studies based mainly on Wikipedia can conceal retrieval failures because:

- English is overrepresented.
- Wikipedia-like content may overlap with retriever and generator pretraining.
- a generator may answer from parametric memory rather than retrieved evidence.

The study therefore asks how Arabic–English retrieval behaves in domain-specific bilingual corpora when the query language and the supporting-document language are controlled independently.

## Experimental Pipeline

The evaluated pipeline has three stages:

1. Dense retrieval from a mixed Arabic–English corpus.
2. Cross-encoder reranking.
3. Answer generation in the same language as the user question.

Configuration:

| Component | Setting |
| --- | --- |
| Dense retrievers | BAAI BGE-M3 and Multilingual-E5-Large |
| Embedding dimension | 1,024 for both retrievers |
| Chunking | LlamaIndex SentenceSplitter, maximum 100 tokens, no overlap |
| Preserved metadata | Original document title retained in every passage |
| Retrieval depth | Top 20 passages |
| Reranker | BGE-reranker-v2-m3 |
| Generation context | Top 5 reranked passages |
| Generator | Qwen-2.5-14B-Instruct |
| Required answer language | Same language as the question |

## Benchmarks

The authors built two benchmarks from public UAE websites containing parallel Arabic and English documents.

| Benchmark | Source | Corpus scale | Final QA distribution |
| --- | --- | --- | --- |
| Legal | UAE Legislation website; 390 laws | Approximately 1.5 million words | 1,282 QA pairs |
| Travel | UAE Ministry of Foreign Affairs travel pages | Approximately 150,000 words | 1,923 QA pairs |

For each parallel document pair, exactly one language version was retained, selected uniformly at random. DataMorgana generated single-turn question–answer pairs that could be answered from one document. Query language was also sampled independently and uniformly, producing four query–document language combinations.

Exact benchmark counts:

| Benchmark | English query / English document | English query / Arabic document | Arabic query / English document | Arabic query / Arabic document |
| --- | ---: | ---: | ---: | ---: |
| Legal | 318 | 337 | 324 | 303 |
| Travel | 513 | 471 | 479 | 460 |

The question-generation configuration also varied formulation, linguistic similarity, question type, and user need. Questions were balanced between factoid and open-ended types and between Arabic-grounded and English-grounded documents.

## Evaluation Metrics

The study evaluates each pipeline stage and the complete system:

- Retrieval Hit@20: whether at least one passage containing the answer appears among the top 20.
- Reranking Hit@5: whether a relevant passage remains in the top 5, calculated only after successful retrieval.
- Conditional generation accuracy: answer accuracy calculated only after successful reranking.
- End-to-end answer accuracy.
- NDCG@20 and MRR@20 as additional ranking metrics.

Claude 3.5 Sonnet assigns passage relevance and judges semantic equivalence between predicted and reference answers. Results are reported with 95% confidence intervals.

## Main End-to-End Results

| Benchmark | Retriever | Hit@20 | Conditional Hit@5 | Conditional generation accuracy | End-to-end accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| Legal | BGE-M3 | 81±2% | 88±2% | 78±3% | 58±3% |
| Legal | Multilingual-E5-Large | 66±3% | 87±2% | 78±3% | 48±3% |
| Travel | BGE-M3 | 89±1% | 97±1% | 87±2% | 79±2% |
| Travel | Multilingual-E5-Large | 76±2% | 97±1% | 85±2% | 67±2% |

The no-RAG accuracies were 27±3% for Legal and 37±3% for Travel.

### Interpretation Reported by the Authors

Reranking and conditional generation remained similar across the two embedders, while retrieval changed substantially. The retriever was therefore the principal bottleneck in this experimental setting.

## Language-Combination Results

### BGE-M3

| Benchmark | Query → document | Hit@20 | End-to-end accuracy |
| --- | --- | ---: | ---: |
| Legal | Arabic → Arabic | 92±3% | 68±5% |
| Legal | Arabic → English | 90±3% | 67±5% |
| Legal | English → Arabic | 56±5% | 31±5% |
| Legal | English → English | 86±4% | 68±5% |
| Travel | Arabic → Arabic | 93±2% | 85±3% |
| Travel | Arabic → English | 91±3% | 78±4% |
| Travel | English → Arabic | 80±4% | 70±4% |
| Travel | English → English | 94±2% | 84±3% |

### Multilingual-E5-Large

| Benchmark | Query → document | Hit@20 | End-to-end accuracy |
| --- | --- | ---: | ---: |
| Legal | Arabic → Arabic | 87±4% | 67±5% |
| Legal | Arabic → English | 51±5% | 37±5% |
| Legal | English → Arabic | 41±5% | 22±4% |
| Legal | English → English | 88±4% | 70±5% |
| Travel | Arabic → Arabic | 90±3% | 86±3% |
| Travel | Arabic → English | 54±4% | 37±4% |
| Travel | English → Arabic | 64±4% | 60±4% |
| Travel | English → English | 95±2% | 85±3% |

Cross-language degradation exceeded 40 percentage points in some conditions. BGE-M3 displayed an asymmetric weakness, especially for English queries retrieving Arabic documents. Multilingual-E5-Large degraded in both cross-language directions.

## Failure-Source Experiment

The paper separates two possible causes:

1. Query–document mismatch: representing a query and a relevant passage written in different languages.
2. Document–document mismatch: comparing and ranking candidate passages written in different languages within one result list.

A language-oracle retriever searched only the known language of the ground-truth document. Its performance was nearly equal across language pairs. The authors therefore attribute most failure to cross-language ranking among documents, rather than to the query–document semantic match alone.

This distinction is important for the proposed study: a multilingual embedding score may not be calibrated comparably across Arabic and English candidate pools, even when individual cross-language pairs are semantically represented well.

## Mitigation Experiments

The paper compares two practical interventions:

- Translation: translate the query into the other language, retrieve once per language, merge the lists by retrieval score, and retain the top 20.
- Balanced retrieval: retrieve 10 Arabic and 10 English passages separately.

Both improved cross-language retrieval without a statistically significant loss in same-language cases. Overall retrieval gains were approximately 4–6 percentage points for BGE-M3 and approximately 20 points for Multilingual-E5-Large. The two interventions were not statistically distinguishable in the reported experiments.

Balanced retrieval avoids the external latency and cost of machine translation. In an additional Travel experiment with 25%, 50%, and 75% English documents, equal balanced retrieval remained stable and competitive with a corpus-proportion-weighted alternative.

## Validation of Automated Judging

The answer-accuracy judge was checked using separate 100-item English and 100-item Arabic samples. Native speakers judged whether generated and reference answers matched and marked debatable cases.

- Non-debatable items represented 80% of both language samples.
- Agreement on non-debatable cases was 95% for English and 98% for Arabic.
- Overall agreement was 82% for English and 85% for Arabic.

The retrieval metric also showed strong downstream separation on the Legal benchmark. When Hit@20 was zero, end-to-end accuracy was 10±3% for BGE-M3 and 9±2% for Multilingual-E5-Large. When Hit@20 was one, both reached 79% conditional end-to-end accuracy.

## Strengths

- Directly controls the query and supporting-document languages.
- Uses domain-specific corpora rather than only Wikipedia-derived data.
- Separates retrieval, reranking, conditional generation, and end-to-end failure.
- Includes an oracle experiment that identifies the source of retrieval failure.
- Reports 95% confidence intervals and supplementary ranking metrics.
- Validates automated answer judgments with Arabic and English native speakers.
- Releases code, corpora, and benchmark records.

## Limitations and Threats to Validity

Some limitations are stated by the authors; others below are limitations relative to the proposed study.

- Only Arabic and English are evaluated.
- The domains are legal and travel information, not scientific literature.
- Questions are synthetically generated and single-turn.
- Every question is designed to be answerable from one source document.
- The generator is Qwen-2.5-14B-Instruct, not a small 4B-class local model.
- Passage relevance and answer correctness rely heavily on one proprietary LLM judge, although sampled human validation is reported.
- The paper does not evaluate explicit answer citations, citation coverage, or claim-level faithfulness.
- Partial evidence, deliberately unanswerable questions, ambiguity, and distractor-rich evidence groups are not systematically controlled.
- Abstention and false-abstention behavior are not evaluated.
- Translation uses an external Google Translate call, so its latency and cost do not represent a fully local system.
- The paper identifies non-uniform language distributions and corpora with more than two languages as open challenges.

## Relationship to the Proposed Study

### Boundary of Transfer to an English-Only Scientific Corpus

The paper's largest failure source was ranking Arabic and English candidates together. The proposed study currently targets Arabic questions over predominantly English scientific documents. In that setting, the document–document language mismatch may be absent because all candidates are English.

Consequently, S009 does **not** establish that query translation will outperform direct Arabic multilingual retrieval in the proposed corpus. It instead creates a sharper empirical question: once mixed-language score calibration is removed, how much cross-language cost remains at the Arabic-query-to-English-document matching stage, and does translation or reranking improve claim-level evidence sufficiency?

### Design Elements to Reuse

- Report results separately for every query–document language combination.
- Treat retrieval, reranking, and generation as separate conditional stages.
- Include a direct multilingual baseline, a translation baseline, and an oracle evidence condition.
- Report both component-level and end-to-end results.
- Preserve a local-cost comparison because translation and reranking add different operational costs.
- Use confidence intervals and paired comparisons.

Language-balanced retrieval should be included only if the experimental corpus contains both Arabic and English documents. It is not a meaningful main baseline for an English-only scientific corpus.

### Research Space Still Open

The paper provides strong evidence that cross-language retrieval is a bottleneck, but it does not answer whether retrieval improvements produce trustworthy scientific answers. The proposed study extends this question by jointly measuring:

- claim-level evidence coverage;
- complete evidence retrieval;
- answer correctness;
- citation correctness and citation coverage;
- faithfulness to the retrieved evidence;
- partial answering and abstention;
- Arabic response-language adherence;
- latency and local resource requirements for a small open-weight generator.

The defensible novelty claim is therefore not merely that Arabic–English retrieval is difficult. That is already demonstrated. The candidate contribution is a controlled link between **cross-lingual retrieval choices**, **claim-level evidence sufficiency**, and **downstream trustworthiness** in scientific RAG with a small local model.

## Implications for the Current Research Questions

| Proposed question or hypothesis | Evidence from S009 |
| --- | --- |
| RQ1: retrieval and reranking effects on evidence coverage | Strong motivation, but S009 uses passage Hit@k rather than claim-level evidence coverage. |
| RQ2: retrieval gains versus answer trustworthiness | It connects Hit@20 to answer accuracy, but does not evaluate citations or claim-level faithfulness. |
| RQ3/RQ4: incomplete, absent, or ambiguous evidence and abstention | Not systematically studied. This remains open. |
| RQ5: small local model quality–latency trade-off | Not studied; the generator is 14B and translation uses an external service. |
| H1: translated English retrieval improves over direct Arabic retrieval | Not established. S009 locates most failure in mixed-language candidate ranking, which may be absent in an English-only corpus. Translation must remain an empirical comparison rather than an assumed improvement. |
| H5: claim-level sufficiency predicts answer quality better than document hit rate | Not tested. S009 motivates the question by showing that Hit@20 is informative but coarse. |

## Provisional Quality Appraisal

Scoring follows the review protocol: 0 = not reported, 1 = partially reported, and 2 = clearly reported.

| Criterion | Score | Rationale |
| --- | ---: | --- |
| Clear research objective | 2 | The cross-lingual retrieval question and four experiments are explicit. |
| Transparent dataset description | 2 | Sources, construction, language randomization, scale, and final counts are reported. |
| Reproducible methodology | 2 | Models, chunking, top-k settings, prompts, and released repository are reported. |
| Appropriate baseline comparison | 2 | No-RAG, two embedders, direct, oracle, translation, and balanced retrieval are compared. |
| Suitable evaluation metrics | 2 | Component-level, end-to-end, Hit@k, NDCG, and MRR metrics are used. |
| Human evaluation when required | 1 | Native-speaker validation is useful, but independent reviewer structure and agreement between multiple human reviewers are not fully described. |
| Statistical analysis | 1 | Confidence intervals and significance conclusions are reported, but the main text does not fully specify the statistical testing procedure. |
| Error analysis | 2 | The oracle experiment isolates document-ranking failure from query–document mismatch. |
| Code or data availability | 2 | The benchmark, corpora, and code repository are linked. |
| Limitations and threats to validity | 1 | Some open challenges are stated, but several relevant threats require reviewer inference. |
| **Total** | **17/20** | **High quality, provisional pending independent human verification.** |

## Extraction Boundary

All numerical results and descriptions of the study above are extracted from the paper. Statements about relevance to the proposed project, untested metrics, and candidate novelty are reviewer interpretations and must not be attributed to Amiraz et al.
