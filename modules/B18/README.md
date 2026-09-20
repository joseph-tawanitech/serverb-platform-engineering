# B18 Incident Investigation & Root Cause Analysis

B18 provides a reusable, deterministic, and reproducible incident investigation framework for the Tawanitech Automation Platform (TAP).

B18 transforms structured incident and evidence data into investigation artifacts covering:

* evidence normalization
* incident timelines
* evidence correlation
* hypothesis generation
* evidence sufficiency
* root cause analysis
* investigation orchestration
* investigation results

B18 is designed as the investigation foundation for the TAP AI-SRE architecture.

---

# 1. Purpose

The purpose of B18 is to provide a structured investigation pipeline that can answer:

1. What happened?
2. What evidence is available?
3. When did the observed events occur?
4. Which evidence items are related?
5. What hypotheses can explain the observations?
6. Is the available evidence sufficient?
7. Can a root cause be established?
8. What limitations remain?
9. What investigation artifacts should be passed to later TAP components?

B18 separates observed evidence from interpretation.

A symptom is not automatically a root cause.

A correlation is not automatically causation.

A hypothesis is not automatically a confirmed root cause.

---

# 2. B18 Investigation Pipeline

The complete implemented B18 pipeline is:

```text
Incident
   |
   v
Evidence
   |
   v
Evidence Normalization
   |
   +------------------------+
   |                        |
   v                        v
Timeline Builder       Correlation Engine
                            |
                            v
                    Hypothesis Generator
                            |
                            v
                 Evidence Sufficiency
                            |
                            v
                       RCA Engine
                            |
                            v
                 InvestigationResult
```

The orchestration layer provides the integrated workflow:

```text
Incident + Evidence
        |
        v
  InvestigationEngine
        |
        +--> Normalize Evidence
        |
        +--> Build Timeline
        |
        +--> Correlate Evidence
        |
        +--> Generate Hypotheses
        |
        +--> Evaluate Evidence Sufficiency
        |
        +--> Perform RCA
        |
        v
 InvestigationResult
```

---

# 3. B18 Modules

## B18.1 — Incident Data Model

Defines the core incident representation.

An incident contains information such as:

* incident ID
* title
* severity
* status
* detection time
* source
* affected resources
* symptoms
* evidence references
* timeline
* impact
* hypotheses
* root cause
* recommendations
* confidence
* metadata

The incident model provides the top-level investigation context.

---

## B18.2 — Evidence Layer

Defines the structured evidence representation.

Supported evidence categories include:

* metrics
* logs
* traces
* events
* Kubernetes state
* command output
* configuration
* alerts
* other evidence

Evidence also records characteristics such as:

* source
* collection time
* observation time
* resource
* location
* reliability
* collection status
* metadata

The evidence layer establishes the factual input to investigation.

---

## B18.3 — Evidence Normalization

Normalizes evidence into a consistent representation before downstream
investigation processing.

Normalization allows different evidence sources to participate in the
same investigation pipeline.

The orchestrator uses the existing normalization component rather than
implementing normalization rules itself.

---

## B18.4 — Incident Timeline

Builds chronological timeline events from evidence.

A timeline event contains:

* event ID
* timestamp
* evidence ID
* source
* event type
* description
* resource
* metadata

The timeline answers the temporal question:

> What happened, and when?

Timeline construction does not determine causation.

---

## B18.5 — Evidence Correlation

Identifies relationships between evidence items.

Correlation can use factors such as:

* common resource
* temporal proximity
* configured correlation windows
* evidence relationships

Correlation produces `CorrelationGroup` and `CorrelationLink` objects.

Correlation represents a possible relationship between observations.

It does not prove causation.

---

## B18.6 — Hypothesis Generation

Produces structured hypotheses from correlated evidence.

A hypothesis contains information such as:

* hypothesis ID
* statement
* supporting evidence
* contradicting evidence
* affected resources
* reasoning
* metadata

The hypothesis layer converts evidence relationships into candidate
explanations.

The generated hypothesis remains an investigation hypothesis until
supported by sufficient evidence.

---

## B18.7 — Evidence Sufficiency

Evaluates whether the evidence supporting a hypothesis is sufficient for
the configured investigation criteria.

The current model supports:

```text
INSUFFICIENT
PARTIAL
SUFFICIENT
```

The evaluator considers factors such as:

* supporting evidence
* reliable evidence
* contradicting evidence
* missing evidence
* required evidence sources

The resulting assessment includes a confidence value and reasoning.

Evidence sufficiency is intentionally separate from RCA.

---

## B18.8 — Root Cause Analysis

Evaluates a hypothesis using its evidence sufficiency assessment.

RCA can produce:

```text
NOT_ESTABLISHED
PROVISIONAL
CONFIRMED
REJECTED
```

The RCA result can contain:

* root cause
* hypothesis ID
* supporting evidence IDs
* contradicting evidence IDs
* affected resources
* root cause location
* contributing factors
* confidence
* reasoning
* limitations
* metadata

Important distinction:

```text
Evidence
   ↓
Hypothesis
   ↓
Evidence Sufficiency
   ↓
RCA
```

RCA therefore does not bypass the evidence layer.

---

## B18.9 — Investigation Orchestration

B18.9 connects the existing B18 components into one investigation
workflow.

The primary class is:

```python
InvestigationEngine
```

The primary operation is:

```python
investigate(
    incident,
    evidence_items,
)
```

The result is:

```python
InvestigationResult
```

The orchestrator performs:

```text
Validate Incident
        ↓
Validate Evidence
        ↓
Normalize Evidence
        ↓
Build Timeline
        ↓
Correlate Evidence
        ↓
Generate Hypotheses
        ↓
Evaluate Evidence Sufficiency
        ↓
Perform RCA
        ↓
Validate Investigation Result
```

B18.9 coordinates existing engines rather than duplicating their logic.

---

# 4. Investigation Result

The integrated investigation result contains:

```text
InvestigationResult
├── incident
├── evidence[]
├── timeline[]
├── correlations[]
├── hypotheses[]
├── sufficiency[]
├── rca[]
└── metadata
```

This provides a reusable investigation artifact for higher-level TAP
components.

The result can subsequently become input to:

* incident reporting
* recommendation generation
* AI investigation
* RAG retrieval
* human review
* authorization workflows
* governed remediation
* Recorder/audit workflows

Those capabilities are outside the responsibility of the B18 deterministic
investigation engine itself.

---

# 5. Investigation Principles

## Evidence Before Conclusion

B18 begins with evidence rather than immediately assigning a root cause.

```text
Observation
    ↓
Evidence
    ↓
Correlation
    ↓
Hypothesis
    ↓
Evidence Sufficiency
    ↓
RCA
```

---

## Symptoms Are Not Root Cause

A symptom describes an observed condition.

Example:

```text
CPU usage reached 95%.
```

That is an observation or symptom.

It does not by itself establish why CPU usage increased.

---

## Correlation Is Not Causation

Two evidence items occurring close together or involving the same resource
may be related.

That relationship does not automatically establish that one caused the
other.

---

## Hypotheses Are Testable Explanations

A hypothesis represents a possible explanation of the available evidence.

Additional evidence can:

* support it
* contradict it
* leave it unresolved

---

## Evidence Sufficiency Controls Confidence

B18 does not treat every hypothesis as equally established.

The evidence sufficiency layer determines whether the available evidence
is sufficient for the configured investigation criteria.

---

## RCA Must Preserve Limitations

An investigation may produce a useful conclusion while still having
evidence gaps.

B18 therefore records limitations rather than hiding them.

---

# 6. Deterministic Investigation

The B18 core is deterministic.

Given equivalent:

* incident data
* evidence
* configuration
* correlation rules
* sufficiency rules

the investigation pipeline should produce equivalent investigation
artifacts.

This makes B18 suitable for:

* testing
* reproducibility
* auditing
* debugging
* incident review
* controlled AI integration

---

# 7. AI-SRE Boundary

B18 is an investigation foundation.

It does not attempt to make the investigation engine itself an autonomous
AI agent.

The intended TAP architecture is:

```text
Evidence Systems
      |
      v
     B18
      |
      v
Investigation Artifacts
      |
      v
AI Investigation / RAG
      |
      v
Recommendation
      |
      v
Policy / Risk
      |
      v
Authorization
      |
      v
Governed Execution
```

AI can later consume B18 investigation artifacts to assist with:

* deeper reasoning
* alternative hypotheses
* evidence interpretation
* incident summarization
* recommendation generation
* natural-language explanation
* investigation assistance

However, AI does not bypass the TAP authority boundary.

---

# 8. Relationship to TAP Governance

B18 investigates.

B18 does not authorize infrastructure changes.

The broader TAP architecture remains:

```text
MONITOR
   ↓
DETECT
   ↓
REASON
   ↓
DECIDE
   ↓
AUTHORIZE
   ↓
EXECUTE
   ↓
VERIFY
   ↓
REPORT
```

B18 primarily contributes to the:

```text
REASON
DECIDE
```

portion of this architecture.

Authorization and execution remain outside B18.

---

# 9. Future Integration

B18 is designed to support future integration with:

* Prometheus
* OpenTelemetry
* Kubernetes
* logs
* EDA
* configuration evidence
* MCP
* RAG
* AI Gateway
* AI investigation
* Recommendation Reviewer
* TAP Job Broker
* Ansible
* Kubernetes remediation
* Recorder
* dashboards
* incident reporting

These integrations should consume B18 artifacts through defined interfaces
rather than embedding infrastructure-specific execution logic into the
B18 investigation engines.

---

# 10. Glossary

## Incident

A recorded operational event requiring investigation.

An incident provides the context in which evidence is analyzed.

---

## Evidence

A recorded observation or data artifact relevant to an incident.

Examples include:

* metric
* log
* trace
* event
* Kubernetes state
* command output
* configuration
* alert

---

## Evidence Source

The system or mechanism from which evidence originated.

Examples:

```text
Prometheus
Kubernetes
OpenTelemetry
EDA
system logs
configuration
```

---

## Observation

A recorded fact about the environment at a particular point in time.

An observation may become evidence when it is captured and associated with
an investigation.

---

## Symptom

An observed condition indicating that something may be wrong.

Example:

```text
HTTP requests are returning errors.
```

A symptom does not necessarily identify the underlying cause.

---

## Timeline

A chronological representation of investigation events.

A timeline helps establish the order in which observations occurred.

---

## Timeline Event

A structured event within an investigation timeline.

It references the evidence from which the event was derived.

---

## Correlation

A detected relationship between evidence items.

Correlation can be based on factors such as:

* resource
* time
* source
* configured relationships

Correlation does not by itself establish causation.

---

## Correlation Group

A collection of related evidence items.

A correlation group provides input to hypothesis generation.

---

## Hypothesis

A proposed explanation for observed evidence.

A hypothesis can be supported, contradicted, or remain unresolved.

---

## Supporting Evidence

Evidence that is consistent with a hypothesis.

Supporting evidence does not automatically prove the hypothesis.

---

## Contradicting Evidence

Evidence that conflicts with a hypothesis.

Contradicting evidence can prevent a hypothesis from being accepted as
the established root cause.

---

## Evidence Sufficiency

An assessment of whether the available evidence is sufficient to support
an investigation conclusion under configured criteria.

B18 currently supports:

```text
INSUFFICIENT
PARTIAL
SUFFICIENT
```

---

## Root Cause

The underlying condition identified as responsible for an incident or
observed failure.

A root cause should be supported by appropriate evidence.

---

## Root Cause Analysis (RCA)

The structured process of evaluating a hypothesis and its evidence to
determine whether a root cause can be established.

B18 supports:

```text
NOT_ESTABLISHED
PROVISIONAL
CONFIRMED
REJECTED
```

---

## Provisional RCA

A root cause assessment supported by evidence but still subject to
remaining evidence gaps or limitations.

---

## Confirmed RCA

A root cause assessment that satisfies the configured evidence sufficiency
criteria and has no recorded contradicting evidence.

---

## Rejected RCA

An RCA assessment in which the associated hypothesis has contradicting
evidence and therefore cannot be accepted as the root cause.

---

## Impact

The effect of an incident on systems, services, users, workloads, or
business operations.

Impact is part of the incident model but is not automatically calculated
by the B18.9 orchestrator.

---

## Affected Resource

A server, workload, application, Kubernetes object, network component, or
other infrastructure resource associated with an incident or hypothesis.

---

## Root Cause Location

The resource or location associated with the identified root cause.

B18 can derive a location when the supporting evidence consistently
identifies a single resource.

---

## Contributing Factor

A condition that contributed to the incident without necessarily being the
primary root cause.

---

## Confidence

A numeric representation of the strength of an investigation assessment.

B18 represents confidence between:

```text
0.0
```

and:

```text
1.0
```

Confidence is associated with the investigation model and its evidence
assessment rules.

---

## Limitation

A known constraint, missing evidence source, evidence gap, or other factor
that limits the certainty of an investigation conclusion.

---

## Recommendation

A proposed action resulting from an investigation.

Recommendations are part of the broader incident model, but B18 does not
authorize or execute remediation actions.

---

## Investigation

The structured process of collecting, normalizing, correlating, evaluating,
and interpreting evidence to understand an incident.

---

## Investigation Result

The complete structured output of a B18 investigation.

It contains the incident context and generated investigation artifacts.

---

## Orchestration

The coordination of independent investigation components into a defined
workflow.

B18.9 provides this orchestration layer.

---

# 11. Testing

B18 includes unit tests covering the individual models and engines as well
as the integrated investigation workflow.

The B18.9 investigation model has dedicated validation tests.

The B18.9 investigation engine has dedicated orchestration tests.

The complete B18 test suite currently verifies:

```text
121 passed
```

The test suite covers:

* incident validation
* evidence validation
* evidence normalization
* timeline construction
* correlation
* hypothesis generation
* evidence sufficiency
* RCA
* investigation result validation
* investigation orchestration

---

# 12. Directory Structure

The B18 module is organized approximately as:

```text
modules/B18/
├── README.md
├── docs/
│   ├── B18.1-INCIDENT-DATA-MODEL.md
│   ├── B18.2-EVIDENCE-LAYER.md
│   ├── B18.3-EVIDENCE-NORMALIZATION.md
│   ├── B18.4-INCIDENT-TIMELINE.md
│   ├── B18.5-EVIDENCE-CORRELATION.md
│   ├── B18.6-HYPOTHESIS-GENERATION.md
│   ├── B18.7-EVIDENCE-SUFFICIENCY.md
│   ├── B18.8-ROOT-CAUSE-ANALYSIS.md
│   └── B18.9-INVESTIGATION-ORCHESTRATION.md
│
├── engine/
│   ├── incident_model.py
│   ├── evidence_model.py
│   ├── evidence_collector.py
│   ├── evidence_normalizer.py
│   ├── timeline_model.py
│   ├── timeline_builder.py
│   ├── correlation_model.py
│   ├── correlation_engine.py
│   ├── hypothesis_model.py
│   ├── hypothesis_generator.py
│   ├── evidence_sufficiency_model.py
│   ├── evidence_sufficiency_evaluator.py
│   ├── rca_model.py
│   ├── rca_engine.py
│   ├── investigation_model.py
│   └── investigation_engine.py
│
└── tests/
    └── ...
```

---

# 13. Current Implementation Status

```text
B18.1  Incident Data Model          IMPLEMENTED
B18.2  Evidence Layer               IMPLEMENTED
B18.3  Evidence Normalization       IMPLEMENTED
B18.4  Incident Timeline            IMPLEMENTED
B18.5  Evidence Correlation         IMPLEMENTED
B18.6  Hypothesis Generation        IMPLEMENTED
B18.7  Evidence Sufficiency         IMPLEMENTED
B18.8  Root Cause Analysis           IMPLEMENTED
B18.9  Investigation Orchestration  IMPLEMENTED
```

B18 therefore provides a complete deterministic investigation foundation.

---

# 14. Scope Boundary

B18 is responsible for structured investigation.

B18 is not responsible for:

* autonomous infrastructure changes
* authorization
* remediation execution
* Ansible execution
* Kubernetes mutation
* Terraform execution
* credential management
* policy enforcement
* production change approval

Those capabilities belong to other TAP layers.

The architectural principle is:

```text
B18 investigates.
TAP governs.
Authorized execution systems execute.
Verification confirms the result.
Recorder preserves the history.
```

---

# 15. Architectural Principle

B18 is designed around the principle:

> Evidence first. Reason explicitly. Preserve uncertainty. Do not confuse correlation with causation.

The framework provides the structured investigation foundation required for
the broader TAP AI-SRE system.

AI may enhance investigation, but the investigation artifacts remain
structured, traceable, testable, and auditable.
