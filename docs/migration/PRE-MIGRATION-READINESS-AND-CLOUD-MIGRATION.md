# Server B / TAP — Pre-Migration Readiness & Reproducible Cloud Migration

**Project:** Server B / TAP — Tawanitech Automation Platform
**Repository:** `joseph-tawanitech/serverb-platform-engineering`
**Local working directory:** `~/serverb-platform-engineering`
**Document type:** Strategic plan, readiness checklist, engineering decision record, and evolving technical runbook
**Status:** Initial repository audit completed; detailed technical and operational readiness checks pending
**Cloud provisioning:** Not authorized by this document

---

## 1. Purpose

Establish an evidence-based process to rebuild Server B / TAP in an appropriately sized cloud environment.

The objective is not to blindly copy the existing virtual machine. It is to identify the infrastructure, configuration, software, data, dependencies, security controls, and operational procedures required to reproduce the platform from controlled definitions and verified evidence.

The migration must preserve the distinction between:
- Implemented and verified capabilities.
- Implemented capabilities that still require verification.
- Existing configuration that needs adaptation.
- Planned cloud engineering work.
- Deferred investigations that require the original local environment.

## 2. Engineering principles

### TAP governance

AI proposes → TAP evaluates → Policy authorizes → Automation executes → Verification proves → Recorder records.

AI reasoning and RAG provide evidence and recommendations; neither independently grants authority to execute privileged actions.

### Engineering workflow

Inspect → Test → Verify → Document → Git Commit.

### Infrastructure provisioning workflow

Initialize → Validate → Plan → Review cost and security → Approve → Apply → Verify → Record.

No billable cloud resources should be created before the provider, architecture, estimated costs, security design, and provisioning plan have been reviewed and explicitly approved.

## 3. Migration objectives

The cloud rebuild should establish:

1. Reproducible infrastructure definitions and documented provisioning.
2. Repeatable operating-system and service configuration.
3. Secure identity, access, secrets, network, and firewall controls.
4. A documented Kubernetes installation and recovery process.
5. Controlled deployment of the required B0–B20 capabilities.
6. Verified AI Gateway and model-routing configuration.
7. Observability, evidence collection, and investigation capability.
8. Documented storage, persistence, backup, and recovery requirements.
9. Basic time-synchronization configuration and verification.
10. Repeatable rebuild and operational verification procedures.
11. Evidence sufficient to distinguish a successful deployment from an unverified configuration.

## 4. Initial repository audit

Audit date: 2026-10-19.

### 4.1 Git baseline

Observed:
- Current branch: `main`.
- Local branch is one commit ahead of `origin/main`.
- Latest commit: `3398746` — `B20.8: require observed state for verification`.
- Working tree reported clean by `git status --short --branch`.
- Latest commit modifies:
  - `modules/B20/docs/B20.8-VERIFICATION-AUDIT.md`
  - `modules/B20/src/tap_b20/verification_service.py`
  - `modules/B20/tests/test_verification_service.py`

Action required:
- Preserve the existing B20.8 commit.
- Decide separately whether and when to push it.
- Keep migration documentation in a separate change.
- Do not claim the commit is present on the remote until remote status confirms it.

### 4.2 Existing infrastructure-related files

The following tracked files were found:

**Terraform**
- `terraform/b10-test/main.tf`
- `terraform/b11-integration/main.tf`

The inspected definitions are test/integration examples. The B11 example uses `terraform_data` to pass an environment value. These files do not establish that cloud resources can currently be provisioned.

**Ansible**
- `ansible/b11-integration/inventory/hosts`
- `ansible/b11-integration/site.yml`
- `ansible/runner-test/inventory/hosts`
- `ansible/runner-test/project/site.yml`

The inspected inventories and playbooks use localhost for testing and integration. A cloud configuration workflow remains to be designed and verified.

**Kubernetes monitoring**
- `kubernetes/monitoring/grafana-ingress.yaml`
- `kubernetes/monitoring/grafana/values-grafana.yaml`
- `kubernetes/monitoring/opentelemetry/servicemonitor-opentelemetry.yaml`
- `kubernetes/monitoring/opentelemetry/values-opentelemetry.yaml`
- `kubernetes/monitoring/prometheus/values-prometheus.yaml`

These are migration inputs, not proof that the entire Kubernetes platform can be recreated from Git.

**Container configuration**
- `containers/quadlet/serverb-test.container`

This file alone does not establish the complete platform startup or recovery process.

### 4.3 Documentation evidence

Existing audit documents include:
- `docs/audits/server-b-b12-kubernetes-audit.md`
- `docs/audits/b13.4-grafana-audit.md`
- `docs/audits/b13.5-opentelemetry-audit.md`
- `docs/audits/Server B B14 MCP Controlled Evidence Retrieval Audit.md`
- `docs/audits/server-b-b15-ai-gateway-model-routing.md`

These documents should be reviewed for installation steps, configuration values, dependencies, observed results, and recovery instructions before creating replacement procedures.

The initial filename searches did not find an existing migration/reproducibility runbook. This is a search finding, not proof that no relevant instructions exist anywhere in the repository or VM.

### 4.4 CI/CD and automation

The initial search found no recognized GitHub Actions workflow, GitLab CI configuration, or Jenkinsfile.

Status: CI/CD reproducibility is not yet demonstrated by the inspected repository.

### 4.5 Git ignore and secrets

The `.gitignore` excludes common secret files, private-key patterns, Terraform state, Python environments, logs, and temporary files.

This is a useful baseline but does not prove that tracked files contain no credentials or sensitive infrastructure details. Tracked inventories, Helm values, Terraform definitions, and other configuration must be reviewed before cloud use.

Never commit real secrets, private keys, access tokens, passwords, or Terraform state containing sensitive values.

## 5. Existing platform capabilities

The project history and existing audit documents describe B0–B20 engineering work, including Kubernetes, observability, controlled evidence retrieval, AI Gateway/model routing, investigation, RAG, and governed security actions.

These capabilities must be verified against source code, tests, configuration, and observed runtime state before migration claims are finalized.

Important known design constraint:
- B15 is the actual AI Gateway/model router identified in the project record.
- Do not describe multiple deployed AI Gateways unless new evidence establishes them.
- Runtime availability, model availability, and successful end-to-end operation must be checked independently.

A module's existence or a passing unit test alone does not prove successful cloud deployment.

## 6. Readiness work still required

### 6.1 Runtime and dependency inventory

- [ ] Inspect existing B12–B20 audit documents and record their deployment prerequisites.
- [ ] Identify actual startup commands, system services, containers, Helm releases, and Kubernetes resources.
- [ ] Record required language runtimes, package dependencies, and versions.
- [ ] Identify environment variables and configuration files without exposing secret values.
- [ ] Identify persistent data, databases, model files, caches, and volumes.
- [ ] Determine which components must survive reboot and which must survive full rebuild.
- [ ] Record inbound/outbound ports and service-to-service dependencies.
- [ ] Record DNS, ingress, certificates, and access requirements.

### 6.2 Infrastructure and capacity

- [ ] Measure current CPU, memory, storage use, and growth requirements.
- [ ] Estimate the resource requirements of Kubernetes, monitoring, AI workloads, and supporting applications.
- [ ] Select a cloud provider only after comparing realistic costs and capabilities.
- [ ] Define network boundaries, administrative access, firewall rules, and egress requirements.
- [ ] Define storage and backup requirements.
- [ ] Determine whether the AI workload should run on the same host or use a separate service.
- [ ] Define a shutdown and deletion procedure to prevent unintended ongoing charges.

### 6.3 Reproducibility

- [ ] Define Terraform modules and variables for the selected provider.
- [ ] Define Ansible roles/playbooks for operating-system and service configuration.
- [ ] Establish a controlled secrets-delivery method.
- [ ] Define Kubernetes installation and application deployment procedures.
- [ ] Document required external dependencies and version constraints.
- [ ] Test the rebuild procedure in a controlled environment.
- [ ] Verify that the rebuilt system matches expected state.
- [ ] Document rollback, recovery, and resource teardown.

## 7. Target migration sequence

1. Complete and preserve the pre-migration audit.
2. Review existing module audit documents and runtime evidence.
3. Finalize application, data, dependency, and resource inventories.
4. Compare cloud-provider options and estimate total costs.
5. Approve the target architecture, security controls, and spending limits.
6. Implement and validate Terraform definitions without creating resources.
7. Review the Terraform plan and configuration for security and cost.
8. Provision only after explicit approval.
9. Configure the operating system and required services.
10. Install and verify Kubernetes.
11. Deploy required monitoring and platform dependencies.
12. Deploy B0–B20 in dependency order.
13. Verify individual components and end-to-end TAP workflows.
14. Test restart, recovery, and repeatable rebuild procedures.
15. Record evidence, discrepancies, and corrective actions.
16. Begin B21–B25 development in the verified cloud environment.
17. Return to deferred local DNS and Chrony investigations using preserved evidence.

The order may be adjusted only when dependency evidence justifies the change and the decision is documented.

## 8. Deferred local DNS investigation

The local K3s DNS issue remains an unresolved investigation.

Requirements:
- Preserve the local VM and relevant logs as an evidence source.
- Do not assume a cloud rebuild will resolve the local problem.
- Verify DNS and service discovery independently in the cloud environment.
- After cloud readiness, investigate the local issue through evidence collection, hypothesis generation, controlled testing, governed remediation, verification, and recording.

## 9. Deferred Chrony/time-synchronization investigation

Time synchronization has previously shown conflicting signals between service status, clock synchronization state, Chrony tracking/source selection, and hardware-clock state.

The historical evidence suggests a significant time discrepancy, but the root cause is not established by this summary.

Requirements:
- Preserve original evidence and timestamps.
- Configure and verify basic time synchronization in the cloud.
- Avoid implementing a dedicated automatic remediation workflow before the cloud baseline is operational.
- Later investigate the recurring Server A and Server B cases through reusable detection, evidence collection, correlation, hypothesis evaluation, authorization, remediation, verification, and audit recording.
- Do not change clocks or apply corrective actions without understanding the operational impact.

## 10. Security and governance requirements

- Apply least-privilege access.
- Separate infrastructure provisioning, application deployment, and IAM administration.
- Protect secrets and prevent them from entering Git history or logs.
- Review inbound access, network exposure, and administrative pathways.
- Require explicit authorization for high-impact operations.
- Capture pre-action and post-action evidence.
- Verify observed state after changes.
- Record failures and partial execution honestly.
- Define cleanup and recovery procedures before applying infrastructure changes.

## 11. Evidence and change control

For every significant migration step, record:
- Purpose and expected outcome.
- Commands or automation executed.
- Relevant configuration and versions.
- Actual output and observed state.
- Test results and failures.
- Security and cost implications.
- Remediation performed, if any.
- Verification evidence.
- Documentation and Git commit reference.

Use PASS only when evidence supports the stated acceptance criteria. Otherwise use FAIL, BLOCKED, or NOT VERIFIED, with an explanation.

## 12. Current decision record

**Decision:** Rebuild Server B from controlled definitions rather than treating a VM copy as the primary migration method.

**Reason:** The objective is reproducibility, controlled infrastructure, documented configuration, and verifiable operational behavior.

**Constraints:** Cost-sensitive deployment; architecture and provider not yet approved; existing local environment must be preserved for deferred investigations.

**Not yet decided:** Cloud provider, instance type, final resource sizing, network topology, storage configuration, deployment automation architecture, and final budget.

**Provisioning status:** No cloud resources authorized by this plan.

## 13. Acceptance criteria

The migration is not considered complete until:
- Required infrastructure can be recreated from reviewed definitions.
- Required services and workloads are deployed from documented procedures.
- Security and network controls are verified.
- B0–B20 acceptance checks have evidence.
- AI Gateway and required model routing are verified end to end.
- Observability and evidence retrieval are functional.
- Persistent data and recovery expectations are tested.
- Time synchronization is checked.
- Rebuild and teardown procedures are documented and tested.
- Costs are reviewed and resource lifecycle controls are in place.
- The resulting evidence and decisions are recorded in Git.

---

**Next action:** Review this document against the existing audit records, identify missing runtime dependencies, and update the readiness checklist before selecting or provisioning a cloud environment.
