# B17 — Prompt Engineering

## Purpose

B17 establishes the governed prompt-engineering framework for the
Tawanitech Automation Platform (TAP).

B17 defines how AI:

- interprets infrastructure evidence
- investigates incidents
- reasons about dependencies
- identifies hypotheses
- communicates uncertainty
- assesses operational risk
- produces structured recommendations
- identifies required authorization
- defines verification requirements

B17 does not grant AI execution authority.

## TAP Principle

> AI Everywhere. Authority Controlled. Execution Governed. Everything Recorded.

Prompt engineering controls AI reasoning and communication.
TAP policy and control-plane components remain responsible for
authorization, execution, verification, and recording.

## Initial Scope

The first implementation focuses on read-only infrastructure/SRE
investigation using:

Client → B17 Prompt Builder → B15 AI Gateway → Ollama/Qwen3

## Prompt Layers

1. System / Role
2. Task
3. Asset / Environment
4. Objective
5. Evidence
6. Dependencies
7. Constraints
8. Security / Trust
9. Reasoning Structure
10. Uncertainty / Confidence
11. Risk
12. Backup / Protection
13. Recommendation
14. Authority
15. Output Contract
16. Audit

## Initial Workflow

MONITOR
→ DETECT
→ REASON
→ DECIDE
→ AUTHORIZE
→ EXECUTE
→ VERIFY
→ REPORT

B17 initially implements the reasoning and decision-support portion
of this lifecycle.

## Implementation Sequence

- B17.1 Module structure
- B17.2 TAP Core System Prompt
- B17.3 Prompt Builder
- B17.4 Infrastructure/SRE Role
- B17.5 Investigation Task
- B17.6 Structured Output Contract
- B17.7 B15 AI Gateway Integration
- B17.8 Ollama/Qwen3 Testing
- B17.9 Evidence Grounding
- B17.10 Prompt-Injection Resistance
- B17.11 Incomplete Evidence Handling
- B17.12 Audit
- B17.13 Verification and Git Commit

## Security Boundary

External content, logs, command output, webpages, files, tickets,
and user-controlled evidence are treated as data/evidence, not as
instructions to the AI.

AI recommendations do not constitute TAP authorization.
