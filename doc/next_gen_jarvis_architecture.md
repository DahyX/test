# Jarvis Next-Generation Cognitive Architecture

## 1. Executive architecture summary

Jarvis should be built as a persistent cognitive software system with explicit
layers:

- perception
- memory
- reasoning
- planning
- action selection
- verification
- reflection
- self-improvement
- autonomous background work
- model-stack specialization

The live runtime must remain local-first, testable, and reversible. Every
improvement must define a metric, a verification path, and a rollback path.

## 2. Folder structure

Current and new foundation modules:

- `cognition/`
- `planning/`
- `autonomy/`
- `model_stack/`
- `verifier/`
- `training_pipeline/`
- `dataset_builder/`
- `rollback/`
- `benchmarks/`
- `core/`
- `memory/`
- `reasoning/`
- `reflection/`
- `self_improvement/`
- `safety/`
- `tests/`
- `data/`

Note: a top-level `logging/` package is intentionally avoided because it would
shadow Python's standard library `logging` module. Audit logging should continue
through SQLite and runtime log records until a safe namespace is chosen.

## 3. File-by-file build plan

- `core/main_loop.py`
  Make this the executive controller that calls perception, memory retrieval,
  planning, tool selection, verification, and reflection in order.
- `cognition/foundation.py`
  Keep the authoritative architecture ledger and realism check.
- `planning/plan_schema.py`
  Define plan steps, metrics, gates, and rollback strategy.
- `core/offline_memory.py`
  Keep short-term and episodic memory durable without network access.
- `memory/memory_router.py`
  Upgrade ranking, consolidation, pruning, and contradiction resolution.
- `verifier/verification_pipeline.py`
  Enforce impact analysis, sandbox validation, tests, benchmarks, and rollback.
- `reflection/reflection_engine.py`
  Compare expected vs actual results and emit lessons.
- `autonomy/session_manager.py`
  Define bounded, reviewable background jobs and audit records.
- `scheduler.py`
  Execute approved autonomy jobs on a safe cadence.
- `model_stack/jarvis_model_stack.py`
  Separate Jarvis-general, Jarvis-coder, Jarvis-reasoner, Jarvis-verifier,
  Jarvis-memory-router, and Jarvis-trainer roles.
- `dataset_builder/jarvis_dataset_schema.py`
  Standardize Jarvis training examples.
- `training_pipeline/llm_course_pipeline.py`
  Use `mlabonne/llm-course` as the technical basis for SFT, QLoRA, alignment,
  quantization, and evaluation workflows.
- `rollback/rollback_controller.py`
  Require revertability before meaningful self-modification.
- `benchmarks/cognitive_regression.py`
  Track non-negotiable behavioral metrics.

## 4. Self-improvement framework

Every self-improvement candidate must include:

- target module
- goal
- baseline metric
- candidate change
- verifier gates
- benchmark comparison
- rollback plan

Lifecycle:

1. Observe a failure or repeated weakness.
2. Propose a bounded candidate change.
3. Run sandbox checks and focused tests.
4. Compare against baseline benchmarks.
5. Accept only if metrics improve or remain stable with clearer architecture.
6. Log the result and store lessons.

## 5. Autonomous background work framework

Autonomy is real only if it is bounded and auditable. Each autonomous session
must log:

- timestamp
- trigger
- objective
- tools used
- files touched
- tests run
- result summary
- accepted or rejected status
- rollback status

Default background jobs:

- review recent failures
- consolidate memory
- benchmark model routing
- curate training data
- review code hotspots

## 6. Jarvis-specific LLM training plan

Use `https://github.com/mlabonne/llm-course` as the implementation foundation,
not as a ready-made Jarvis brain.

Planned path:

1. Build Jarvis-specific datasets from runtime memory, repo QA, self-check, and
   benchmark traces.
2. Fine-tune a small instruct model with a QLoRA-style workflow.
3. Add preference optimization only after SFT quality is stable.
4. Evaluate general chat, coding, reasoning, memory, verifier, and autonomy
   behavior separately.
5. Quantize the best model for local-first deployment.
6. Route specialized roles through the model stack instead of overloading one
   generic model.

## 7. Safety and rollback plan

Safety rules:

- no blind self-rewrites
- no improvement without a metric
- no promotion without verifier approval
- no critical change without rollback readiness
- no destructive autonomy by default

Rollback rules:

- backup before edit
- patch log before merge
- benchmark comparison before adoption
- auto-revert failed candidates where possible

## 8. Phase-by-phase implementation roadmap

### Phase 1: Foundation

- add explicit architecture modules
- add dataset schemas and seed corpora
- add verifier and autonomy definitions

### Phase 2: Runtime integration

- route main loop through planning and verifier surfaces
- expose architecture status through CLI and web runtime

### Phase 3: Evaluation

- expand benchmarks for memory, grounding, verification, and autonomy
- harden self-check and routing diagnostics

### Phase 4: Controlled self-improvement

- integrate sandboxed candidate testing
- compare baseline vs candidate automatically

### Phase 5: Model specialization

- create Jarvis-general, Jarvis-coder, Jarvis-reasoner, Jarvis-verifier, and
  Jarvis-memory-router role routing

### Phase 6: Background development

- run bounded autonomous sessions on approved schedules
- curate datasets and benchmark regressions continuously

## 9. Honest realism check

### Feasible now

- structured memory
- repo-grounded code answers
- explicit architecture/status surfaces
- dataset export for future SFT
- verifier and autonomy definitions
- local-first deployment flow

### Partially feasible now

- reflection quality
- scheduler-backed autonomy
- rollback automation
- model-role routing
- self-improvement proposals

### Still aspirational

- trustworthy unattended self-coding
- full human-like multi-stage cognition
- a trained Jarvis-specific multi-model stack already outperforming the current
  runtime
- safe continuous architecture evolution without heavy human review
