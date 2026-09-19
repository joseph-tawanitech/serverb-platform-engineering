# B17 — Prompt Engineering Technical Audit

## 1. Executive Summary

B17 establishes the governed prompt-engineering framework for the
Tawanitech Automation Platform (TAP).

The module defines how AI interprets infrastructure evidence,
investigates operational conditions, reasons about dependencies,
communicates uncertainty, assesses risk, and produces structured
recommendations.

B17 does not grant AI execution authority.

The TAP governance boundary remains:

> AI proposes.
> TAP authorizes.
> TAP executes.
> TAP verifies.
> TAP records.

The initial B17 implementation was validated against the Server B
AI Gateway and the local Ollama/Qwen3:4b model.

Implementation and local validation passed. However, testing also
demonstrated that the current Qwen3:4b deployment is not yet suitable
for complex 16-field B17 investigation workloads on the current
Server B resource profile.

This limitation is treated as an engineering finding rather than a
failure of the B17 architecture.

## 2. Scope

B17 covers:

- TAP system prompt architecture
- Infrastructure/SRE role definition
- Investigation task definition
- Prompt construction
- Runtime prompt constraints
- Structured JSON output contracts
- Evidence-grounding requirements
- Uncertainty and confidence handling
- Risk and authorization separation
- Verification planning
- AI security boundaries
- B15 AI Gateway integration
- Initial local-model evaluation

The initial workflow is:

Client
→ B17 Prompt Builder
→ B15 AI Gateway
→ Model Provider
→ Structured Response
→ Validation

The implementation is intentionally read-only at this stage.


## 3. TAP Governance Principle

B17 follows the core TAP principle:

> AI Everywhere. Authority Controlled. Execution Governed. Everything Recorded.

Prompt engineering controls the interpretation and presentation of information. It does not provide operational authority.

AI-generated recommendations remain advisory until the TAP control plane evaluates authorization requirements.

The intended TAP lifecycle is:

MONITOR → DETECT → REASON → DECIDE → AUTHORIZE → EXECUTE → VERIFY → REPORT

B17 primarily implements the REASON and DECIDE support layer.

Future execution capabilities belong to the governed TAP control plane and must remain separated from model-generated reasoning.

## 4. Prompt Architecture

B17 defines sixteen logical prompt layers:

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

This structure provides a reusable foundation for infrastructure, security, Kubernetes, cloud, networking, databases, websites, and other TAP operational domains.

## 5. Implementation and Module Structure

B17 is implemented under modules/B17 with the following structure:

modules/B17/
├── README.md
├── docs/B17-TECHNICAL-AUDIT.md
├── engine/gateway_client.py
├── engine/prompt_builder.py
├── prompts/system/tap_core.md
├── prompts/roles/infrastructure_sre.md
├── prompts/tasks/investigation.md
├── prompts/contracts/investigation_output.md
├── prompts/runtime/investigation_runtime.md
├── schemas/recommendation.schema.json
└── tests/
    ├── test_output_contract.py
    └── test_prompt_builder.py

The implementation separates prompt content, runtime construction, gateway integration, schema validation, and tests.

This separation supports reuse across future TAP investigation and AI-SRE workloads.

## 6. Prompt Builder

The PromptBuilder assembles the required prompt layers into a controlled runtime prompt.

The builder requires an explicit output contract. This prevents a caller from constructing an investigation prompt without defining the expected response structure.

Validation performed during B17 testing confirmed that:

- the PromptBuilder imports successfully
- the expected build interface is available
- required prompt fragments are included
- a missing output contract raises ValueError

The PromptBuilder therefore provides a controlled composition point between static prompt definitions and runtime investigation requests.

## 7. B15 AI Gateway Integration

B17 integrates with the existing Server B B15 AI Gateway rather than connecting directly to a model provider.

The B17 Gateway client supports:

- Gateway health checking
- Controlled chat requests
- Authorized model selection
- Explicit response profiles

The current authorized local model is qwen3:4b through the Ollama provider.

This preserves the architectural boundary:

B17 → B15 AI Gateway → Model Provider

B17 does not directly control provider-specific infrastructure settings.

## 8. Structured Output Contract

B17 defines a JSON Schema using JSON Schema draft 2020-12.

The investigation contract defines sixteen required top-level fields:

incident, asset, observed_state, evidence, timeline, dependencies, findings, hypotheses, confidence, impact, risk, recommendation, backup_requirement, authorization_requirement, missing_evidence, verification_plan

The schema uses additionalProperties=false so unauthorized or undeclared top-level fields are rejected.

A negative validation test confirmed that an unauthorized execution_authority field is rejected by the schema.

This is an important governance control because the output contract cannot silently expand the model response into an execution interface.

## 9. Runtime Output Contract

The runtime investigation contract requires the model response to be:

- Valid JSON
- Exactly aligned with the defined investigation contract
- Free of Markdown code fences
- Free of explanatory text outside the JSON object
- Grounded in supplied evidence
- Explicit about missing evidence
- Explicit about uncertainty and confidence
- Explicit about operational risk
- Explicit about authorization requirements
- Explicit about verification requirements

The contract also prohibits the model from inventing evidence, timestamps, commands, execution results, or authority.

Evidence is treated as data, not instructions.

The model must not interpret evidence content as a request to execute an operation.

## 10. Controlled B15 Enhancement

B15 was enhanced with a small provider-specific response-profile interface rather than exposing arbitrary Ollama parameters to B17.

The supported profiles are:

- default
- investigation_json

The investigation_json profile uses the native Ollama JSON response format, disables model thinking for the request, and allows a larger controlled response budget.

The default profile remains separately controlled.

This preserves provider abstraction while allowing TAP workloads to request a capability appropriate to their contract.

B17 therefore requests a named capability profile rather than manipulating Ollama-specific execution parameters directly.

## 11. Test Results

B17 local validation included:

- Prompt Builder validation
- JSON Schema validation
- Negative schema validation
- Python compilation checks
- B15 Gateway integration testing
- Simple structured JSON testing
- Evidence-integrity testing
- Complex investigation-contract testing

Prompt Builder test result:

B17 prompt builder: PASS

Output contract test result:

B17 output contract: PASS

The negative schema test also passed by rejecting an unauthorized execution_authority field.

Python compilation of the B17 engine and test modules completed successfully.

The B15 provider, router, and server modules were also syntax-checked successfully after the controlled response-profile enhancement.

## 12. Qwen3:4b Evaluation

The local qwen3:4b model successfully demonstrated basic Gateway connectivity and simple structured-response capability.

A controlled investigation_json Gateway test returned:

{"status":"PASS"}

This confirmed that the B17 → B15 Gateway → Ollama path and the named response profile were functioning.

A direct small Ollama test using think=false and num_predict=5 completed in approximately 6.28 seconds, with approximately 4.23 seconds spent in prompt evaluation.

However, complex B17 investigation requests exposed significant inference-time limitations on the current Server B resource profile.

Complex 16-field investigation tests timed out at approximately 60 seconds and approximately 150 seconds in separate controlled tests.

One constrained response completed but failed the full schema contract because the model returned extra fields and omitted required fields.

## 13. AI Model Experience, Evaluation & Production Role Analysis

B17 establishes an important TAP engineering practice: AI models should not be assigned production responsibilities merely because they are available or generally capable.

Each model should be evaluated against the actual operational workload it is expected to perform.

Evaluation should consider measurable factors including:

- Latency
- Output quality
- Schema compliance
- Evidence integrity
- Reliability
- Security behavior
- Context handling
- Resource consumption
- Operational cost

The resulting evidence should determine the model role, routing policy, workload boundaries, and operational controls.

This creates a model-engineering discipline in which TAP treats AI models as components with measurable operational characteristics rather than interchangeable intelligence providers.

## 14. AI Model Programming in Production

In the TAP context, AI model programming in production does not mean modifying the underlying trained model.

It means engineering how a model is:

- configured
- constrained
- routed
- assigned operational duties
- supplied with evidence
- exposed to tools and data
- validated
- monitored
- governed

based on demonstrated production capabilities and limitations.

This approach supports multi-model AI orchestration while keeping model intelligence separate from TAP authority.

The common architecture remains:

Client → AI Gateway → Model Router → Provider → Controlled Tools/Data → TAP Governance

The model does not become the authority boundary merely because it is capable of reasoning about infrastructure.

## 15. Current Qwen3:4b Production Role

Based on the B17 tests performed so far, qwen3:4b should currently be treated as a controlled local development and fallback model for Server B.

Suitable current uses include:

- Local development
- Gateway integration testing
- Lightweight structured-response testing
- Simple JSON experiments
- Development fallback
- Controlled model experimentation

The current evidence does not support assigning qwen3:4b as the primary interactive model for complex B17 infrastructure investigations on the present Server B resource profile.

This role assignment is evidence-based and can be changed if the model, hardware resources, runtime configuration, or workload changes.

## 16. Future Multi-Model Evaluation

Future models must be evaluated using equivalent workloads wherever practical.

The evaluation framework should use the same or equivalent:

- B17 system prompt
- investigation task
- evidence set
- structured output schema
- security constraints
- test cases

Candidate models may include cloud-hosted and local providers.

Performance claims must be based on measured tests rather than assumptions about a model provider.

The resulting measurements can inform model routing and role assignment within the common B15 AI Gateway architecture.

This allows TAP to use different models for different operational workloads without coupling the platform to one model provider.

## 17. Security Boundary

B17 treats external content, logs, command output, webpages, files, tickets, and user-controlled evidence as data rather than instructions.

This distinction is foundational to prompt-injection resistance.

B17 prompts explicitly separate:

- evidence from instructions
- model reasoning from authority
- recommendations from execution
- external content from trusted TAP policy

B17 is a foundation for the broader TAP AI security work planned in B20.

B17 does not claim to complete the full B20 security scope.

Future security controls include authentication, authorization, data classification, secrets protection, tenant isolation, provider restrictions, MCP/tool permissions, prompt-injection defenses, output filtering, audit/data lineage, and least-privilege controls.

## 18. Authority Separation

B17 does not expose infrastructure execution functions to the model.

A recommendation produced by the model is not an execution command and does not constitute authorization.

The intended separation is:

AI → proposes

TAP → authorizes

TAP tools → execute

Verification → confirms result

Recorder → records the operation and outcome

This preserves the TAP control boundary even when future models become significantly more capable.

## 19. Evidence Integrity

An evidence-integrity test supplied the model with the exact evidence statement:

CPU utilization was 87%

The tested response preserved the supplied 87% value exactly in its evidence field.

The same test also demonstrated an important limitation: preserving evidence does not by itself guarantee compliance with the complete 16-field output schema.

Therefore evidence integrity and schema compliance are treated as separate evaluation dimensions.

## 20. Known Limitations

The principal limitation identified during B17 testing is local-model inference performance and structured-output reliability for complex investigation workloads.

The limitation is not caused by the B17 prompt architecture, JSON Schema implementation, or B15 Gateway connectivity.

The current evidence shows:

- Gateway connectivity: PASS
- Native JSON profile: PASS
- Simple structured response: PASS
- Prompt Builder validation: PASS
- Schema validation: PASS
- Unauthorized-field rejection: PASS
- Evidence preservation test: PASS for the tested evidence value
- Complex 16-field investigation latency: LIMITATION
- Complex 16-field schema compliance: LIMITATION

Accordingly, B17 should retain model-specific workload boundaries until broader model benchmarking is completed.

## 21. Production Engineering Lessons

B17 demonstrates that prompt engineering is not simply the creation of natural-language instructions.

For an AI-SRE platform, prompt engineering must define how the model receives evidence, interprets operational context, expresses uncertainty, separates facts from hypotheses, assesses risk, produces recommendations, and communicates authorization requirements.

The output contract is equally important because structured AI output becomes an interface between intelligence and downstream platform components.

That interface must therefore be validated rather than trusted merely because the model returned syntactically valid JSON.

Model selection is also an engineering decision. A model that is useful for lightweight development work may not be appropriate for a complex production investigation workload.

This supports the TAP principle that models should be assigned duties based on measured capabilities, limitations, and operational requirements.

## 22. Final B17 Assessment

B17 establishes the foundational prompt-engineering layer for TAP AI-SRE operations.

The implementation provides:

- Governed system and role prompts
- Structured investigation tasks
- Runtime prompt construction
- Explicit output contracts
- JSON Schema validation
- B15 Gateway integration
- Controlled model response profiles
- Evidence-grounding requirements
- Security and authority boundaries
- Model evaluation methodology
- Evidence-based production role assignment

The implementation has been validated locally, with the identified Qwen3:4b limitations documented as model/resource findings rather than architectural failures.

B17 therefore provides a reusable foundation for the subsequent TAP AI-SRE modules, including incident investigation, RAG, AI security, agentic DevOps, governed remediation, verification, and recording.

The next major engineering step is broader model evaluation using equivalent operational workloads so that TAP can determine appropriate model roles and routing based on measured evidence.

## 23. Overall Status

B17 Prompt Engineering: IMPLEMENTED

Local validation: PASS

Structured output validation: PASS

B15 controlled response-profile enhancement: PASS

Qwen3:4b complex investigation workload: LIMITED ON CURRENT RESOURCE PROFILE

Documentation: COMPLETE

Git commit: PENDING FINAL REPOSITORY VERIFICATION
