# Research Direction Version 1

## Working Title

Evidence Sufficiency and Trustworthiness in Arabic to English Scientific RAG Using Small Local Language Models

## Research Context

Arabic-speaking researchers often formulate questions in Arabic while the relevant scientific literature is predominantly written in English.

Cross-lingual RAG research has examined multilingual retrieval, query translation and generation across languages. Arabic RAG research has also compared embedding models, rerankers and language models.

Scientific RAG studies have evaluated retrieval and reranking over scholarly corpora. Other studies have separately examined citation quality, faithfulness and abstention.

However, these areas are usually evaluated separately.

## Preliminary Research Gap

Based on the reviewed literature, limited evidence is available on how retrieval and reranking strategies affect claim-level evidence sufficiency and downstream trustworthiness in Arabic to English scientific RAG using small local language models.

The missing joint evaluation includes:

- Claim-level evidence coverage
- Complete evidence retrieval
- Answer correctness
- Citation correctness and coverage
- Faithfulness to retrieved evidence
- Partial answering and abstention
- Arabic response-language adherence
- Local computational cost

This gap statement is provisional and must be validated through a structured literature review.

## Main Research Question

How do cross-lingual retrieval and reranking strategies affect evidence sufficiency and answer trustworthiness in Arabic to English scientific RAG using a small local language model?

## Research Questions

### RQ1

How do direct Arabic retrieval, English query translation and reranking affect claim-level evidence coverage and complete evidence rate?

### RQ2

Do improvements in retrieval performance translate into improvements in answer correctness, citation correctness and faithfulness?

### RQ3

How do the evaluated configurations behave when the available evidence is complete, partial, absent or ambiguous?

### RQ4

How accurately does the system provide partial answers or abstain when the retrieved context is insufficient?

### RQ5

What quality and latency trade-offs arise when the system operates with a small local language model?

## Preliminary Hypotheses

### H1

English query translation followed by reranking will improve complete evidence retrieval compared with direct Arabic dense retrieval.

### H2

Higher retrieval recall will not always produce higher citation correctness or answer correctness.

### H3

Reranking will improve answers when sufficient evidence exists but may increase unsupported answers when retrieved evidence is plausible yet incomplete.

### H4

A reranker aligned with the language and scientific domain will outperform an English general-domain MS MARCO reranker.

### H5

Claim-level evidence sufficiency will predict downstream answer quality better than document-level hit rate alone.

## Planned Retrieval Conditions

- Direct Arabic query with multilingual dense retrieval
- Arabic question translated into English before dense retrieval
- Translated query with English cross-encoder reranking
- Direct Arabic query with multilingual reranking
- Oracle evidence condition

## Planned Evidence Conditions

- Fully answerable
- Partially answerable
- Unanswerable from the corpus
- Ambiguous question
- Distractor-rich context

## Planned Evaluation Metrics

### Retrieval

- Recall at k
- Mean Reciprocal Rank
- Micro claim coverage
- Complete evidence rate
- Evidence-group recall

### Generation

- Answer correctness
- Citation correctness
- Citation coverage
- Faithfulness
- Response-language adherence
- Abstention recall
- False abstention rate

### Operational

- Retrieval latency
- Reranking latency
- Generation latency
- Memory and hardware requirements

## Expected Contributions

- An Arabic-question and English-scientific-document evaluation dataset
- Claim-level gold evidence groups
- Answerability and evidence-sufficiency annotations
- A controlled comparison of cross-lingual retrieval strategies
- An end-to-end evaluation of correctness, citation quality, faithfulness and abstention
- A reproducible local RAG pipeline using an open-weight small language model

## Role of the Current Experiments

The current seven-question experiment based on one paper is a pilot study.

It is used to:

- Test the evaluation workflow
- Identify annotation problems
- Detect ambiguous questions
- Refine claim and citation evaluation
- Estimate runtime
- Design the larger benchmark

Its numerical results will not be presented as evidence of general superiority.

## Minimum Main Study Scope

- 30 to 50 open-access scientific papers
- At least 300 Arabic questions
- Multiple scientific domains
- Two bilingual reviewers
- Inter-annotator agreement
- Fixed prompts and generation settings
- Paired statistical comparisons
- Public code and evaluation records

## Decision Rule

The project proceeds to the main experiment only if the literature review confirms a defensible gap and the expanded pilot shows that the proposed annotations can be applied consistently.

## Core Related Studies

- RAGChecker  
  https://arxiv.org/abs/2408.08067

- UAEval4RAG  
  https://aclanthology.org/2025.acl-long.415/

- XRAG Cross-lingual Retrieval-Augmented Generation  
  https://aclanthology.org/2025.findings-emnlp.849/

- The Cross-Lingual Cost  
  https://aclanthology.org/2025.arabicnlp-main.6/

- Arabic RAG Pipeline Optimization  
  https://arxiv.org/abs/2506.06339

- Scientific RAG in European Portuguese  
  https://aclanthology.org/2026.nslp-1.3/

- IslamicFaithQA  
  https://aclanthology.org/2026.findings-acl.1317/

## Current Status

Pilot experiments Q01, Q02, Q04 and Q05 have been completed for Dense at 5 and Reranked at 5.

Q05 remains excluded from aggregate evaluation because its intended task and answerability are ambiguous.

The literature matrix contains seed records S001-S015. S009, *The Cross-Lingual Cost*, is the first record with a completed provisional full-text extraction and quality appraisal.

S009 provides direct evidence that retrieval can be the main bottleneck in domain-specific Arabic-English RAG and that mixed-language candidate ranking can produce cross-language gaps above 40 percentage points. It does not evaluate scientific documents, small local generators, claim-level evidence sufficiency, citations, faithfulness, or abstention.

This evidence also limits the interpretation of H1. Because the planned scientific corpus is predominantly English-only, the mixed-language document-ranking failure isolated by S009 may be absent. Query translation must therefore remain an empirical comparison and must not be assumed to outperform direct Arabic multilingual retrieval.

The repository checkpoint before this extraction session is commit 5095664.
