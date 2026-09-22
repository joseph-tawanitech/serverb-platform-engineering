"""B20.5 adapter for the existing B17 prompt-engineering layer."""

from __future__ import annotations

from pathlib import Path

from .operator import SecurityInvestigationRequest


B20_ROOT = Path(__file__).resolve().parents[2]
B17_PROMPTS = B20_ROOT.parent / "B17" / "prompts"


def _load(relative_path: str) -> str:
    """Load an existing B17 prompt fragment."""
    path = B17_PROMPTS / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"B17 prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def build_security_investigation_prompt(
    request: SecurityInvestigationRequest,
) -> str:
    """Build a B20 security investigation prompt using B17 components."""

    from engine.prompt_builder import PromptBuilder

    builder = PromptBuilder(
        system_prompt=_load("system/tap_core.md"),
        role_prompt=_load("roles/infrastructure_sre.md"),
        task_prompt=_load("tasks/investigation.md"),
    )

    evidence = "\n".join(
        [
            f"Security evidence IDs: {', '.join(request.evidence_ids) or 'none'}",
            f"Security evidence context: {request.context or 'none'}",
        ]
    )

    knowledge = (
        f"Relevant knowledge/history:\n{request.knowledge_context}"
        if request.knowledge_context
        else "Relevant knowledge/history: none supplied."
    )

    constraints = "\n\n".join(
        [
            _load("runtime/investigation_runtime.md"),
            knowledge,
        ]
    )

    return builder.build(
        asset=f"{request.environment} / {request.asset}",
        objective=request.question,
        evidence=evidence,
        dependencies=knowledge,
        constraints=constraints,
        output_contract=_load("contracts/investigation_output.md"),
    )
