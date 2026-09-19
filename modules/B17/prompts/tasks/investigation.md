# TAP Infrastructure Investigation Task

## Task

Investigate the supplied infrastructure condition using only the
available evidence.

Determine what is known, what is likely, what remains uncertain, and
what additional evidence would improve the investigation.

## Investigation Questions

Answer the following questions:

### 1. What happened?

Describe the observed technical condition.

Do not infer causes yet.

### 2. Which asset or service is affected?

Identify:

- hostname
- asset ID
- IP address where provided
- VM/container/pod where applicable
- service/application
- environment
- relevant dependencies

Do not invent missing identifiers.

### 3. When did it happen?

Establish the timeline using available timestamps.

Identify:

- first known observation
- changes before the event
- event onset
- escalation
- recovery if known

If timestamps are missing or inconsistent, state this.

### 4. What evidence exists?

Summarize the evidence supplied to the investigation.

Identify the source of each important observation.

Examples:

- Prometheus
- OpenTelemetry
- EDA
- logs
- systemd
- Kubernetes
- network telemetry
- Git
- Terraform
- Ansible
- application monitoring
- backup systems

### 5. What dependencies are involved?

Identify upstream and downstream dependencies that could explain or
contribute to the observed condition.

Do not invent dependencies.

### 6. What changed?

Identify relevant changes before or during the incident.

Examples:

- deployment
- configuration
- package update
- infrastructure change
- network change
- DNS change
- firewall change
- certificate change
- resource allocation
- user or permission change

### 7. What are the plausible causes?

Generate technically plausible hypotheses.

For each hypothesis:

- describe the hypothesis
- identify supporting evidence
- identify contradictory evidence
- identify missing evidence
- assign a confidence level

Do not declare a root cause unless evidence supports it.

### 8. What is the impact?

Assess potential impact to:

- availability
- performance
- data
- security
- customers
- dependent services
- infrastructure

Separate observed impact from potential impact.

### 9. What is the operational risk?

Consider:

- blast radius
- reversibility
- production impact
- data-loss potential
- security implications
- dependency impact
- backup/recovery position

Classify risk as:

LOW
MEDIUM
HIGH
CRITICAL

Explain the basis.

### 10. Is protection required?

Before recommending a risky operation, determine whether:

- backup exists
- backup is recent
- backup is verified
- snapshot is available
- rollback exists
- recovery path exists

If protection status is unknown, say so.

### 11. What should happen next?

Provide the safest evidence-based next step.

Prefer additional evidence collection when the current evidence is
insufficient.

Do not recommend destructive or privileged actions without clearly
identifying the authorization requirement.

### 12. How should the result be verified?

Define measurable verification criteria.

Examples:

- service returns to healthy state
- error rate decreases
- latency returns to expected range
- pod becomes Ready
- systemd service becomes active
- disk pressure clears
- network connectivity is restored
- application health check passes

Verification must correspond to the actual incident.

## Investigation Discipline

Use this sequence:

Observed
→ Evidence
→ Timeline
→ Dependencies
→ Changes
→ Findings
→ Hypotheses
→ Confidence
→ Impact
→ Risk
→ Recommendation
→ Authorization
→ Verification

Do not skip directly from symptom to remediation.

## Evidence Sufficiency

If the evidence is insufficient to determine the cause:

1. State that the root cause is not confirmed.
2. Identify the strongest current hypotheses.
3. Identify the evidence required to distinguish them.
4. Recommend evidence collection before remediation where practical.

## Read-Only Initial Mode

The initial B17 implementation is an investigation and
decision-support mode.

Do not execute or simulate execution of operational commands.

Do not claim that remediation occurred.

Do not claim that a service was restarted, configuration changed,
backup created, snapshot created, or system recovered unless such an
event is explicitly supplied as evidence.

## Final Investigation Result

Produce a structured investigation result containing:

- incident
- asset
- observed_state
- evidence
- timeline
- dependencies
- findings
- hypotheses
- confidence
- impact
- risk
- recommendation
- backup_requirement
- authorization_requirement
- missing_evidence
- verification_plan
