# Jarvis LLM Lab

This roadmap is grounded in the public course repository:

- `https://github.com/mlabonne/llm-course`

## Goal

Use Jarvis's own conversations, repo-QA traces, benchmark prompts, and self-check output to evolve from a rule-heavy assistant into a fine-tuned local model workflow.

## Current runtime support

Jarvis now exposes two LLM-lab entrypoints in the live runtime:

- `llm roadmap`
- `llm export dataset`

The export command writes starter supervised fine-tuning records to:

- `training/jarvis_sft_dataset.jsonl`

## Phases

1. Fundamentals
   Learn the course's foundations for math, Python, and neural networks before attempting model training changes.

2. Dataset creation
   Build supervised examples from:
   - user prompt -> Jarvis answer
   - repo question -> grounded repo answer
   - benchmark prompt -> expected output
   - self-check prompt -> useful diagnostic response

3. Supervised fine-tuning
   Start with a small open instruct model and use a parameter-efficient fine-tuning path inspired by the course's QLoRA and Unsloth notebooks.

4. Preference optimization
   Once SFT is stable, improve helpfulness and consistency with an ORPO or DPO-style stage.

5. Evaluation
   Score Jarvis on:
   - chat quality
   - repo QA grounding
   - benchmark pass rate
   - self-check usefulness
   - safety regressions

6. Quantization and deployment
   Export compact local builds for Jarvis using the course's quantization track.

7. Advanced experiments
   Explore merges and MoE designs only after the dataset and evaluation loop are reliable.

## Practical advice

Do not start by trying to train a frontier model from scratch.
The right first milestone for Jarvis is:

- collect data
- fine-tune a small open model
- evaluate aggressively
- deploy a compact local version
