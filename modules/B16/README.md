# Server B B16 — AI Operations Dashboard

## Purpose

B16 provides a human-facing web interface for controlled interaction with the Server B B15 AI Gateway.

## Architecture

Browser
  |
  v
B16 AI Operations Dashboard
  |
  v
B15 AI Gateway :8081
  |
  v
Model Router
  |
  v
Ollama :11434
  |
  v
Qwen3:4b

## Boundary

The dashboard communicates with the B15 Gateway only.

The dashboard does not communicate directly with:
- Ollama
- Shell
- Ansible
- Terraform
- Kubernetes
- MCP tools
- Infrastructure control interfaces

## Initial Scope

- Gateway health
- Controlled model request
- AI response display
- Request status
- Basic operational information
- Clear error handling

## Out of Scope

- Autonomous agents
- MCP tool execution
- Infrastructure modification
- Ansible execution
- Terraform execution
- Kubernetes administration
- RCA automation
- RAG
- Persistent conversation history
- Business automation
- Payment workflows
- WhatsApp/email automation
- Cloud provisioning

## Design Principle

B16 is an interface layer, not an execution authority.

AI requests pass through the governed B15 Gateway.

B16 does not bypass the TAP control boundary.
