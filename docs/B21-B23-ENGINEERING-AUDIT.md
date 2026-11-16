# TAP Server B — B21–B23 Engineering Audit

**Project:** Tawanitech Automation Platform (TAP)
**Audit scope:** B21 Trusted Execution Foundation, B22 Controlled Infrastructure Adapters, B23 Independent Verification and Recording
**Repository:** `joseph-tawanitech/serverb-platform-engineering`
**Branch:** `main`
**Audit evidence date:** 17 November 2026
**Audit type:** Source-code, test, integration, execution-tooling and Git repository review

---

## 1. Executive Summary

This audit examines the implementation and integration state of TAP Server B's B21–B23 execution architecture.

The intended architecture provides a governed path from a remediation proposal to an infrastructure change and independently verified result.

The governing principle is:

> AI proposes → TAP evaluates → Policy authorizes → Trusted authorization permits → Controlled execution acts → Independent verification proves → Recorder records.

The audit finds that B21 has a substantial trusted-execution foundation, including adapter contracts, plan routing, risk assessment, resource-safety assessment, trusted authorization, workflow transitions, and execution-record contracts.

B22 introduces a controlled execution dispatcher and a Kubernetes adapter. Its tests demonstrate guarded dispatch, resource-safety checks, adapter authorization validation, result validation, and a B21 preparation-to-B22 dispatch integration path.

However, the current implementation is not yet a complete production execution lifecycle:

- B21 risk assessment is not fully bound to the trusted authorization decision.
- The resource-safety implementation uses supplied or simulated readings rather than live infrastructure telemetry.
- The B22 dispatcher returns execution records in memory; durable recording is not established.
- The Kubernetes adapter has a narrow operation scope and does not independently prove rollout completion.
- The Ansible adapter is not implemented in B22.
- Ansible Runner has been installed and tested separately, but those tests do not establish a TAP-controlled Ansible execution channel.
- No B23 implementation directory or B23 test suite was found in the inspected repository state.
- Independent verification, durable audit recording, and reconciliation of uncertain or partially completed operations remain outstanding.

**Overall conclusion:** B21 is a substantial but incompletely integrated execution foundation. B22 has a tested Kubernetes execution path, but the wider execution architecture is incomplete. B23 remains an identified requirement and proposed implementation stage, not an existing capability.

---

## 2. Audit Classification

This report uses four classifications.

| Classification | Meaning |
|---|---|
| Implemented and tested | Source code exists and tests demonstrate the stated behaviour. |
| Implemented but incompletely integrated | Code exists, but a required end-to-end connection or control is missing. |
| Identified gap | Required behaviour is absent, incomplete or not proven by the inspected evidence. |
| Proposed future work | A recommended design or implementation requirement; not an existing capability. |

A passing unit or integration test does not establish production readiness. Test results must be interpreted according to the environment in which they ran.

---

## 3. Architecture and Responsibility Boundaries

### 3.1 Intended lifecycle

The intended lifecycle is:

1. Task intake and investigation.
2. Evidence gathering and root-cause analysis.
3. Remediation proposal and plan creation.
4. Plan routing and channel selection.
5. Risk and resource-safety assessment.
6. Policy evaluation.
7. Trusted authorization.
8. Controlled adapter dispatch.
9. Independent target-state verification.
10. Durable recording of execution and verification evidence.

The architecture separates decision-making, authorization, execution and verification.

### 3.2 Component responsibilities

| Component | Responsibility |
|---|---|
| B15 AI Gateway | Model-independent interface for AI requests and responses. Its actual integration state must be assessed separately from B21–B22 execution. |
| B17–B19 | Prompt framework, root-cause analysis and retrieval-augmented evidence capabilities. |
| B20 Policy Engine | Evaluates whether an action satisfies configured policy requirements. |
| B21 | Defines the trusted execution foundation: contracts, routing, resource and risk assessments, authorization coordination and workflow state. |
| B22 | Dispatches approved actions through controlled infrastructure adapters. |
| B23 | Independently verifies actual target state and records the execution and verification history. |

**Important boundary:** An adapter executes a permitted operation. It does not decide that the operation should be permitted. A successful adapter response is not equivalent to independent verification.

---

## 4. B21 — Trusted Execution Foundation

### 4.1 Purpose

B21 establishes the contracts and controls needed to move from a remediation plan to a potentially executable, governed action.

Its responsibilities include:

- Defining remediation task, plan and action contracts.
- Selecting and routing actions to execution channels.
- Assessing action risk.
- Assessing resource safety.
- Coordinating policy and trusted authorization.
- Defining adapter contracts.
- Managing execution workflow transitions.
- Defining execution-record and dispatch-result structures.

### 4.2 Implemented and tested

The inspected B21 source includes:

- Adapter contracts and registry.
- Adapter dispatcher contracts.
- Channel selection and plan routing.
- Risk-assessment structures and logic.
- Resource-safety assessment logic.
- Trusted authorization coordination.
- Authorization and ledger components.
- Workflow state transitions.
- Action execution and dispatch-result contracts.

The B21 tests demonstrate these components' defined behaviours.

**Recorded test evidence:** The full B21 test suite passed with **214 tests** in the latest recorded run.

This proves the tested code paths in the local test environment. It does not prove live infrastructure execution, durable persistence or complete production integration.

### 4.3 Adapter contract

The `RemediationAdapter` protocol defines the expected adapter interface.

It requires:

- `adapter_id`
- `supported_channels`
- `supported_operations`
- `validate_execution_request(request)`
- `execute_approved_request(request)`

The contract allows an adapter to be implemented as a local process integration or a remote service client.

The adapter must independently enforce authorization before executing an operation.

The associated `AdapterExecutionRequest` carries the task, plan, individual action, selected route, routed actions and authorization grant.

The request validation checks consistency between task, plan, action, route and grant identifiers. The adapter remains responsible for verifying the grant itself.

The `AdapterExecutionResult` provides structured execution information, including action and target identity, status, timestamps, message and evidence identifiers.

**Classification:** Implemented and tested as contracts. The existence of a contract does not mean every planned adapter has been implemented.

### 4.4 Risk assessment

B21 includes a deterministic risk-assessment component.

The assessor aggregates supplied evidence classifications into an assessment. It does not independently discover infrastructure facts, interpret arbitrary evidence or establish the authenticity of the evidence supplied to it.

A critical integration gap remains in the trusted authorization path:

- B21's trusted authorization service passes `risk=self._policy.max_risk` to B20.
- It does not bind the actual per-action `ActionRiskAssessment` to the authorization decision.
- The remediation plan does not currently provide a complete per-action risk-assessment binding.

Consequently, the presence of a risk assessor does not prove that every action is authorized according to its own assessed risk.

**Classification:** Risk-assessment logic implemented and tested; end-to-end risk-to-authorization integration incomplete.

### 4.5 Resource Safety Gate

B21 includes a resource-safety assessment mechanism.

The inspected implementation uses resource readings and impact information supplied to the assessment. Its configured thresholds include:

| Resource | Review threshold | Hard threshold |
|---|---:|---:|
| RAM | 80% | 90% |
| CPU | 85% | 95% |
| Disk | 80% | 90% |

The assessment can return:

- `ALLOW`
- `NEEDS_HUMAN`
- `BLOCK`

Missing or inadequate readings must not be treated as evidence that the environment is safe.

The B22 dispatcher consumes a resource-safety assessment before adapter authorization and execution.

However, the inspected implementation does not establish live telemetry collection or continuous monitoring. The assessment is not yet a complete operational integration with infrastructure monitoring.

**Classification:** Assessment logic implemented and tested; live telemetry integration and operational enforcement remain incomplete.

### 4.6 Trusted authorization

The inspected B21 authorization design includes:

- B20 policy evaluation.
- Ed25519-signed authorization grants.
- Plan-bound authorization data and digest checks.
- Trusted issuer public-key verification.
- Replay-protection logic through an authorization ledger.
- Workflow checks associated with authorization.

Important limitations:

1. The risk passed to B20 is not the actual per-action assessment.
2. A valid Ed25519 signature establishes that the grant was signed by the corresponding private key. It does not, by itself, prove the real-world identity of the human named in an `approved_by` field.
3. The inspected ledger is in-memory and is not a durable, multi-process authorization store.
4. The inspected B21 flow consumes grants, but a complete integrated issuance, registration and revocation lifecycle was not established.
5. The adapter integration tests can construct and sign grants directly. Those tests therefore do not prove the complete B20-to-B21-to-B22 governance chain.

**Classification:** Cryptographic authorization checks and associated tests implemented; complete production authorization lifecycle and identity assurance remain gaps.

### 4.7 Workflow and execution records

The B21 workflow includes states such as:

- `UNVERIFIED`
- `NEEDS_HUMAN`
- `BLOCKED`
- `AUTHORIZED`
- `EXECUTING`
- `VERIFYING`

The execution status contract includes:

- `NOT_STARTED`
- `PREPARED`
- `BLOCKED`
- `EXECUTING`
- `SUCCEEDED`
- `FAILED`
- `TIMED_OUT`
- `UNKNOWN`

`ActionExecutionRecord` is a frozen data structure containing identifiers and execution information, including:

- Dispatch ID.
- Attempt ID and attempt number.
- Task, plan and action IDs.
- Adapter ID and selected channel.
- Grant ID.
- Execution status.
- Preparation and relevant authorization/resource timestamps.
- Adapter result.
- Failure code and failure message.

`DispatchResult` groups action records and validates their shared dispatch, task, plan and grant identity, as well as uniqueness constraints.

These structures provide a useful basis for structured execution history.

However:

- They are in-memory data structures.
- Durable storage is not established.
- Append-only history is not established.
- The result validator does not independently prove that the overall dispatch status was correctly recomputed from all action statuses.
- Record existence does not prove that a trusted, durable recorder has persisted the record.

**Classification:** Execution-record contracts implemented and tested; durable audit recording not implemented or not proven.

### 4.8 B21 nine-part capability assessment

| Audit question | Finding |
|---|---|
| Purpose | Establish governed execution foundations. |
| Governing principle | Execution must follow policy and trusted authorization. |
| How it works | Contracts, routing, assessment, authorization and workflow transitions. |
| What it permits | Preparation and controlled progression of valid actions through defined workflow states. |
| What it prohibits | Treating preparation or an AI proposal as authorization to execute. |
| Failure behaviour | Invalid or missing evidence and authorization checks should prevent progression; workflow states include blocked and human-review outcomes. |
| Verification | B21 unit and integration tests; 214 tests passed in the recorded full-suite run. |
| Current status | Substantial implementation; several end-to-end integration and persistence gaps remain. |
| Practical example | A remediation action is routed, assessed and checked against policy and a trusted grant before an adapter can execute it. |

---

## 5. B22 — Controlled Infrastructure Adapters

### 5.1 Purpose

B22 provides the controlled execution layer between B21-approved actions and infrastructure-specific tools or APIs.

The design supports separate adapters for different execution technologies.

The inspected implementation contains:

- An execution dispatcher.
- A Kubernetes adapter.
- Tests for dispatcher behaviour.
- Tests for Kubernetes adapter behaviour.
- Tests for B21 preparation-to-B22 Kubernetes dispatch integration.

The inspected B22 package does not contain an Ansible adapter or Service API adapter.

### 5.2 Execution dispatcher

The B22 dispatcher performs the following sequence:

1. Validates the prepared actions.
2. Checks task, plan and grant consistency.
3. Checks unique action identifiers and complete plan coverage.
4. Validates the resource-input mapping.
5. Obtains and validates the resource-safety assessment.
6. Blocks execution for hard-limit, review-required or invalid assessment outcomes.
7. Calls the adapter's `validate_execution_request()` method.
8. Calls the adapter's execution method only after validation succeeds.
9. Validates the returned result and checks that its identity matches the requested action.
10. Converts the adapter outcome into an `ActionExecutionRecord`.
11. Returns a `DispatchResult`.

The dispatcher executes actions sequentially in plan order.

When an action does not succeed, later actions are not started. They are recorded with `NOT_STARTED` and `PREVIOUS_ACTION_NOT_SUCCESSFUL`.

This is important because a multi-action plan may stop after a partial execution.

#### Failure handling

| Condition | Dispatcher behaviour |
|---|---|
| Resource assessment fails or is invalid | Blocks the action. |
| Resource decision is `BLOCK` | Blocks with `RESOURCE_HARD_LIMIT`. |
| Resource decision is `NEEDS_HUMAN` | Blocks with `RESOURCE_REVIEW_REQUIRED`. |
| Adapter validation raises an exception | Blocks with `ADAPTER_VALIDATION_REJECTED`. |
| Adapter execution raises an exception | Records `UNKNOWN` because a remote side effect may already have occurred. |
| Adapter result is invalid or mismatched | Records `UNKNOWN` with `INVALID_ADAPTER_RESULT`. |
| Adapter reports success | Records execution success, but independent verification is still required. |

The `UNKNOWN` outcome is especially important. A timeout or transport exception does not prove that the target system did nothing. Retrying immediately could duplicate or compound an operation.

The dispatcher currently returns its records in memory. A durable recorder and a reconciliation workflow for uncertain outcomes are not established.

**Classification:** Dispatcher implementation and tested behaviour are present; persistent recording, reconciliation and human-review resumption remain incomplete.

### 5.3 Kubernetes adapter

#### Implemented scope

The concrete adapter ID is:

`tap-b22-kubernetes`

Its supported operation is:

`restart_deployment`

The adapter uses a Kubernetes Apps API client and a configured mapping of permitted targets.

It validates:

- The execution request.
- The selected Kubernetes channel.
- The supported operation.
- The configured target.
- The allowed namespace.
- The absence of unsupported action parameters.
- The Ed25519 authorization grant.
- Whether execution is enabled.

Execution is disabled by default.

The restart operation patches the Deployment's pod-template annotation:

`kubectl.kubernetes.io/restartedAt`

The adapter uses a UTC timestamp for the restart annotation.

#### Execution outcomes

The adapter distinguishes outcomes such as:

- API rejection.
- Successful patch acceptance.
- Timeout or transport uncertainty.
- Unexpected or unclassified response.

An accepted patch means the Kubernetes API accepted the request. It does not prove that the Deployment rollout completed successfully or that the intended replicas became ready.

That verification belongs in B23.

#### Security controls

The inspected adapter includes:

- Explicit trusted issuer public keys.
- Signature verification.
- Configured target restrictions.
- Namespace allowlisting.
- Operation allowlisting.
- Execution disabled by default.
- Request validation before execution.
- Result status classification.

#### Limitations

The inspected implementation does not establish:

- A live Kubernetes rollout verifier.
- A Kubernetes RBAC manifest or deployed least-privilege service account.
- Live resource telemetry integration.
- A complete B20 policy and B21 trusted authorization integration in its adapter tests.
- Production deployment or live-cluster verification.

The tests use a fake Kubernetes API client. They prove tested adapter behaviour, not a successful operation against a live cluster.

The adapter's success outcome is therefore an execution acknowledgement, not proof of the desired final infrastructure state.

**Classification:** Kubernetes adapter implemented and tested against fake API behaviour; full governance integration and independent live-state verification remain incomplete.

---

## 6. Ansible Execution Channel Audit

### 6.1 Current status

The intended second infrastructure remediation channel is Ansible.

The inspected B22 source does not contain:

- An Ansible adapter implementation.
- An Ansible Runner integration.
- An Ansible Runner dependency in the B22 package.
- A structured B22 Ansible execution-result integration.

The existence of Ansible on Server B does not mean TAP has implemented an Ansible execution adapter.

**Classification:** Ansible tooling is installed and has been exercised separately; TAP's B22 Ansible adapter is not implemented.

### 6.2 Ansible execution tool responsibilities

The intended execution chain is:

`B22 Ansible Adapter → Ansible Runner → ansible-playbook → Ansible modules → Target infrastructure`

The responsibilities are different:

| Tool or component | Responsibility |
|---|---|
| B22 Ansible Adapter | Receives a governed action, validates its scope and authorization, constructs a controlled execution request and returns structured results. |
| Ansible Runner | Provides a programmatic interface for launching and supervising Ansible jobs, collecting status and execution events. |
| `ansible-playbook` CLI | Executes the Ansible playbook engine. Runner invokes the Ansible execution process; Runner does not replace the playbook engine. |
| Ansible modules | Perform the actual work, such as managing files, packages, services or infrastructure resources. |
| Inventory | Identifies the hosts and connection information used by the playbook. |
| Target infrastructure | The machines or services on which the Ansible modules perform operations. |
| B23 verifier | Independently checks the resulting target state rather than relying only on Ansible's reported job status. |
| B23 recorder | Persists the execution and verification evidence in a controlled audit history. |

### 6.3 Installed tooling evidence

The system installation was inspected:

- `ansible-playbook` is available at `/usr/bin/ansible-playbook`.
- Ansible Core version: `2.20.1`.
- Python version: `3.14.4`.
- The system Python can import `ansible_runner` from `/usr/lib/python3/dist-packages/ansible_runner/`.
- The `.venv-b20` virtual environment cannot import `ansible_runner`.

The system-wide Runner installation is not the same as a declared dependency in the B22 Python package.

The `ansible-runner` CLI reported `0.0`; that output should not be interpreted as the installed Python package version.

### 6.4 Runner smoke-test evidence

Three historical Runner artifact directories were inspected. Their identifiers included:

- `78284213-3de3-4e02-97be-864acd8fe283`
- `b21-preintegration-check`
- `c9639266-57a4-4122-8e6f-bc346eef26af`

The historical jobs completed successfully with:

- `rc=0`
- `ok=1`
- `changed=0`
- `unreachable=0`
- `failed=0`

The associated playbook used the localhost inventory and Ansible ping module.

This demonstrates a successful local Ansible Runner smoke test. It does not demonstrate remote infrastructure remediation or B22 integration.

### 6.5 Controlled Runner behaviour tests

Separate controlled tests were conducted in an isolated temporary directory.

#### Test A — Successful change

A local playbook used the Ansible copy module to create a file in a temporary path.

Observed result:

- Runner status: successful.
- Runner return code: `0`.
- Event: `runner_on_ok`.
- Task result: `changed=true`.
- Play recap: `ok=1`, `changed=1`.

This demonstrates that Runner can supervise an actual local filesystem change.

#### Test B — Partial execution and failure

A second local playbook:

1. Created a file using the copy module.
2. Executed a later command that failed using `/bin/false`.

Observed result:

- Runner status: failed.
- Runner return code: `2`.
- Task-level return code: `1`.
- A prior task had already changed the filesystem.
- Failure event: `runner_on_failed`.
- Play recap: `ok=1`, `changed=1`, `failures=1`.

This demonstrates why a failed Ansible job must not be treated as proof that no changes occurred.

The Runner job status and the task-level return code are different pieces of evidence. A failed playbook can leave earlier successful changes in place.

These experiments were local and isolated. They do not establish multi-host execution, remote-host failure handling or a production remediation channel.

### 6.6 Runner event and artifact considerations

Runner exposes structured job status, return codes, events and artifacts.

Inspected event types included:

- `playbook_on_start`
- `playbook_on_play_start`
- `playbook_on_task_start`
- `runner_on_start`
- `runner_on_ok`
- `runner_on_failed`
- `playbook_on_stats`

Event payloads may include task output, module results, invocation details, variables or other potentially sensitive information.

A future TAP integration must not indiscriminately persist raw Runner events.

The integration should consider:

- Event ordering using the event counter.
- Start and completion timestamps.
- Job identity and return code.
- Host-level results.
- Task-level success and failure.
- Changed and unreachable counts.
- Partial execution.
- Sanitised evidence references.
- Secret and sensitive-data redaction.
- Artifact retention and access controls.

The repository's `.gitignore` includes rules for Ansible Runner artifacts and environment directories. These rules reduce the risk of accidentally tracking generated artifacts, but they do not encrypt files or protect them from local access.

### 6.7 Proposed Ansible integration

The recommended future architecture is:

`B22 Ansible Adapter → Ansible Runner Python API → ansible-playbook → Ansible modules → Target infrastructure → B23 verification`

The B22 adapter should:

1. Accept only a valid governed execution request.
2. Check the action, target, inventory and permitted playbook scope.
3. Verify the trusted authorization independently.
4. Use a controlled Runner configuration and environment.
5. Restrict credentials and execution privileges.
6. Launch the intended playbook.
7. Collect structured Runner status and events.
8. Preserve evidence of partial execution and failures.
9. Return a structured adapter result to B22.
10. Leave independent target-state verification to B23.

Runner should be evaluated as the programmatic backend for TAP. The `ansible-playbook` CLI remains useful for learning, playbook development, manual diagnostics and controlled testing.

Runner does not replace Ansible Core, playbooks or modules.

**Classification:** Proposed future integration. Not implemented in B22.

---

## 7. Other Planned Execution Channels

The B21 channel vocabulary includes:

- `kubernetes`
- `ansible`
- `service_api`

The inspected B22 package implements only the Kubernetes adapter.

No concrete Service API adapter was found in the inspected B22 source.

A channel identifier or adapter contract must not be confused with an operational adapter.

| Channel | Current evidence |
|---|---|
| Kubernetes | B22 adapter implemented and tested using a fake Kubernetes API client. |
| Ansible | System tooling installed and separately tested; B22 adapter absent. |
| Service API | Channel vocabulary exists; concrete B22 adapter not found. |
| Terraform/OpenTofu | Not part of the immediate B21–B23 execution scope; deferred. |

Future adapters should be added only when their responsibilities, trust boundaries, permitted operations, dependencies, failure semantics and verification requirements are explicitly defined.

---

## 8. B23 — Independent Verification and Recording

### 8.1 Repository audit result

The inspected repository contains `modules/B21` and `modules/B22`.

No `modules/B23` implementation directory or B23 test suite was found.

The inspected Git history did not reveal B23 commits in the available refs.

The only relevant B23 source reference found was in the Kubernetes adapter. It explains that accepting a Deployment restart patch does not mean the rollout has completed and that B23 must verify the result.

**Conclusion:** B23 is not implemented in the inspected repository state. Its responsibilities are identified requirements, not existing capabilities.

### 8.2 Purpose

B23 should provide independent proof of the actual target state after B22 attempts an operation.

It must not simply repeat or trust the execution adapter's success message.

Its purpose is to answer:

- Did the target system reach the requested state?
- Does the observed state match the authorized expected state?
- Did the operation partially succeed?
- Is the result uncertain?
- Is it safe to retry?
- What evidence supports the verification result?
- Has the execution and verification history been durably recorded?

### 8.3 Proposed verification responsibilities

#### Kubernetes

A Kubernetes verifier should independently inspect the target Deployment and relevant workload state.

Potential checks include:

- Deployment existence and identity.
- Desired and observed generation.
- Desired and available replica counts.
- Updated and ready replicas.
- Rollout progress.
- Timeout behaviour.
- Pod readiness and relevant failure conditions.

An accepted restart patch is not equivalent to a completed rollout.

#### Ansible

An Ansible verifier should inspect actual target state independently of Runner's job status.

It should account for:

- Per-host results.
- Per-task outcomes.
- Changed tasks.
- Failed tasks.
- Unreachable hosts.
- Partial changes.
- Final target-state observations.

A successful Runner job does not necessarily prove that the desired business or infrastructure state exists. A failed job does not prove that no changes occurred.

### 8.4 Proposed verification outcomes

B23 should distinguish at least:

| Outcome | Meaning |
|---|---|
| `VERIFIED` | Independent observations prove the expected state. |
| `VERIFICATION_FAILED` | The observed state contradicts the expected state or the verification criteria fail. |
| `UNVERIFIED` | Evidence is unavailable, incomplete, inconsistent or insufficient to establish the result. |

Execution status and verification status must remain separate.

For example:

- Adapter execution: `SUCCEEDED`
- Verification: `VERIFICATION_FAILED`

This means the tool accepted or completed the operation, but the intended state was not established.

Another example:

- Adapter execution: `UNKNOWN`
- Verification: `UNVERIFIED`

This means the outcome is uncertain and further reconciliation is required.

### 8.5 Proposed reconciliation

An uncertain or partially completed operation must not be blindly retried.

B23 should help determine:

1. Whether the target operation occurred.
2. Which parts of the plan completed.
3. Which targets or hosts changed.
4. Which actions remain outstanding.
5. Whether retrying is safe and idempotent.
6. Whether human review is required.

This is especially important for Ansible playbooks that can complete earlier tasks before a later task fails.

### 8.6 Proposed durable recording

B23 should provide a durable record of:

- Task and plan identity.
- Action and attempt identity.
- Authorization grant reference.
- Adapter and channel.
- Execution start and completion times.
- Execution status.
- Failure details.
- Adapter result and evidence references.
- Verification start and completion times.
- Verification outcome.
- Observed state and expected state.
- Reconciliation decisions.
- Human approval or review references where applicable.

The recording system should support append-only history and tamper-evident evidence.

Raw logs and events should be redacted and stored under controlled access and retention policies.

A useful future relationship is:

`ActionExecutionRecord → AdapterExecutionResult → Structured Adapter Evidence → Verification Result → Durable Audit Record`

For Ansible, structured evidence may include Runner job identity, status, return code, task events, host results, changed/failed/unreachable counts and sanitised artifact references.

This evidence model is a proposal, not an existing implementation.

### 8.7 B23 nine-part capability assessment

| Audit question | Finding |
|---|---|
| Purpose | Independently prove the final infrastructure state and preserve audit evidence. |
| Governing principle | Execution acknowledgement is not verification. |
| How it works | Proposed independent observation, expected-state comparison, reconciliation and recording. |
| What it permits | Verified completion, controlled recovery and evidence-based operational decisions. |
| What it prohibits | Treating adapter success or AI assertions as proof of target-state success. |
| Failure behaviour | Distinguish failed verification from unavailable or inconclusive evidence; avoid blind retries. |
| Verification | No B23 implementation or test evidence found. |
| Current status | Not implemented in the inspected repository. |
| Practical example | After a Kubernetes restart request, inspect Deployment rollout and replica readiness before marking the action verified. |

---

## 9. Git and GitHub Repository Audit

### 9.1 Repository state

The latest inspected Git state showed:

- Branch: `main`.
- Remote: `origin`.
- Last known `origin/main` commit: `2a5e40c30e5c7eabac7f57151afc493dd0574bb7`.
- Local commits ahead of the remote included:
  - `e4ba9bb feat(B21): add adapter dispatcher contracts`
  - `71df214 feat(B21): add adapter preparation`

The working tree contained modified tracked files and untracked source directories.

#### Modified tracked files

- `modules/B20/src/tap_b20/policy_engine.py`
- `modules/B20/tests/test_action_service.py`
- `modules/B21/src/tap_b21/workflow.py`
- `modules/B21/tests/test_workflow.py`

#### Untracked files and directories

- `modules/B21/src/tap_b21/adapter_dispatcher.py.d1-backup`
- `modules/B21/src/tap_b21/resource_safety.py`
- `modules/B21/src/tap_b21/risk_assessor.py`
- `modules/B21/tests/test_resource_safety.py`
- `modules/B21/tests/test_risk_assessor.py`
- `modules/B22/`

The untracked B22 package contains its package configuration, source and tests.

These files were present in the working tree but were not established as committed repository content by the inspected Git status.

**Important:** A passing test against untracked code is valid local test evidence, but it does not mean the implementation has been committed or delivered to GitHub.

### 9.2 Git delivery status

The audit must distinguish:

- Local source changes.
- Local commits.
- Remote branch state.
- Untracked implementation.
- Test evidence.
- GitHub-delivered implementation.

The latest known state showed local commits ahead of `origin/main`, plus additional uncommitted and untracked changes.

Therefore, the inspected state was not a clean, fully synchronised delivery state.

No conclusion should be drawn that all current B21–B22 work is already available on GitHub.

### 9.3 Ansible repository contents

The inspected tracked Ansible files included:

- `ansible/b11-integration/inventory/hosts`
- `ansible/b11-integration/site.yml`
- `ansible/runner-test/inventory/hosts`
- `ansible/runner-test/project/site.yml`

The inspected inventories and playbooks were localhost-oriented.

The Runner test playbook used Ansible's ping module against localhost. The B11 integration playbook contained Terraform environment assertions and debug tasks.

No production remote-target Ansible remediation integration was established from these files.

### 9.4 Ignore rules and generated artifacts

The repository `.gitignore` includes rules for:

- Ansible Runner artifacts.
- Ansible Runner environment directories.
- Runner test inventory.
- Secret and credential files.
- Vault password files.

These rules are useful for preventing accidental commits of generated artifacts and sensitive files.

However, `.gitignore` is not a security boundary. It does not encrypt files, prevent local access or provide retention controls.

Generated Python caches, pytest caches and package metadata should also be distinguished from intentional source changes.

### 9.5 CI and delivery evidence

The final repository inspection searched `.github/workflows` and found no workflow files.

Therefore, this audit establishes no repository-defined GitHub Actions workflow configuration or successful GitHub Actions run evidence for B21–B23.

The local pytest results recorded in this report demonstrate successful local test execution. They must not be represented as GitHub Actions or CI results.

The following remain unverified or outstanding:

- Automated test execution in GitHub Actions.
- Dependency installation and package build in CI.
- Python version consistency in CI.
- Security and dependency scanning.
- Branch protection and review requirements.
- Clean-checkout installation and test reproducibility.

These items should be assessed before claiming that a complete CI/CD delivery pipeline is operational.

---

## 10. Test Evidence Summary

The latest recorded test results were:

| Test scope | Result | Evidence limitation |
|---|---:|---|
| B20 | 60 passed | Local automated tests. |
| B21 | 214 passed | Local automated tests. |
| B22 | 22 passed | Fake Kubernetes API and B21 preparation-to-B22 dispatch tests. |
| Ansible Runner smoke tests | 3 successful historical local runs | Localhost ping only. |
| Ansible Runner controlled change test | Successful | Actual local temporary-directory file creation. |
| Ansible Runner partial-failure test | Failed job with earlier change retained | Controlled local failure injection. |
| B23 | No test suite found | No implementation directory found. |

The B20, B21 and B22 results represent **296 passing tests across the three recorded suites**.

These are separate suite counts, not proof of 296 independent production scenarios.

The Ansible experiments are separate from the B22 suite and should not be counted as B22 adapter tests.

### 10.1 Test coverage boundaries

The tests demonstrate important local behaviours, but they do not establish:

- Live Kubernetes cluster execution.
- Successful live Deployment rollout.
- Remote Ansible remediation.
- Multi-host Ansible failure handling.
- Full B20-to-B21-to-B22 authorization integration.
- Live resource monitoring.
- Durable execution recording.
- Independent B23 verification.
- Production IAM and least-privilege deployment.
- Production-grade secret management and evidence retention.

---

## 11. Security and Operational Control Assessment

### 11.1 Authorization boundary

AI-generated plans and adapter requests must not become authorization by themselves.

A future complete execution path must ensure that:

- Policy evaluation is connected to the actual assessed action risk.
- Trusted authorization is plan- and action-bound.
- Adapters verify authorization independently.
- Grant replay protection is durable across relevant processes and restarts.
- Human approval identity is authenticated rather than inferred from a signed field.
- Authorization cannot be bypassed through direct CLI or agent tool access.

### 11.2 Resource safety

The resource-safety mechanism must remain fail-closed.

Missing readings must not be interpreted as safe conditions.

Before production use, live monitoring and resource-impact evidence must be connected to the assessment path. Hard resource limits must not be overridden by an ordinary human approval.

### 11.3 Execution privileges

Infrastructure adapters should use restricted identities.

For Kubernetes, this means a dedicated service account and narrowly scoped RBAC.

For Ansible, this means controlled inventory, credentials, privilege escalation and host scope.

AI agents must not receive unrestricted root or cluster-administrator execution access. They must not gain an alternate route around TAP's policy and authorization controls.

### 11.4 Secrets and evidence

The implementation should ensure:

- Secrets are not stored in source code or committed artifacts.
- Runner environment snapshots and event payloads are reviewed for sensitive information.
- Evidence is redacted before persistence where necessary.
- Evidence access and retention are controlled.
- Audit records are tamper-evident.
- Failure and partial-execution details are retained without exposing credentials.

### 11.5 Unknown execution outcomes

An adapter exception does not prove that no infrastructure change occurred.

The system must preserve `UNKNOWN` as a meaningful status and require reconciliation before retrying an uncertain operation.

---

## 12. Consolidated Capability Matrix

| Capability | Current classification | Evidence / limitation |
|---|---|---|
| B21 adapter contracts | Implemented and tested | Protocol and request/result validation. |
| B21 adapter registry and routing | Implemented and tested | Source and tests inspected. |
| B21 risk assessment | Implemented and tested | Per-action authorization binding incomplete. |
| B21 resource-safety assessment | Implemented and tested | Simulated/supplied readings; no live telemetry integration established. |
| B21 trusted authorization | Implemented but incompletely integrated | Ed25519 and policy checks exist; risk binding, identity assurance and durable ledger remain gaps. |
| B21 workflow | Implemented and tested | In-memory state machine; not an execution engine. |
| B21 execution records | Implemented and tested as data contracts | No durable recorder established. |
| B22 execution dispatcher | Implemented and tested | Sequential dispatch, fail-closed checks and structured results. |
| B22 Kubernetes adapter | Implemented and tested | Fake API tests; narrow restart operation; no live rollout proof. |
| B22 Ansible adapter | Identified gap | No adapter implementation found. |
| Ansible Runner tooling | Installed and separately tested | Local smoke tests and controlled local changes only. |
| B22 Service API adapter | Identified gap | No concrete implementation found. |
| B23 independent verification | Identified gap / proposed work | No B23 module or tests found. |
| B23 durable recording | Identified gap / proposed work | No durable append-only recorder established. |
| Partial-execution reconciliation | Identified gap / proposed work | Dispatcher preserves failure/unknown outcomes but no full reconciliation workflow. |
| GitHub delivery state | Incomplete at audit time | Two local commits ahead of origin/main; modified tracked files and untracked B21/B22 source and audit documentation remain undelivered. |
| GitHub Actions CI | Not established | No files found under `.github/workflows`; no GitHub Actions run evidence inspected. |

---

## 13. Recommended Completion Sequence

The following is a proposed sequence for completing the B21–B23 engineering work. It is not a statement that these tasks have already been implemented.

### Stage 1 — Finalise B21

1. Bind each action's risk assessment to the policy decision and trusted authorization.
2. Establish the complete grant issuance, registration, verification, consumption and revocation lifecycle.
3. Define authenticated human approval identity.
4. Integrate live resource evidence while preserving hard limits and fail-closed behaviour.
5. Clarify workflow transitions for human review, blocked actions and uncertain execution.
6. Define the durable execution-record interface required by B23.

### Stage 2 — Complete B22

1. Preserve and harden the existing Kubernetes adapter.
2. Define and implement the Ansible adapter.
3. Evaluate and integrate Ansible Runner as the programmatic execution backend.
4. Define the structured Ansible job, task and host evidence model.
5. Preserve partial execution and uncertain outcomes.
6. Define the Service API adapter only when its intended scope and security boundary are clear.
7. Add tests for defensive validation branches and adapter failure cases.
8. Test against controlled infrastructure before enabling real execution.

### Stage 3 — Implement B23

1. Define independent verifier contracts.
2. Implement Kubernetes rollout and readiness verification.
3. Implement Ansible target-state verification.
4. Define verification outcomes independently from execution status.
5. Implement reconciliation for unknown and partial outcomes.
6. Implement durable execution and verification recording.
7. Establish append-only and tamper-evident audit history.
8. Add retention, redaction and access-control policies.
9. Test successful, failed, partial, timed-out and inconclusive outcomes.

### Stage 4 — Validate the complete lifecycle

Demonstrate the complete governed lifecycle:

`Task → Investigation → RCA → RAG → Plan → Routing → Risk and Resource Assessment → Policy → Trusted Authorization → B22 Dispatch → Independent B23 Verification → Durable Recording`

Test both successful and failure scenarios.

A passing execution test must not be treated as a passing verification test.

### Stage 5 — Repository and GitHub delivery

Before declaring B21–B23 complete:

1. Review every tracked modification and untracked source file.
2. Remove or explicitly classify temporary backup files.
3. Verify package dependencies and clean installation.
4. Run the complete relevant test suites.
5. Validate GitHub Actions and CI evidence.
6. Review secrets, generated artifacts and ignore rules.
7. Confirm the final commit history and remote synchronisation.
8. Publish the final architecture and operational documentation.

---

## 14. Final Audit Conclusion

The inspected Server B implementation has made meaningful progress toward a governed infrastructure execution platform.

B21 establishes important contracts and controls. B22 demonstrates a controlled Kubernetes execution path with useful validation and failure handling. The separate Ansible Runner experiments establish that Runner can supervise local Ansible jobs and expose useful execution evidence.

However, the architecture is not yet a complete B21–B23 production lifecycle.

The most important remaining work is to connect actual risk assessments to authorization, complete the Ansible adapter, establish independent verification, preserve partial and uncertain outcomes, and implement durable audit recording.

The implementation should not be described as having complete B23 verification or recording, a completed Ansible remediation channel, or a production-ready end-to-end authorization chain.

**Final status:** B21 substantially implemented with integration gaps; B22 partially implemented with a tested Kubernetes adapter; Ansible adapter outstanding; B23 not implemented in the inspected repository state.

The next engineering decisions should be based on this evidence, with no new execution channel or AI-agent integration added until the existing B21–B23 architecture has been completed and validated.
