# local-elicitation-front

> A decentralized, on-prem elicitation front that turns a vague business need
> into a structured, co-authored spec — without re-interrogating the requester.
> **The front asks; downstream builds. It never produces a solution.**

## The problem

Business doesn't speak IT; IT doesn't speak business. A request like
*"automate my reconciliation file"* is, on its own, unimplementable: the real
spec is buried in a spreadsheet nobody documented — a hidden join key, a
fallback key tucked inside a formula, two bare coefficients no one can explain
until asked. Today that gap is closed by repeated back-and-forth, or not at all.

## The approach

A chat-shaped front (chat is the *façade*, not the product) drives a small,
deterministic elicitation pipeline:

1. **Mirror** the need back — *"if I understand correctly, you want X."*
2. **Anchor** on real data — ask for the missing files, then read their schema.
3. **Question** — 2–3 pre-filled, swipe-to-confirm cards on the highest-risk
   unknowns. The gesture *is* the captured verdict (co-authorship, no cost).
4. **Normalize** — project the free-form need onto a **closed vocabulary**
   (a need *type* + enumerable *slots*). Stability comes from the closed target,
   not from hashing generative output.
5. **Emit** a single artifact: the normalized spec + an append-only trace
   (verbatim dialogue, human verdicts, declared files, provenance).

Schema-driven: the schema is the contract; Python is thin glue, never the seat
of intelligence. A single local model (≤3B, GGUF, in-process) runs per machine.

## Why decentralized

- **Marginal cost near zero** — one local model per seat, no per-token API,
  no per-seat cloud subscription. Cost doesn't scale with usage.
- **Data never leaves the site** — a compliance argument (PII/GDPR) *and* a
  cost argument (no central transit/storage to secure).
- **No single point of failure** — each machine is autonomous (one exe, one
  model in-process).
- **Captured value is reusable** — the append-only trace is an asset
  (normalized specs, human verdicts), not just a log.

The honest bet: value depends on **adoption** (engagement is the #1 survival
variable) and on the acceptance oracles passing on the real reference case.
The POC is judged by hard oracles, never by a polished demo.

## Scope (deliberately narrow)

**The front, and nothing but the front.** No code/solution generation, no
deduplication, no curation, no web UI — those are downstream stages that
*consume* this output. Non-negotiable guardrail: no downstream stage opens
until the oracles are green on the real reference case.

## Status

**Proof of concept.** Design phase complete; implementation in progress.
Success is measured by three hard oracles: completeness (a human implements
from one artifact, no re-interrogation), obedience/stability of the model under
an imperative harness, and listening (a pushed fact is honored on the next turn).

## Stack

Python · `uv` · `ruff` · `pytest` · GGUF model via local runtime.
