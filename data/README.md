# Jarvis training data

These files seed the Jarvis-specific datasets used by the future training and
evaluation pipeline.

Required corpora:

- `jarvis_identity.jsonl`
- `jarvis_reasoning.jsonl`
- `jarvis_coding.jsonl`
- `jarvis_tooluse.jsonl`
- `jarvis_memory.jsonl`
- `jarvis_selfcheck.jsonl`
- `jarvis_self_improvement.jsonl`
- `jarvis_reflection.jsonl`

Each record captures:

- input task
- context
- available tools
- relevant memory
- expected plan
- expected answer
- expected tool usage
- expected verification
- expected reflection
- outcome notes
