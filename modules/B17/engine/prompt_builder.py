"""
B17 Prompt Builder

Builds governed TAP prompts from reusable prompt components.

The builder assembles:

    System/Core Prompt
    + Role
    + Task
    + Environment
    + Objective
    + Evidence
    + Dependencies
    + Constraints
    + Output Contract

The builder does NOT grant execution authority.
"""

from pathlib import Path


B17_ROOT = Path(__file__).resolve().parent.parent


class PromptBuilder:
    """Build a governed TAP AI prompt."""

    def __init__(
        self,
        system_prompt: str,
        role_prompt: str = "",
        task_prompt: str = "",
    ):
        self.system_prompt = self._require_text(
            system_prompt,
            "system_prompt",
        )
        self.role_prompt = role_prompt.strip()
        self.task_prompt = task_prompt.strip()

    @staticmethod
    def _require_text(value: str, name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string")

        value = value.strip()

        if not value:
            raise ValueError(f"{name} cannot be empty")

        return value

    @staticmethod
    def _section(title: str, content: str) -> str:
        content = content.strip()

        if not content:
            return ""

        return f"\n## {title}\n\n{content}\n"

    def build(
        self,
        *,
        asset: str = "",
        objective: str = "",
        evidence: str = "",
        dependencies: str = "",
        constraints: str = "",
        output_contract: str = "",
    ) -> str:
        """
        Build the final governed prompt.

        An explicit output contract is mandatory so that every B17
        investigation has a defined machine-readable result contract.
        """

        output_contract = self._require_text(
            output_contract,
            "output_contract",
        )

        sections = [
            self.system_prompt,
        ]

        if self.role_prompt:
            sections.append(
                self._section("ROLE", self.role_prompt)
            )

        if self.task_prompt:
            sections.append(
                self._section("TASK", self.task_prompt)
            )

        sections.append(
            self._section("ASSET / ENVIRONMENT", asset)
        )

        sections.append(
            self._section("OBJECTIVE", objective)
        )

        sections.append(
            self._section("EVIDENCE", evidence)
        )

        sections.append(
            self._section("DEPENDENCIES", dependencies)
        )

        sections.append(
            self._section("CONSTRAINTS", constraints)
        )

        sections.append(
            self._section("OUTPUT CONTRACT", output_contract)
        )

        return "\n".join(
            section for section in sections if section
        ).strip()


def load_prompt(relative_path: str) -> str:
    """
    Load a prompt file relative to the B17 module.
    """

    path = B17_ROOT / relative_path

    if not path.is_file():
        raise FileNotFoundError(
            f"Prompt file not found: {path}"
        )

    return path.read_text(encoding="utf-8").strip()
