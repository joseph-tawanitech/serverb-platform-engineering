# Server B B15 — AI Gateway, Model Routing & Basic Guardrails

## Status

PASS — B15 verified

## Purpose

B15 establishes the controlled AI Gateway foundation for Server B.

The module provides:

- Controlled HTTP API contract
- Local Ollama model runtime integration
- Qwen3:4b model execution
- Model routing through a provider abstraction
- Basic model authorization guardrails
- No unrestricted infrastructure execution interface

## B15 Architecture

Client
  |
  v
AI Gateway
  |
  +-- API Contract
  |
  +-- Model Authorization Guardrail
  |
  v
Model Router
  |
  v
Ollama Provider
  |
  v
Ollama Runtime
  |
  v
Qwen3:4b
  |
  v
Controlled Response

## B15.10 — API Contract

The Gateway exposes:

POST /v1/chat

The client supplies:

- model
- messages
- message role
- message content

The Gateway returns:

- provider
- model
- response
- status

The API contract separates the client from the underlying AI provider.

The client does not need to know how Ollama communicates with Qwen3:4b.

## B15.11 — Ollama

Ollama was installed and verified as the local AI runtime.

Ollama API:

127.0.0.1:11434

The runtime was successfully queried and confirmed operational.

## B15.12 — Qwen3:4b

Qwen3:4b was installed through Ollama and successfully tested.

Direct model execution was verified before Gateway integration.

## B15.13 — Gateway to Ollama Integration

The Gateway was integrated with Ollama using the Python HTTP client library httpx.

Verified execution path:

Client
  |
  v
AI Gateway
  |
  v
Ollama
  |
  v
Qwen3:4b
  |
  v
Gateway Response

The Gateway successfully returned a model response.

## B15.14 — Model Router

B15.14 introduced the Model Router between the Gateway and AI providers.

Previous architecture:

Gateway
  |
  v
Ollama

Current architecture:

Gateway
  |
  v
Model Router
  |
  v
Ollama Provider
  |
  v
Ollama

The current routing policy maps Qwen3 models to the Ollama provider.

Verified provider:

ollama

Verified model:

qwen3:4b

Verified response:

provider = ollama
model = qwen3:4b
status = ok

This establishes provider abstraction and allows additional providers to be added later without changing the client API contract.

## B15.15 — Basic AI Guardrail

An explicit model authorization policy was added to the Gateway.

Currently authorized model:

qwen3:4b

Authorized model test:

HTTP 200
provider = ollama
model = qwen3:4b
status = ok

Unauthorized model test:

HTTP 403
detail = Model not authorized: unauthorized-model

The unauthorized request was rejected by the Gateway before provider execution.

## AI Authority Boundary

B15 establishes the following TAP principle:

AI capability is not execution authority.

The Gateway provides controlled AI inference.

The Gateway does not provide unrestricted access to:

- Linux shell
- Filesystem modification
- Ansible execution
- Terraform execution
- Kubernetes modification
- Direct infrastructure changes

Future governed execution belongs to later TAP modules.

## Security Boundary

The AI Gateway was bound to:

127.0.0.1:8081

The Ollama runtime was accessed through:

127.0.0.1:11434

The current design keeps AI inference separated from infrastructure execution.

## Verification Summary

B15.10 API Contract: PASS
B15.11 Ollama Runtime: PASS
B15.12 Qwen3:4b: PASS
B15.13 Gateway to Ollama: PASS
B15.14 Model Router: PASS
B15.15 Model Authorization Guardrail: PASS
Unauthorized Model Rejection: PASS
HTTP 403 Authorization Boundary: PASS

## Known Model Behavior

During testing, Qwen3:4b sometimes returned additional reasoning-style text despite requests for concise answers.

This did not indicate a Gateway, routing, or provider failure.

The observation is recorded as a model-behavior issue for future Prompt Engineering and AI Guardrails work.

## Design Principle

The Server B AI Gateway is a controlled capability boundary.

AI may reason and provide information, but AI does not automatically receive authority to execute infrastructure changes.

This separation is fundamental to TAP governance.

## B15 Completion

B15 establishes:

Client
  |
  v
AI Gateway
  |
  v
Authorization Guardrail
  |
  v
Model Router
  |
  v
Provider
  |
  v
AI Runtime
  |
  v
Controlled Response

B15 is ready for Git version control and evidence preservation.

## Next Module

B16 — AI Operations Dashboard

Planned architecture:

Browser
  |
  v
AI Operations Dashboard
  |
  v
AI Gateway
  |
  v
Model Router
  |
  v
Ollama
  |
  v
Qwen3:4b

Browser
  |
  v
AI Operations Dashboard
  |
  v
AI Gateway
  |
  v
Model Router
  |
  v
Ollama
  |
  v
Qwen3:4b
