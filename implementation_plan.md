# Jarvis Next-Generation Implementation Plan

This repository is evolving from a task-oriented assistant into a persistent
engineering intelligence. The goal is not to fake autonomy or human cognition,
but to assemble explicit, testable subsystems that together approximate a
stable cognitive architecture.

## Active runtime path

- `jarvis.py`
- `core/main_loop.py`
- `web_server.py`
- `core/offline_memory.py`
- `core/repo_qa.py`
- `core/llm_lab.py`
- `cognition/foundation.py`

## File-by-file build plan

### Runtime orchestration

- `core/main_loop.py`
  Extend the live loop to call perception, planning, verifier, autonomy, and
  memory services in a staged order rather than a single fallback chain.
- `cognition/foundation.py`
  Central architecture ledger that reports what is real now, partial now, and
  still aspirational.
- `planning/plan_schema.py`
  Shared plan objects for user tasks, internal tasks, and self-improvement.

### Memory system

- `core/offline_memory.py`
  Keep durable working and episodic memory online even with no model backend.
- `memory/memory_router.py`
  Upgrade ranking, consolidation, and conflict handling.
- `dataset_builder/jarvis_dataset_schema.py`
  Convert useful Jarvis interactions into structured training examples.

### Reasoning and verification

- `reasoning/intent_analyzer.py`
  Improve decomposition, ambiguity detection, and escalation triggers.
- `verifier/verification_pipeline.py`
  Require impact analysis, sandboxing, benchmarks, and rollback readiness.
- `reflection/reflection_engine.py`
  Replace weak free-form reflection with structured expected-vs-actual review.

### Autonomy and self-improvement

- `autonomy/session_manager.py`
  Define bounded background jobs and audit requirements.
- `scheduler.py`
  Eventually schedule background jobs through the bounded autonomy registry.
- `self_improvement/patch_proposer.py`
  Keep proposals small, explicit, and tied to metrics.
- `self_improvement/patch_evaluator.py`
  Compare baseline vs candidate before adoption.
- `rollback/rollback_controller.py`
  Enforce rollback readiness before any high-risk change.

### Model stack and training

- `model_stack/jarvis_model_stack.py`
  Define separate model roles instead of pretending one model does everything.
- `training_pipeline/llm_course_pipeline.py`
  Ground fine-tuning, alignment, evaluation, and quantization in
  `mlabonne/llm-course`.
- `data/*.jsonl`
  Maintain Jarvis-specific training and evaluation corpora.

### Benchmarks and deployment

- `benchmarks/cognitive_regression.py`
  Measure memory continuity, repo grounding, verifier discipline, autonomy
  safety, and dataset quality.
- `benchmarking/benchmark_runner.py`
  Fold cognitive regression cases into the live benchmark runner.
- `web_server.py`
  Surface architecture, verifier, memory, and autonomy status in the UI.

## Phase roadmap

1. Foundation
   Add explicit architecture modules, dataset schemas, verifier stages, and
   autonomy job definitions.
2. Integration
   Route the live loop through the new planning, verifier, and memory surfaces.
3. Evaluation
   Benchmark routing, grounding, safety, and training-data quality.
4. Controlled self-improvement
   Only adopt measured improvements with rollback support.
5. Model specialization
   Train and route Jarvis-specific roles for general, coding, reasoning,
   verifier, and memory tasks.

## Honest realism

- Real now: offline memory, repo-grounded answers, inherited Claude command
  surface, LLM roadmap, dataset export, streaming web UI.
- Partially real: scheduler, reflection, rollback, model routing,
  self-improvement scaffolding.
- Not real yet: trustworthy unsupervised self-coding, persistent autonomous code
  evolution, or a trained Jarvis-specific model family.
