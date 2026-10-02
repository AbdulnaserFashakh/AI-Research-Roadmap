# S012 Full-Text Extraction Note

## Record Status

- Study ID: S012
- Screening decision: Included
- Extraction status: Full text extracted
- Extraction date: 2 October 2026
- Review status: Provisional AI-assisted extraction; human verification required before final synthesis
- Evidence stream: B — RAG and Scientific Question Answering

## Citation and Sources

Matos, J., Silva, C., and Gonçalo Oliveira, H. (2026). Benchmarking Retrieval-Augmented Generation for Scientific Knowledge QA in European Portuguese. In *Proceedings of the 3rd International Workshop on Natural Scientific Language Processing (NSLP 2026) at LREC 2026*, 25–31. ELRA Language Resources Association.

- DOI: https://doi.org/10.63317/3muergicuxwk
- ACL Anthology record: https://aclanthology.org/2026.nslp-1.3/
- Full text: https://aclanthology.org/2026.nslp-1.3.pdf
- Code, data, and results: https://github.com/NLP-CISUC/Benchmark-ScientificQA-RAG-pt-PT

## Why This Study Was Selected

This study is a close methodological predecessor for the planned project because it evaluates scientific RAG with open instruction-tuned small language models, compares language-specialized and multilingual dense retrievers, switches reranking on and off, and varies the amount of retrieved context.

It substantially narrows the novelty claim. Scientific RAG with 4–12B models and controlled retriever, reranker, and top-k comparisons is already demonstrated. The open space is the joint evaluation of Arabic questions over English scientific evidence, claim-level evidence sufficiency, open-ended grounded generation, citations, faithfulness, partial answering, abstention, and local operational cost.

## Research Question

The study asks:

> How does RAG improve European Portuguese scientific question answering across open instruction-tuned small language models, and how sensitive is it to retrieval setup choices?

The experiment is a controlled multiple-choice evaluation rather than an open-ended answer-generation benchmark.

## Data and Scientific Knowledge Base

| Element | Description |
| --- | --- |
| Evaluation dataset | Portuguese test split of Global MMLU Lite |
| Test size | 400 items per language in Global MMLU Lite; the Portuguese split is used |
| Translation status | Portuguese samples were professionally translated |
| Question categories | Humanities, STEM, Medical, Social Sciences, Business, and Other |
| External knowledge base | CorEGe-PT |
| Knowledge-base size | More than 32,000 open-access scientific documents in Portuguese |
| Document formats after preparation | Markdown |
| Source types | Materials ranging from book chapters to PhD theses |
| Scientific fields | Exact and Natural Sciences; Engineering and Technology; Medical and Health Sciences; Social Sciences; Humanities |

The questions and the retrieval corpus are both Portuguese. Therefore, the study evaluates language specialization within Portuguese, not cross-lingual Arabic-to-English retrieval.

## Models

Five non-quantized instruction-tuned models in the 4–12B range were evaluated:

- AMALIA 9B, specialized for European Portuguese;
- EuroLLM-9B-Instruct;
- Qwen3-8B;
- Gemma-3-4B-IT;
- Gemma-3-12B-IT.

The comparison between Gemma 4B and 12B holds the architecture family constant while varying model scale. Qwen3-8B was included partly because its pretraining reportedly contains five trillion high-quality STEM tokens.

## Retrieval and Reranking Pipeline

| Component | Setting |
| --- | --- |
| First chunking stage | Split by Markdown section headers |
| Second chunking stage | Recursive splitting into 500-character chunks |
| Chunk overlap | 50 characters |
| Vector store | ChromaDB |
| Similarity | Cosine similarity |
| Multilingual retriever | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`, 278M parameters |
| Portuguese-specific retriever | `PORTULAN/serafim-335m-portuguese-pt-sentence-encoder-ir`, 335M parameters |
| Candidate pool | Top 30 chunks precomputed per question and retriever |
| Retrieval query | Question stem |
| Context sizes | k ∈ {1, 3, 5, 10} |
| Reranker | `Alibaba-NLP/gte-multilingual-reranker-base` |
| Main conditions | Closed-book; retrieval; retrieval plus reranking |
| RAG configurations per generator | 16: two retrievers × four k values × reranking on/off |

The two retrievers have similar parameter counts, which helps isolate language specialization from model scale.

## Evaluation Protocol

- Framework: `lm_evaluation_harness`.
- Prompting: three-shot.
- Demonstrations: deterministic selection with a fixed seed.
- Scoring: log-likelihood of the multiple-choice options.
- Generation: no open-ended decoding.
- Controlled variables: the prompt format remains fixed while context presence, k, and reranking change.
- Hardware: one NVIDIA RTX A6000 GPU.
- Primary outcome: multiple-choice accuracy.
- Uncertainty: standard error is reported.
- Statistical comparisons: two-proportion Z test and McNemar test are reported for comparisons with the closed-book baseline; paired tests are also described across subcategories.

Because answers are selected by option log-likelihood, sampling parameters such as temperature do not affect the selected answer. This improves determinism but prevents evaluation of citation behavior, linguistic adherence in generated Arabic prose, and unsupported free-form claims.

## Main Accuracy Results

| Generator | Closed-book accuracy | Best retrieval accuracy | Best retrieval + reranking accuracy | Best change from closed book |
| --- | ---: | ---: | ---: | ---: |
| AMALIA | 63.0 ± 2.4 | 64.7 ± 2.4, Portuguese retriever, k=10 | 65.7 ± 2.4, Portuguese retriever, k=1 | +2.7 pp, not significant |
| EuroLLM-9B-Instruct | 62.0 ± 2.4 | 63.5 ± 2.4, Portuguese retriever, k=1 | 64.2 ± 2.4, Portuguese retriever, k=10 | +2.2 pp, not significant |
| Qwen3-8B | 73.0 ± 2.2 | 72.0 ± 2.2, multilingual retriever, k=3 | 71.8 ± 2.3, Portuguese retriever, k=1 | −1.0 pp, not significant |
| Gemma-3-4B-IT | 50.7 ± 2.5 | 60.3 ± 2.4, multilingual retriever, k=3 | 60.5 ± 2.4, multilingual retriever, k=5 | +9.8 pp, significant |
| Gemma-3-12B-IT | 55.5 ± 2.5 | 70.5 ± 2.3, Portuguese retriever, k=1 | 71.0 ± 2.3, Portuguese retriever, k=1 | +15.5 pp, significant |

Only the two Gemma models produced statistically significant gains over their closed-book baselines.

## Robustness Across All 16 RAG Configurations

| Generator | Worst change | Best change | Mean change ± SD |
| --- | ---: | ---: | ---: |
| AMALIA | −1.50 pp | +2.75 pp | +0.53 ± 1.30 pp |
| EuroLLM-9B-Instruct | −2.00 pp | +2.25 pp | +0.08 ± 1.04 pp |
| Qwen3-8B | −4.75 pp | −1.00 pp | −2.89 ± 1.18 pp |
| Gemma-3-4B-IT | +6.25 pp | +9.75 pp | +8.41 ± 1.08 pp |
| Gemma-3-12B-IT | +11.75 pp | +15.50 pp | +13.61 ± 1.08 pp |

Qwen3-8B had the strongest closed-book result, but every tested RAG configuration reduced its accuracy. This provides direct evidence that a strong base model can be harmed by retrieved context.

## Findings About Context Size, Retrieval, and Reranking

### Context Volume

Accuracy did not increase monotonically with k. Some models peaked at small contexts and then plateaued or declined as more chunks were added. The authors interpret this as a trade-off between useful evidence and retrieval noise.

### Retriever Specialization

Without reranking, the Portuguese-specific retriever often outperformed the multilingual retriever in Business, STEM, and Medical categories. The advantage was not universal and interacted with the knowledge domain and context size.

### Reranking

Reranking did not consistently improve accuracy. It sometimes moved the best-performing condition toward a smaller k, which may improve efficiency.

In technical domains, the fixed multilingual reranker could erase gains obtained from the Portuguese-specific retriever. The paper attributes this provisionally to language and domain mismatch between the specialized retriever and the general multilingual reranker. In Social Sciences, however, reranking corrected an initial retrieval disadvantage from −1.6 percentage points to a +1.4 percentage-point advantage.

The main design lesson is that reranking is not an automatically beneficial stage. Retriever–reranker language and domain alignment must be tested rather than assumed.

## Strengths

- Uses an open scientific corpus containing more than 32,000 documents.
- Evaluates five open instruction-tuned models in a controlled 4–12B range.
- Compares closed-book, retrieval, and retrieval-plus-reranking conditions.
- Uses a complete factorial grid over retriever type, k, and reranking.
- Keeps prompts and demonstrations fixed across conditions.
- Reports uncertainty, statistical tests, and robustness across all configurations rather than only the best setting.
- Releases code, data, and experimental results.
- Explicitly documents limitations and future work.

## Limitations and Threats to Validity

The following limitations are stated by the authors or arise relative to the proposed project:

- Global MMLU Lite is broad multiple-choice QA and may not represent scientific reasoning over documents.
- Portuguese evaluation resources are limited.
- The Portuguese questions may contain Brazilian Portuguese bias despite the European Portuguese target.
- Retrieval quality is not evaluated directly at the chunk level; answer accuracy is used as a proxy.
- Only one chunking strategy is evaluated.
- The study does not generate open-ended answers.
- It does not evaluate explicit citations, citation coverage, claim-level faithfulness, partial answering, or abstention.
- It does not control complete, partial, absent, ambiguous, and distractor-rich evidence conditions.
- Questions and documents are both Portuguese, so no cross-lingual retrieval condition is present.
- Experiments use non-quantized models on an RTX A6000; consumer-hardware latency and memory trade-offs are not reported.
- Qwen3-4B is not included as an additional small-model comparison.

## Relationship to the Proposed Study

### Direct Overlap

S012 already covers:

- scientific RAG;
- small open instruction-tuned generators;
- multilingual versus language-specialized dense retrieval;
- reranking on versus off;
- k sensitivity;
- model-dependent effects of retrieved context;
- statistical comparison with closed-book baselines.

These elements cannot be claimed as standalone novelty in the proposed study.

### Research Space Still Open

S012 does not jointly evaluate:

- Arabic questions retrieving English scientific documents;
- direct Arabic multilingual retrieval versus translated English retrieval;
- claim-level gold evidence groups;
- micro claim coverage and complete evidence rate;
- open-ended Arabic answers;
- answer correctness together with citation correctness and coverage;
- claim-level faithfulness;
- controlled complete, partial, absent, ambiguous, and distractor-rich evidence;
- partial answering and calibrated abstention;
- Arabic response-language adherence;
- a quantized local generator and consumer-hardware latency.

The defensible contribution is therefore not another component benchmark. It is a controlled connection between cross-lingual retrieval decisions, claim-level evidence sufficiency, and downstream answer trustworthiness under open-ended generation.

## Design Elements to Reuse

- Include a closed-book baseline where scientifically meaningful.
- Test more than one k because context volume can help or harm depending on the generator.
- Report the distribution of changes across all configurations, not only the best result.
- Treat the generator as an experimental factor or explicitly limit conclusions to the selected local model.
- Compare matched and mismatched retriever–reranker language/domain settings.
- Fix prompts, demonstrations, seeds, and generation parameters across retrieval conditions.
- Use paired statistical comparisons and confidence intervals.
- Measure retrieval quality directly rather than using downstream answer accuracy as its proxy.

## Implications for Current Research Questions and Hypotheses

| Proposed question or hypothesis | Evidence from S012 |
| --- | --- |
| RQ1: retrieval and reranking effects on evidence coverage | S012 tests retriever, reranker, and k effects, but it does not measure chunk relevance or claim-level evidence coverage directly. |
| RQ2: retrieval gains versus answer trustworthiness | Strong motivation: more context and reranking do not guarantee higher answer accuracy. Citations and faithfulness remain untested. |
| RQ3/RQ4: incomplete evidence and abstention | Not evaluated because the benchmark uses multiple-choice questions and no controlled answerability conditions. |
| RQ5: small local model quality–latency trade-off | Model size is compared, but experiments use non-quantized models on an RTX A6000 and do not report consumer-local latency. |
| H2: higher retrieval recall does not always improve answer quality | Plausible and strengthened, although retrieval recall itself was not measured. Larger k sometimes reduced accuracy. |
| H3: reranking can help or harm depending on evidence and mismatch | Strengthened. Reranking was inconsistent and could erase specialized-retriever gains. |
| H4: language/domain-aligned reranking should outperform a mismatched reranker | Strongly motivated but not directly tested because only one fixed multilingual reranker was used. |
| H5: claim-level sufficiency predicts answer quality better than document hit rate | Still open. S012 explicitly lacks direct chunk-level retrieval evaluation and uses task accuracy as a proxy. |

## Provisional Quality Appraisal

Scoring follows the review protocol: 0 = not reported, 1 = partially reported, and 2 = clearly reported.

| Criterion | Score | Rationale |
| --- | ---: | --- |
| Clear research objective | 2 | The scientific QA question and retrieval-sensitivity objective are explicit. |
| Transparent dataset description | 2 | The benchmark split, translation status, categories, corpus scale, document types, and scientific fields are reported. |
| Reproducible methodology | 2 | Models, chunking, retrievers, reranker, k values, prompt control, framework, hardware, and repository are reported. |
| Appropriate baseline comparison | 2 | Closed-book and 16 factorial RAG configurations are compared for each generator. |
| Suitable evaluation metrics | 1 | Accuracy is suitable for the multiple-choice task, but retrieval quality is not measured directly despite retrieval-focused conclusions. |
| Human evaluation when required | 2 | Human evaluation is not required for deterministic scoring against gold multiple-choice labels. |
| Statistical analysis | 2 | Standard errors, significance thresholds, two-proportion Z testing, McNemar testing, and paired subcategory comparisons are reported. |
| Error analysis | 2 | Results are decomposed by generator, configuration, k, domain, retriever specialization, and reranking behavior. |
| Code or data availability | 2 | Code, data, and results are released. |
| Limitations and threats to validity | 2 | The paper explicitly discusses benchmark, language-variety, retrieval-evaluation, chunking, open-generation, and model-coverage limitations. |
| **Total** | **19/20** | **High quality, provisional pending independent human verification.** |

## Extraction Boundary

Numerical results and descriptions of the study above are extracted from the paper. Statements about novelty, transfer to Arabic–English scientific RAG, proposed hypotheses, and additional untested dimensions are reviewer interpretations and must not be attributed to Matos et al.
