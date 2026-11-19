# Server B / TAP — Cloud SRE, Platform Engineering & Agentic DevOps Implementation Roadmap

**Project:** TAP — Tawanitech Automation Platform
**Document:** Immediate Server B Deployment Roadmap
**Version:** 2.0
**Date:** 19 November 2026
**Time:** 15:29:55 SAST (UTC+2)
**Status:** Active implementation roadmap

---

## 1. Purpose

This roadmap defines the implementation sequence for migrating, securing, deploying and operating TAP on Server B.

The objective is to establish a reproducible, secure and operationally validated platform that supports SRE, cloud and platform engineering, and governed Agentic DevOps.

This is the immediate implementation roadmap. The separate public master engineering roadmap describes the broader long-term engineering vision. Separate component roadmaps retain detailed requirements for individual platform components.

## 2. Current Engineering Baseline — B21 to B23

The B21–B23 remediation-engine implementation reached its implementation acceptance checkpoint on 18 November 2026.

The engineering foundation includes:

- Workflow orchestration and execution lifecycle controls.
- Execution authorization and trusted authorization checks.
- Adapter contracts and adapter registry.
- Controlled adapter dispatch.
- Kubernetes and Ansible adapter implementations.
- Resource Safety controls.
- Execution and verification contracts.
- Independent verification components.
- SQLite persistence and recording services.
- Execution history and audit evidence.

The B20–B23 engineering audit is maintained separately in:

`docs/B20-B23-REMEDIATION-ENGINE-AUDIT.md`

**Important validation boundary:** Implementation and automated test evidence do not, by themselves, prove successful execution against every live infrastructure target. Live Ansible and Kubernetes execution, deployment-specific configuration, and operational readiness must be validated separately and recorded accurately.

B21–B23 are not being reopened for redesign. Address only defects demonstrated by evidence or issues that block the next deployment stage.

## 3. Implementation Sequence

The agreed implementation sequence is:

1. B24 migration preparation and cloud deployment.
2. Server B stabilisation and operational validation.
3. Jenkins installation and GitHub CI/CD.
4. Complete IAM/PAM foundations.
5. AI model installation and evaluation.
6. AI agent integration.
7. Intelligent SRE and Agentic DevOps operational validation.
8. Unified TAP SRE and Agentic Remediation Dashboard.
9. End-to-end acceptance and security validation.
10. GitHub engineering portfolio publication.

Minimum security prerequisites, including secure SSH access, administrator access, service identities and credential protection, must be addressed before or during migration. The broader IAM/PAM foundation is completed after Jenkins.

---

## 4. Stage 1 — B24 Cloud Migration Preparation and Deployment

### Objectives

Prepare the existing Server B platform for migration and deploy it into the intended cloud environment.

### Work

- Review the B20–B23 engineering audit for migration-relevant dependencies and limitations.
- Inspect the source environment, installed packages, services, applications and configurations.
- Document the source infrastructure and deployment dependencies.
- Assess and prepare the Contabo VPS destination.
- Establish minimum security prerequisites:
  - Secure SSH configuration and administrator access.
  - Required service identities and permissions.
  - Secure handling of credentials, keys and secrets.
  - Network and firewall access controls.
- Prepare reusable, version-controlled migration procedures.
- Develop and validate the required Ansible playbooks, roles and supporting scripts.
- Establish backup, restore and rollback procedures.
- Prepare destination networking, firewall rules and service access.
- Migrate the required TAP applications, configuration and persistent data.
- Deploy TAP on Server B.
- Validate service startup, connectivity, configuration, data integrity and recovery procedures.

### Completion criteria

- TAP is deployed on the intended Server B environment.
- Required services start and operate correctly.
- Access and security prerequisites are in place.
- Persistent data and configuration integrity are checked.
- Backup, restoration and rollback procedures are documented and tested.
- Migration evidence and remaining limitations are recorded.

The detailed migration plan remains a separate supporting document:

`docs/migration/PRE-MIGRATION-READINESS-AND-CLOUD-MIGRATION.md`

## 5. Stage 2 — Server B Stabilisation and Operational Validation

### Objectives

Establish a stable and measurable operating baseline before introducing CI/CD and AI workloads.

### Work

- Validate Linux operating-system health and configuration.
- Validate network connectivity, DNS and required service communication.
- Inspect application and service health.
- Measure CPU, RAM, storage and available capacity.
- Validate database and persistent-data integrity.
- Test service startup, restart and recovery behaviour.
- Review firewall, SSH and administrator access controls.
- Validate backup and recovery procedures.
- Establish baseline monitoring, logs and operational checks.
- Record issues, root causes, remediation and verification evidence.

### Completion criteria

Server B has a stable, secure and documented operational baseline suitable for CI/CD integration and subsequent AI deployment.

## 6. Stage 3 — Jenkins Installation and GitHub CI/CD

### Objectives

Establish automated software validation and controlled delivery from GitHub to Server B.

### Work

- Install and secure Jenkins.
- Configure GitHub integration and appropriately scoped credentials.
- Create and maintain Jenkins pipeline definitions.
- Implement automated source validation and testing.
- Integrate the relevant Python test suites.
- Add packaging and container workflows where appropriate.
- Implement controlled deployment stages.
- Add post-deployment health checks.
- Validate pipeline failure handling and recovery or rollback procedures.
- Preserve build, test and deployment evidence.

### Completion criteria

A functioning GitHub-to-Jenkins pipeline can validate, test, build and deploy through controlled stages, with observable results and documented failure handling.

## 7. Stage 4 — Complete IAM/PAM Foundations

### Objectives

Establish auditable identity and privileged-access controls across administrators, services, applications and future AI agents.

### Work

- Define human administrator identities and roles.
- Establish service accounts and service identities.
- Implement role-based access control (RBAC).
- Apply least-privilege permissions.
- Review SSH and administrator access security.
- Establish secure secrets and credential management.
- Separate administrator, application and execution privileges.
- Define AI model and agent identity boundaries.
- Control and audit privileged operations.
- Review access permissions and validate security boundaries.

### Completion criteria

IAM/PAM controls are implemented and validated for the relevant people, services, applications and agent execution paths.

## 8. Stage 5 — AI Model Installation and Evaluation

### Objectives

Introduce local and external model capabilities only after migration and Server B stabilisation.

### Work

- Assess actual VPS CPU, RAM, storage and workload capacity.
- Benchmark candidate models against TAP's real workloads.
- Select an appropriate primary model.
- Evaluate an optional smaller model for faster, simpler tasks.
- Evaluate an external API fallback or escalation option.
- Integrate model routing through the model-independent TAP AI Gateway.
- Measure latency, reliability, resource consumption and operating cost.
- Apply access controls and secure configuration.
- Ensure models cannot bypass TAP authorization or execution governance.

Model selection must follow measured hardware capacity and workload results. Do not delay migration or stabilisation based on speculative future model releases.

### Completion criteria

A stable, tested and cost-conscious model environment is available through the TAP AI Gateway, with documented benchmarks, limitations and access boundaries.

## 9. Stage 6 — AI Agent Integration

### Objectives

Integrate selected agents as governed operational and engineering assistants.

### Candidate tools

- Goose
- Hermes Agent
- OpenCode

Final selection and deployment depend on compatibility, security, resource usage and demonstrated value.

### Work

- Install and configure selected agents.
- Establish MCP and other required tool interfaces.
- Define agent identities, permissions and access boundaries.
- Integrate model and agent routing.
- Enable controlled infrastructure and application evidence gathering.
- Integrate investigation and remediation workflows with TAP.
- Route consequential execution through TAP governance and authorization.
- Validate agent access, security, failure handling and audit records.

### Completion criteria

Selected agents can investigate, gather evidence and assist engineering or propose remediation within defined permissions and TAP governance. They cannot independently bypass authorization controls.

## 10. Stage 7 — Intelligent SRE and Agentic Operations Validation

### Objectives

Validate the complete operational lifecycle using the deployed platform.

### Work

- Validate infrastructure and application investigation.
- Correlate distributed observability evidence.
- Validate incident investigation and root-cause analysis.
- Evaluate AI-generated remediation recommendations.
- Apply policy and risk evaluation.
- Enforce Resource Safety controls.
- Require trusted authorization where the action's risk or impact demands it.
- Dispatch approved work through controlled adapters.
- Independently verify execution outcomes.
- Persist execution and verification records.
- Test failures, partial execution, blocked actions and recovery.
- Validate administrator escalation and approval workflows.

### Completion criteria

The platform demonstrates an evidence-based, governed operational lifecycle from investigation and remediation planning through authorization, controlled execution, independent verification and persistent recording.

## 11. Stage 8 — Unified TAP SRE and Agentic Remediation Dashboard

### Objectives

Build and deploy one integrated operational application combining SRE visibility, intelligent investigation, governed remediation and administrator interaction.

The dashboard is a required core TAP platform component, not two separate applications.

### A. SRE Operations Dashboard

- Distributed observability and infrastructure monitoring.
- Server, application and service health.
- CPU, RAM, storage and capacity visibility.
- Performance and reliability indicators.
- Incident detection, investigation and RCA.
- Security and infrastructure alerts.

### B. Agentic Remediation Control Panel

- AI investigation and evidence presentation.
- Remediation recommendations.
- Policy and risk evaluation visibility.
- Trusted authorization and human approval.
- Dispatcher and adapter execution status.
- Ansible and Kubernetes execution visibility.
- Independent verification results.
- Persistent execution and audit history.
- Visibility of failed, blocked, partial and unverified actions.

### C. Administrator Notification Centre and Approval Inbox

- Dedicated administrator notification area and inbox.
- Pending approval visibility.
- Approval and rejection workflows.
- Execution and verification failure notifications.
- Security and Resource Safety alerts.
- Escalation and acknowledgement workflows.
- Notification and approval history.

### D. Administrator Email and WhatsApp Integration

- Configure the administrator's email address and WhatsApp number during deployment.
- Securely configure provider credentials and API access.
- Define notification categories and severity.
- Support approval and escalation notifications.
- Record delivery status and notification history.
- Handle delivery failures and retries.

Personal contact details, provider credentials, API tokens and other secrets must be supplied and configured securely during deployment. They must never be guessed, hardcoded into source code or published in a public GitHub repository.

### E. Application Engineering

- Python backend and APIs.
- Frontend application.
- Database and persistent operational records.
- Authentication and RBAC.
- Secure application configuration.
- Integration with B21–B23 remediation services.
- SRE observability and notification services.
- Approval and administrator workflows.
- Automated and integration tests.
- Maintainable application and operational documentation.

### Completion criteria

A deployed, secured and tested dashboard demonstrates SRE visibility, incident investigation, governed remediation, administrator approvals, email and WhatsApp notifications, and persistent operational evidence.

The detailed dashboard component roadmap remains a separate supporting specification and must be preserved as such. It is not replaced by this summary.

## 12. Stage 9 — End-to-End Acceptance and Security Validation

### Objectives

Validate the integrated platform as an operational system rather than relying only on individual component tests.

### Work

- Run application and integration tests.
- Validate Jenkins pipelines and deployment workflows.
- Validate IAM permissions and privilege boundaries.
- Test model and agent access restrictions.
- Validate remediation authorization and execution paths.
- Test Resource Safety enforcement.
- Validate independent verification.
- Confirm persistent audit and execution history.
- Test administrator inbox and approval workflows.
- Validate email and WhatsApp delivery.
- Exercise failure, recovery and escalation scenarios.
- Review security, deployment and operational documentation.
- Record test evidence, limitations and outstanding defects.

### Completion criteria

Defined acceptance and security tests pass, with reproducible evidence and clearly documented limitations. Any unverified capability remains explicitly identified as unverified.

## 13. Stage 10 — GitHub Engineering Portfolio

### Objectives

Publish a professional, evidence-based engineering portfolio demonstrating the actual Server B / TAP work.

### Work

- Document project objectives and architecture.
- Maintain a clear repository and documentation structure.
- Publish relevant architecture diagrams and decisions.
- Include genuine screenshots and demonstrations where appropriate.
- Document the dashboard and its demonstrated capabilities.
- Document Jenkins pipelines and deployment architecture.
- Preserve test, verification and acceptance evidence.
- Maintain engineering audits and troubleshooting records.
- Distinguish clearly between:
  - Implemented.
  - Tested.
  - Demonstrated.
  - Planned.
  - Unverified.

Do not describe planned or unverified capabilities as completed production achievements.

### Completion criteria

The public repository presents a coherent, technically accurate and evidence-backed engineering portfolio.

---

## 14. Engineering Governance and Safety Principles

All implementation work follows these principles:

**AI proposes → TAP evaluates → Policy authorizes → Trusted authorization permits → Dispatcher executes → Independent verification proves → Recorder records.**

- Preserve working code and established architecture.
- Inspect before changing scope or implementation.
- Avoid unnecessary redesign, gold-plating and speculative features.
- Make focused, evidence-driven changes.
- Test before committing or deploying.
- Apply human approval to consequential or uncertain operations.
- Permit bounded low-risk autonomy only when policy, scope, testing and trusted authorization requirements are satisfied.
- Enforce Resource Safety limits; hard safety limits cannot be overridden by AI or ordinary authorization.
- Keep execution and verification outcomes distinct.
- Preserve execution IDs, attempt IDs, timestamps, failures and partial outcomes.
- Maintain persistent, auditable records.
- Report outcomes honestly as PASS, FAIL or UNVERIFIED.
- Never claim production readiness without corresponding validation evidence.

## 15. Supporting Documentation

Keep detailed documents separate where they serve a distinct engineering purpose. Relevant supporting records include:

- B20–B23 remediation-engine engineering audit.
- B24 migration readiness and execution plan.
- Infrastructure architecture and architecture decision records.
- Security and IAM/PAM assessments.
- Jenkins and CI/CD implementation records.
- AI model and agent integration records.
- Dashboard component roadmap and application architecture.
- Administrator notification and configuration procedures.
- Troubleshooting and root-cause analysis records.
- Test, verification and acceptance evidence.
- Operational runbooks, backup and recovery procedures.

The documentation structure is intentional:

- **Immediate roadmap:** what should be implemented next.
- **Component roadmaps:** what each individual component must deliver.
- **Engineering and troubleshooting records:** what was actually implemented, tested, observed and fixed.

Small component roadmaps remain valid supporting specifications. They are not discarded or replaced by this main roadmap.

## 16. Overall Delivery Sequence

**B21–B23 implementation checkpoint → B24 Cloud Migration → Server B Stabilisation → Jenkins CI/CD → Complete IAM/PAM → AI Models → AI Agents → Intelligent SRE and Agentic Operations Validation → Unified SRE and Agentic Remediation Dashboard → End-to-End Acceptance → GitHub Engineering Portfolio.**

Minimum IAM/PAM security prerequisites are addressed before or during migration; the broader IAM/PAM foundation is completed after Jenkins.

---

**Document control:** Version 2.0
**Last recorded update:** 19 November 2026, 15:29:55 SAST
**Repository:** `joseph-tawanitech/serverb-platform-engineering`
**Intended path:** `docs/roadmap/server-b-immediate-deployment-roadmap.md`
