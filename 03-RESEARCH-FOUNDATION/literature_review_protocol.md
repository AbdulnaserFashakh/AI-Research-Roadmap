# Systematic Scoping Review Protocol

## 1. Protocol Information

Provisional title:

CyberRAG-Bench: A Systematic Scoping Review of Bilingual, Table-Aware, and Abstention-Calibrated RAG for Cyberbullying Research

Protocol version: 0.1

Date: 30 September 2026

Status: Draft

Registration: Not registered. OSF registration will be considered after finalizing the protocol and before formal screening.

Reporting guidelines:

- PRISMA-ScR for scoping reviews
- PRISMA-S for reporting literature searches

## 2. Rationale

Research on cyberbullying has mainly focused on classification, detection, sentiment analysis, and psychological impact assessment.

Retrieval-Augmented Generation may support evidence-grounded question answering across cyberbullying studies. However, the available evidence concerning bilingual retrieval, table extraction, citation faithfulness, and abstention for unsupported questions remains unclear.

A systematic scoping review is required to map the existing evidence, identify confirmed research gaps, and prevent unsupported novelty claims.

## 3. Review Objective

The review aims to identify and classify previous studies related to:

1. Cyberbullying detection and analysis using AI.
2. Retrieval-Augmented Generation for content moderation and scientific question answering.
3. Arabic-English and cross-lingual information retrieval.
4. Table-aware extraction from scientific PDF documents.
5. Faithfulness, hallucination control, uncertainty, and abstention in RAG.
6. Evaluation methods and benchmarks for retrieval and generation.

## 4. Review Questions

LRQ1. How have RAG and large language models been applied to cyberbullying, online harassment, and content moderation?

LRQ2. Which retrieval methods, embedding models, rerankers, and generators have been evaluated?

LRQ3. How have previous systems handled bilingual or cross-lingual queries and documents?

LRQ4. How have tables and numerical evidence been extracted from scientific PDF documents?

LRQ5. How have faithfulness, citation accuracy, hallucination, uncertainty, and abstention been evaluated?

LRQ6. Which datasets, benchmarks, evaluation metrics, and human-evaluation methods have been used?

LRQ7. Which limitations and research gaps are consistently reported across previous studies?

## 5. PCC Framework

### Population or Sources

- Cyberbullying and online-harassment studies
- Content-moderation systems
- Scientific articles and scholarly PDF collections
- Domain-specific question-answering datasets

### Concepts

- Retrieval-Augmented Generation
- Information retrieval
- Scientific question answering
- Cross-lingual retrieval
- Table extraction
- Evidence grounding
- Citation faithfulness
- Abstention and uncertainty

### Context

Evidence-grounded question answering and research support in the cyberbullying domain.

## 6. Evidence Streams

### Stream A: Cyberbullying and Content Moderation

Studies addressing cyberbullying detection, categorization, psychological impact, sentiment analysis, reasoning, intervention, or moderation.

### Stream B: RAG and Scientific Question Answering

Studies developing or evaluating RAG systems over scientific articles, reports, or domain-specific collections.

### Stream C: Cross-Lingual Retrieval

Studies examining Arabic-English, bilingual, multilingual, or cross-lingual retrieval and generation.

### Stream D: Table-Aware Document Processing

Studies extracting or retrieving numerical evidence from tables, figures, and complex PDF layouts.

### Stream E: Faithfulness and Abstention

Studies evaluating groundedness, citation accuracy, hallucination, uncertainty, unanswerable questions, or selective answering.

## 7. Information Sources

Primary databases:

- Scopus
- Web of Science
- IEEE Xplore
- ACM Digital Library
- ScienceDirect
- SpringerLink
- ACL Anthology
- PubMed

Supplementary sources:

- Google Scholar for citation chaining
- Semantic Scholar for discovery
- Reference lists of included studies
- Forward-citation searches

Preprints from arXiv may be included for horizon scanning but will be identified separately from peer-reviewed evidence.

## 8. Date Coverage

Cyberbullying and domain studies:

January 2015 to the final search date.

RAG and related methodological studies:

January 2020 to the final search date.

The final search date will be recorded after completing all database searches.

## 9. Language Coverage

- English
- Arabic

Studies in other languages will be recorded when an English title and abstract are available, but full inclusion will depend on translation feasibility.

## 10. Draft Search Strategies

### Search A: Cyberbullying and RAG

("cyberbullying" OR "cyber bullying" OR "online bullying" OR
"online harassment" OR "content moderation")
AND
("retrieval augmented generation" OR "retrieval-augmented generation" OR
"RAG-based" OR "large language model" OR "large language models")

### Search B: Scientific Question Answering

("scientific question answering" OR "scholarly question answering" OR
"document question answering" OR "scientific document")
AND
("retrieval augmented generation" OR "retrieval-augmented generation")
AND
(evidence OR citation OR table OR numerical OR PDF)

### Search C: Cross-Lingual RAG

(Arabic OR bilingual OR multilingual OR "cross-lingual")
AND
("retrieval augmented generation" OR "semantic retrieval" OR
"information retrieval")
AND
("question answering" OR generation)

### Search D: Faithfulness and Abstention

("retrieval augmented generation" OR "retrieval-augmented generation")
AND
(faithfulness OR groundedness OR hallucination OR abstention OR
unanswerable OR uncertainty OR "selective generation")

The search syntax will be adapted to each database. Every final query and execution date will be recorded.

## 11. Inclusion Criteria

A study will be included when it:

1. Addresses at least one review question.
2. Describes an AI, retrieval, RAG, question-answering, or content-moderation method.
3. Provides sufficient methodological information.
4. Reports experimental results, evaluation metrics, a benchmark, or a structured review.
5. Falls within the defined date range.
6. Is available in English or Arabic.
7. Is peer-reviewed, except preprints retained separately for horizon scanning.

## 12. Exclusion Criteria

A study will be excluded when it:

1. Mentions AI or RAG without describing or evaluating a method.
2. Is unrelated to cyberbullying, content moderation, scientific QA, retrieval, table processing, or RAG reliability.
3. Is an editorial, advertisement, tutorial, or non-technical opinion.
4. Lacks sufficient information for data extraction.
5. Duplicates another publication of the same study.
6. Is unavailable in full text after reasonable retrieval attempts.
7. Uses RAG as an unrelated acronym.

## 13. Screening Process

The selection process will include:

1. Database export.
2. Duplicate removal.
3. Title and abstract screening.
4. Full-text eligibility assessment.
5. Recording reasons for full-text exclusion.
6. Backward and forward citation searching.
7. Preparation of a PRISMA flow diagram.

Two reviewers should independently screen the studies.

Disagreements will be resolved through discussion. Cohen’s Kappa will be calculated when sufficient double-screened records are available.

## 14. Data Extraction Fields

For every included study, the following data will be recorded:

- Study ID
- Full citation
- DOI or URL
- Publication year
- Venue
- Study type
- Application domain
- Research objective
- Dataset or corpus
- Corpus size
- Language
- Modality
- Retrieval method
- Embedding model
- Chunking strategy
- Reranking method
- Generator model
- Table-processing method
- Cross-lingual method
- Citation mechanism
- Abstention mechanism
- Baseline systems
- Retrieval metrics
- Generation metrics
- Human-evaluation method
- Statistical tests
- Main findings
- Reported limitations
- Reported research gaps
- Code availability
- Data availability
- Relevance to CyberRAG-Bench

## 15. Quality Appraisal

Each empirical technical study will be assessed using the following criteria:

1. Clear research objective
2. Transparent dataset description
3. Reproducible methodology
4. Appropriate baseline comparison
5. Suitable evaluation metrics
6. Human evaluation when required
7. Statistical analysis
8. Error analysis
9. Code or data availability
10. Limitations and threats to validity

Each item will receive:

- 0: Not reported
- 1: Partially reported
- 2: Clearly reported

The quality score will support interpretation but will not automatically determine exclusion.

## 16. Evidence Synthesis

The review will use:

- Descriptive statistics
- Method taxonomy
- Evidence mapping
- Comparison tables
- Narrative synthesis
- Gap analysis

A meta-analysis is not currently planned because substantial heterogeneity is expected across tasks, datasets, models, and metrics.

## 17. Gap Validation Rules

A proposed gap will not be treated as confirmed merely because one paper reports it.

Each gap will be classified as:

- Confirmed gap
- Probable gap
- Contradicted gap
- Insufficient evidence

A confirmed gap should be supported by multiple sources and should not be contradicted by stronger recent evidence.

## 18. Research-to-Implementation Traceability

Each confirmed gap will be linked to:

- Research problem
- Research question
- Hypothesis
- Proposed system component
- Baseline
- Evaluation metric
- Experimental result

No system feature will be presented as a scientific contribution without an evidence-based rationale.

## 19. Planned Outputs

The review will produce:

1. PRISMA flow diagram
2. Literature matrix
3. Taxonomy of previous approaches
4. Confirmed research-gap map
5. Problem statement
6. Research questions and hypotheses
7. Experimental traceability matrix
8. Related-work section for the proposed paper
9. Evidence base for CyberRAG-Bench

## 20. Protocol Amendments

Any change to the search strategy, eligibility criteria, databases, or extraction fields will be documented with:

- Amendment date
- Previous version
- New version
- Reason for the amendment

The protocol will be frozen before formal database screening begins.

## 21. Methodological References

PRISMA-ScR:
https://www.prisma-statement.org/scoping

PRISMA-S:
https://www.equator-network.org/reporting-guidelines/prisma-s/

RAGAS:
https://aclanthology.org/2024.eacl-demo.16/

RAGChecker:
https://proceedings.neurips.cc/paper_files/paper/2024/hash/27245589131d17368cccdfa990cbf16e-Abstract.html