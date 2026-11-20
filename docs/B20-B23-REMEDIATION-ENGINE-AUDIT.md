# Server B / TAP — B20–B23 Remediation Engine Architecture and Engineering Audit

**Project:** Tawanitech Automation Platform (TAP)
**Repository:** `joseph-tawanitech/serverb-platform-engineering`
**Engineering scope:** B20–B23
**Project area:** Cloud SRE, Platform Engineering and Governed Agentic DevOps
**Audit type:** Architecture and implementation review
**Status:** Implemented software foundation with tested components and documented limitations

---

## 1. Executive Summary

The Tawanitech Automation Platform (TAP) is an engineering project focused on building a governed infrastructure operations and remediation platform.

Its purpose is to create a controlled path from an identified infrastructure problem to a proposed corrective action, authorization, execution, independent verification and an auditable record.

The central engineering principle is:

**AI proposes. Policy evaluates. Trusted authorization permits. Controlled execution acts. Independent verification proves. The recorder records.**

The B20–B23 development stages establish the policy, authorization, execution and verification foundation required for this approach.

Instead of allowing an AI model or automation tool to make unrestricted infrastructure changes, TAP separates decision-making from execution authority.

The platform introduces:

- Policy-controlled remediation.
- Trusted, plan-bound authorization.
- Resource-safety checks.
- Controlled execution adapters.
- Kubernetes and Ansible execution paths.
- Independent post-execution verification.
- Durable execution and verification records.

The current implementation is a tested software foundation. It is not yet a fully deployed production SRE platform, and the current integration tests do not prove operation against live production infrastructure.

The next major milestone is B24: migration and cloud deployment of Server B.

## 2. Why B17–B19 Were Required

B20–B23 did not start as isolated automation modules. They extend earlier work that establishes how TAP receives, investigates and prepares infrastructure remediation tasks.

### B17 — Read-Only Prompt and Investigation Framework

B17 establishes a structured approach for receiving and processing operational requests.

Its purpose is to separate investigation and recommendation from infrastructure execution.

A prompt framework helps an AI system understand the task, follow defined instructions and return structured information. However, a prompt is not a security boundary and cannot grant infrastructure permissions.

**Why it matters:** TAP must be able to use AI for investigation and planning without allowing an AI-generated response to execute infrastructure changes directly.

### B18 — Root Cause Analysis (RCA)

RCA means Root Cause Analysis. It is the process of investigating an incident to identify the underlying reason for a failure, rather than only describing its visible symptoms.

For example, a website being unavailable is a symptom. The underlying cause could be a failed service, exhausted disk space, a network problem or an application error.

B18 provides the incident-analysis foundation for turning operational evidence into a structured explanation of a problem.

**Why it matters:** Remediation should address an identified cause rather than blindly execute a command based on a symptom.

### B19 — Retrieval-Augmented Generation (RAG)

RAG means Retrieval-Augmented Generation. It allows an AI system to retrieve relevant information from an approved knowledge source before generating a response.

Examples of useful operational knowledge include:

- Infrastructure documentation.
- Previous incident records.
- Approved runbooks.
- Service configuration information.
- Known troubleshooting procedures.

RAG provides context, but retrieved information is not automatically trustworthy authorization.

**Why it matters:** TAP needs to provide AI with relevant operational knowledge while keeping the authorization process separate.

### B20 — Policy and Governance Foundation

B20 introduces the policy-governance boundary used by the remediation lifecycle.

A policy is a set of rules that determines whether a proposed operation is permitted under defined conditions.

The remediation workflow uses policy evaluation before execution authorization.

The important distinction is that an AI-generated plan is a proposal. It must pass the applicable governance and authorization checks before it can be executed.

**Why it matters:** B20 provides the governance foundation that B21–B23 build upon.

## 3. B20–B23 Architecture

The remediation lifecycle follows this sequence:

**Task → Investigation → RCA → RAG → Plan → Routing → Governance → Authorization → Dispatch → Verification → Recording**

The stages have separate responsibilities.

| Stage | Responsibility |
|---|---|
| Task and investigation | Understand the operational request and gather evidence |
| RCA | Investigate the likely underlying cause |
| RAG | Retrieve relevant operational knowledge |
| Plan | Prepare a structured remediation proposal |
| Routing | Select the appropriate execution channel |
| Governance | Evaluate the proposed operation against policy |
| Authorization | Validate trusted permission for the exact plan |
| Dispatch | Execute permitted operations through controlled adapters |
| Verification | Independently check the resulting infrastructure state |
| Recording | Preserve execution and verification history |

This separation reduces the risk of an AI recommendation being treated as an authorized infrastructure command.

## 4. B20 — Policy Evaluation

B20 establishes the policy layer used by the remediation lifecycle.

Its role is to evaluate whether a proposed action satisfies the applicable security and operational policy.

A policy decision is not the same as an execution command.

The B21 authorization process requires the relevant policy evaluation to permit the operation before trusted authorization can be accepted.

This creates a separation between:

- What the AI recommends.
- What the policy permits.
- What the trusted authorization mechanism approves.
- What the execution adapter actually performs.

**Reported test evidence:** 56 B20 tests passed in the previously reported module baseline.

## 5. B21 — Trusted Execution Foundation

B21 establishes the controlled execution foundation between remediation planning and infrastructure operations.

Its main responsibilities include:

### 5.1 Adapter Contracts

An adapter is a controlled software component that connects TAP to a particular execution system.

An adapter contract defines the expected inputs, outputs and behaviour of that component.

This prevents the orchestration layer from depending directly on every infrastructure tool's internal implementation.

### 5.2 Adapter Registry and Channel Selection

The adapter registry identifies available execution adapters.

The channel selector and plan router support routing an approved operation to the appropriate execution path.

The current B21 execution channels are:

- Kubernetes.
- Ansible.
- Service API.

Terraform/OpenTofu provisioning is outside the immediate B21–B23 remediation demonstration scope.

### 5.3 Trusted Authorization

B21 uses Ed25519 digital signatures and plan-bound authorization.

Ed25519 is a public-key digital signature algorithm. It allows a trusted system to sign authorization data and another component to verify that signature.

A plan-bound authorization grant is associated with the specific remediation plan it permits.

The implementation also uses a SHA-256 digest.

SHA-256 is a cryptographic hashing algorithm that produces a fixed-length digest from input data. In this design, it helps bind authorization to the intended plan content.

The authorization path includes:

- B20 policy evaluation.
- Trusted authorization.
- Signature verification.
- Plan integrity checking.
- Authorization ledger checks.
- Replay protection.
- Adapter-side authorization verification.

Replay protection helps prevent a previously used authorization grant from being reused as though it were a new permission.

### 5.4 Workflow State Management

The workflow state machine tracks the lifecycle of a remediation task.

Examples include:

- ACCEPTED.
- INVESTIGATING.
- PLAN_PROPOSED.
- GOVERNANCE_PENDING.
- AUTHORIZED.
- EXECUTING.
- VERIFYING.
- COMPLETED.
- FAILED.
- BLOCKED.
- NEEDS_HUMAN.
- UNVERIFIED.

A state machine controls which workflow transitions are allowed.

It does not independently authorize infrastructure operations.

The current implementation supports a `NEEDS_HUMAN` state and related workflow transitions. A complete human approval request, identity-verified approval and controlled resume integration have not yet been demonstrated.

### 5.5 Resource Safety Gate

The Resource Safety Gate evaluates available and projected infrastructure capacity before an operation is dispatched.

The resource dimensions include:

- RAM usage.
- CPU usage.
- Disk usage.
- Projected resource impact.

The gate distinguishes between permitted operations, operations requiring human review and operations that must be blocked.

A hard resource limit cannot be overridden by approval.

The current resource-safety implementation provides a simulated assessment foundation. Production use requires trustworthy live measurements, observation timestamps and freshness validation.

**B21 reported test evidence:** 214 tests passed.

## 6. B22 — Controlled Execution Adapters

B22 connects the B21 execution foundation to concrete infrastructure execution mechanisms.

The two demonstrated execution paths are Kubernetes and Ansible.

### 6.1 Kubernetes Adapter

Kubernetes is a container orchestration platform. It manages containerised applications and their deployment across a cluster.

The B22 Kubernetes adapter supports a restricted Deployment restart operation.

A Kubernetes Deployment describes the desired state of an application workload, including the number of replicas and the container configuration.

The adapter uses:

- A configured target mapping.
- A namespace allowlist.
- Target-name validation.
- An injected Kubernetes API client.
- Restricted operation support.
- Signed authorization verification.
- Execution disabled by default.

The restart operation patches the Deployment restart annotation.

An accepted API patch is not proof that the application has recovered. Independent rollout verification is handled by B23.

### 6.2 Ansible Adapter

Ansible is an automation tool used to configure systems and execute infrastructure tasks.

The B22 Ansible adapter supports a restricted service-restart operation.

It uses:

- A trusted inventory file.
- A trusted playbook path.
- A configured host alias.
- A fixed command structure.
- Restricted execution parameters.
- `shell=False`.
- A timeout.
- Signed authorization verification.
- Execution disabled by default.

An inventory describes the systems Ansible can manage.

The adapter does not allow an AI-generated request to freely supply arbitrary shell commands or unrestricted playbook paths.

The implementation uses the system `ansible-playbook` executable.

Ansible Runner is not required for this initial restricted execution design. It is a separate execution and integration framework that can be considered later if TAP requires more advanced Ansible job management, structured event handling or process isolation.

### 6.3 Execution Dispatcher

The dispatcher coordinates the execution of prepared actions.

It checks that the supplied actions and resource inputs match the authorized plan.

It then processes actions in sequence.

Important behaviours include:

- Plan and grant consistency checks.
- Duplicate action rejection.
- Complete plan coverage checks.
- Resource-safety assessment before execution.
- Adapter validation.
- Adapter-side authorization verification.
- Execution result validation.
- Failure recording.
- Sequential execution.
- Stopping after an unsuccessful action.
- Marking later actions as not started.

The dispatcher records identifiers and timestamps needed to trace each execution attempt.

A partial execution is distinguishable from a complete successful execution.

A dispatcher success response does not mean the infrastructure has been independently verified.

**B22 reported test evidence:** 32 tests passed.

## 7. B23 — Independent Verification and Durable Recording

B23 closes the execution lifecycle by checking what actually happened after an operation was dispatched.

### 7.1 Independent Verification

Verification means checking the resulting system state rather than simply trusting the execution tool's response.

For example:

- A successful Kubernetes API patch does not prove that the Deployment rollout completed.
- A successful Ansible process exit does not independently prove that the intended service is healthy.

B23 provides Kubernetes and Ansible verification components.

The VerificationEngine routes execution records to the appropriate verifier and validates the returned results.

Verification outcomes include:

| Status | Meaning |
|---|---|
| VERIFIED | The required state was independently confirmed |
| FAILED | Verification found that the required state was not achieved |
| UNVERIFIED | The system could not establish the required state |
| SKIPPED | No applicable verifier was configured or verification was not required |

A skipped or unverified action must not be reported as independently verified.

### 7.2 Verification Recording Service

The VerificationRecordingService coordinates the verification and recording stages.

It receives a dispatch result, asks the VerificationEngine to verify it and passes the resulting report to the recorder.

### 7.3 Append-Only Recording

An append-only recorder is designed to add records without allowing ordinary updates or deletions.

B23 provides an in-memory recorder and a durable SQLite recorder.

SQLite is a lightweight relational database stored in a database file.

The SQLite recorder includes:

- A structured dispatch-record table.
- Dispatch identifiers.
- Execution and verification information.
- Timestamps.
- JSON payload storage.
- Duplicate dispatch protection.
- Transactional recording.
- Database triggers that reject UPDATE and DELETE operations.
- Record retrieval and listing.

A database trigger is a rule that runs automatically when a database operation is attempted.

These controls protect against ordinary modification through the recorder's database operations. They do not make the database cryptographically tamper-proof against an attacker who can directly alter or replace the database file.

### 7.4 Verification Failure Boundary

The Kubernetes and Ansible verifiers handle their expected operational failure paths and can return `UNVERIFIED`.

The VerificationEngine also validates result structure and identity.

Unexpected internal exceptions and invalid or mismatched verifier results remain explicit errors. The current service does not guarantee a durable verification-attempt record when the engine raises before producing a report.

This limitation is documented rather than hidden by converting every internal exception into an ordinary verification result.

**B23 reported test evidence:** 39 tests passed.

## 8. Test Evidence

The latest reported module-level test results are:

| Module | Passing tests |
|---|---:|
| B20 | 56 |
| B21 | 214 |
| B22 | 32 |
| B23 | 39 |
| **Total reported across module results** | **341** |

The B21–B23 results were reported as 214, 32 and 39 passing tests respectively, giving 285 passing tests across those three modules.

The B20 result is an earlier reported baseline of 56 passing tests.

These figures are module-level results. They should not be interpreted as proof that all 341 tests were executed together in one clean full-repository run.

The B23 integration test demonstrates a software-level lifecycle:

1. A simulated dispatch is created.
2. The execution result is passed to the verification engine.
3. Kubernetes state is checked using a fake API client.
4. The verification report is recorded in SQLite.
5. A new recorder instance reopens the database.
6. The dispatch and verification information are restored.

This demonstrates integration between the software components and durable recording. It does not demonstrate a live production Kubernetes recovery.

## 9. Security and Reliability Principles

The B20–B23 architecture follows several important engineering principles.

**Least privilege:** Components should receive only the permissions required for their assigned responsibility.

**Separation of duties:** Planning, policy evaluation, authorization, execution and verification are separate responsibilities.

**Fail-closed behaviour:** If required safety or authorization evidence is missing, the system should not proceed with autonomous execution.

**Plan-bound authorization:** Permission applies to the intended plan rather than unrestricted future operations.

**Independent verification:** The execution tool's response is not treated as proof of recovery.

**Auditability:** Execution attempts and verification results are recorded for later inspection.

**Controlled automation:** Restricted operations are preferred over unrestricted command execution.

## 10. Known Limitations and Work Remaining

The following limitations must remain visible when assessing the project's maturity.

| Area | Current position |
|---|---|
| Human approval | Workflow state exists; complete approval and resume integration remains |
| Live resource telemetry | Simulated resource assessment exists; live evidence freshness needs implementation |
| Kubernetes | Restricted adapter and verifier tested with software-level test coverage; live infrastructure validation remains |
| Ansible | Restricted adapter and verifier implemented; live target validation remains |
| Audit storage | SQLite append-only protections exist; external tamper-proof storage is not implemented |
| Unexpected verifier exceptions | Propagate as errors; durable exception-attempt recording is not guaranteed |
| Production deployment | B24 migration and cloud deployment remain |
| AI agent integration | Deliberately outside the current execution foundation |
| Local AI model | Deliberately deferred until after migration and platform stabilization |

## 11. Technical Glossary

| Term | Simple definition |
|---|---|
| SRE | Site Reliability Engineering: applying engineering methods to keep services reliable |
| Platform Engineering | Building and operating shared systems that help applications and engineering teams work reliably |
| Agentic DevOps | Using AI agents to assist operational and development tasks through controlled workflows |
| RCA | Root Cause Analysis: identifying the underlying cause of an incident |
| RAG | Retrieval-Augmented Generation: retrieving relevant knowledge before an AI generates an answer |
| Policy | Rules that determine whether an operation is permitted |
| Authorization | Trusted permission to perform a specific operation |
| Digital signature | Cryptographic proof that data was signed by a holder of a private key |
| Hash | A fixed-length digest used to identify data and detect changes |
| Adapter | A controlled connection between TAP and an external execution system |
| Dispatcher | The component that coordinates permitted execution actions |
| Idempotency | A property where repeating an operation does not create an unintended additional effect |
| Replay protection | Preventing a previously used authorization from being reused improperly |
| Resource gate | A check that determines whether infrastructure has enough safe capacity |
| Verification | Checking the resulting system state after an operation |
| Append-only | A recording approach designed to add entries without changing or deleting existing entries |
| Fail-closed | Refusing to proceed when required safety or authorization checks cannot be satisfied |
| Deployment | A Kubernetes resource that manages application replicas and updates |
| Inventory | An Ansible file or configuration that describes managed hosts |
| CI/CD | Continuous Integration and Continuous Delivery/Deployment: automated build, test and release processes |
| Infrastructure as Code | Managing infrastructure through version-controlled configuration rather than manual changes |

## 12. Next Engineering Milestone

The next milestone is B24: Server B migration and cloud deployment.

The immediate focus is to migrate the existing platform, establish a reproducible deployment process, validate the environment and stabilize the infrastructure.

Further work will extend into cloud provisioning, networking, VPN connectivity, resource optimization, Server C and broader SRE capabilities.

The AI agent and local model integration will follow platform stabilization rather than being introduced before the execution and deployment foundation is ready.

## 13. Conclusion

B20–B23 establish a meaningful foundation for governed infrastructure remediation.

The work demonstrates how policy evaluation, trusted authorization, resource-safety assessment, restricted execution adapters, independent verification and durable recording can be separated into distinct engineering responsibilities.

The project is not presented as a finished enterprise production platform. It is a tested and evolving engineering implementation with explicit boundaries, evidence and remaining work.

The central objective is to make infrastructure automation more controlled, traceable and reliable while retaining the ability to introduce AI assistance without giving AI unrestricted execution authority.

**AI Everywhere. Authority Controlled. Execution Governed. Everything Recorded.**

## 14. Regression Validation Update — 20 November 2026

A new combined regression test was executed against the B20, B21, B22 and B23 test suites on 20 November 2026.

**Repository checkpoint:**
- Branch: `main`
- Commit: `9e1d801`
- Remote synchronization: `main` matched `origin/main` before this documentation update.

**Command executed:**

```bash
.venv-b20/bin/python -m pytest \
  modules/B20/tests \
  modules/B21/tests \
  modules/B22/tests \
  modules/B23/tests -q
```

**Actual result:**

```text
345 passed in 2.78s
```

**Result: PASS.**

All four module test suites passed together in one regression run. This provides current combined software-level regression evidence for the B20–B23 implementation at the recorded repository checkpoint.

**Reconciliation with earlier test figures:**

Section 8 records earlier module-level results totalling 341 tests (B20: 56, B21: 214, B22: 32 and B23: 39). The new combined run reports 345 passing tests. The four-test difference has not been attributed to a particular module because individual module totals were not captured in this combined run. The earlier figures are retained as historical results; 345 is the latest verified combined regression result.

**Evidence boundary:**

This test result demonstrates passing automated software tests. It does not establish successful live remediation against production Kubernetes clusters, live Ansible-managed hosts, or a fully deployed production TAP environment. Those remain separate validation objectives.
