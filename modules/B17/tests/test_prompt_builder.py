from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.prompt_builder import PromptBuilder


builder = PromptBuilder(
    system_prompt=(
        "You are an AI operating within Tawanitech Automation Platform. "
        "AI intelligence does not constitute execution authority. "
        "AI proposes. TAP authorizes. TAP executes. TAP verifies. TAP records."
    ),
    role_prompt="Infrastructure SRE",
    task_prompt="Perform a read-only investigation.",
)

prompt = builder.build(
    asset="server-b-tap",
    objective="Investigate current server health",
    evidence="CPU utilization was 87%.",
    output_contract="Return exactly the required structured investigation fields.",
)

required_fragments = [
    "Tawanitech Automation Platform",
    "AI intelligence does not constitute execution authority",
    "AI proposes.",
    "TAP authorizes.",
    "TAP executes.",
    "TAP verifies.",
    "TAP records.",
    "Infrastructure SRE",
    "read-only investigation",
    "server-b-tap",
    "CPU utilization was 87%.",
    "OUTPUT CONTRACT",
    "required structured investigation fields",
]

for fragment in required_fragments:
    if fragment not in prompt:
        raise AssertionError(f"Missing required prompt content: {fragment}")

try:
    PromptBuilder(system_prompt="valid").build()
except ValueError:
    pass
else:
    raise AssertionError("Missing output contract was not rejected")

print("B17 prompt builder: PASS")
print(f"Prompt length: {len(prompt)} characters")
