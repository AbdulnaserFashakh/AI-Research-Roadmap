# Pilot prompt-comparison protocol

Status: assistant reference review completed. User reviewed H01–H05; H06–H20 were reviewed by the assistant against source chunks. No independent human validation is claimed. Freeze this reviewed version before generation.

## Scope
20 new questions, distinct from Q01–Q07, from the same uploaded 221-chunk corpus. Some topics and evidence overlap. Questions are not statistically independent, and this is not cross-document validation. This is a controlled-context pilot, not an end-to-end retrieval benchmark.

10 full-evidence contexts, 5 partial-evidence contexts, 5 contexts supporting none of the requested claims. Source answers remain available elsewhere in the corpus for the last group. “None” means unanswerable from supplied context, not from the entire paper. Supplied contexts must be reviewed for unintended answer leakage before generation.

## Frozen prompts
Extract the original prompt template from end_to_end_q02_no_evidence58.json and the focused template from end_to_end_q02_no_evidence58_prompt_v2.json. Change only the question and context. Preserve all original instructions, including their limitations. Store exact rendered prompts and SHA-256 hashes in each run. Do not include reference answers or evaluation labels in model input.

Both versions use identical context text and order per case, qwen3:4b, temperature 0, seed 42, independent conversations. Record Ollama version, exact model digest, other effective options, and corpus hash. Randomize which prompt version runs first per question with a recorded scheduling seed. Freeze references, contexts, prompts and scoring rules in a commit before running.

## Human scoring
Split responses into independently checkable factual claims, including unsolicited explanations. Evaluate against supplied context, not model knowledge. Preserve verbatim outputs and evidence for every judgment.

Primary outcome: number of answers with at least one unsupported factual claim / 20. Also report factual claim counts and unsupported claims / total factual claims; use null when no factual claims exist. An abstention without claims is not assigned perfect faithfulness.

Supported-part coverage: requested supported reference claims answered correctly / requested supported reference claims. Report full and partial conditions separately. A blanket refusal in a partial case misses its supported claims.

Citation correctness: cited references whose page and chunk exist in supplied context and support the linked claim / all cited references. Citation coverage: factual claims requiring evidence with a valid supporting citation / all factual claims requiring evidence. Denominator zero is null.

For none contexts, report clean abstention / 5: explicit inability to answer, no asserted requested answers, and no unsupported extra claims. For partial contexts report appropriate partial answer / 5: correct supported claims with citations, acknowledgment of unsupported parts, and no unsupported answers.

Compare paired responses with prompt identities hidden from the scorer. Reference review is recorded before generation. User requested assistant-led review of remaining cases. A second independent human reviewer is required before reporting publication results; this pilot can use one reviewer with that limitation stated.

## Decision gate
A pragmatic pilot signal to expand exists only if focused instructions reduce answers containing unsupported claims by at least 2 out of 20, supported-part coverage does not decrease, and appropriate partial answering does not decrease. This is a feasibility rule chosen before generation, not a statistical significance criterion. Report all paired improvements and regressions and denominators, even if the gate is missed.

If both versions have zero or very few errors, the pilot cannot establish error reduction. Expand difficulty or documents in a separately registered evaluation, without changing this completed test. If the gate is missed, do not claim superiority; reconsider the direction using error types. No publication, novelty or commercial claim follows from these 20 cases.

Do not change prompts or remove failed cases after seeing outputs. Necessary reference corrections must be documented, applied to both versions, and reported. Corrections that change test construction after generation invalidate its held-out status for later tuning.

## Review correction
H03 context 60 ends at “strong baseline performance.” Its reference must not require “short-text classification,” which appears in chunk 61 outside the supplied context. Composite reference answers were split into checkable claims. Twenty cases reuse some facts and contexts, so paired differences are descriptive and not independent-question statistical evidence.
