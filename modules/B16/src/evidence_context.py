import json

from .ntp_evidence import collect_ntp_evidence


def build_ntp_evidence_context() -> str:
    evidence = collect_ntp_evidence()

    return (
        "SERVER B SRE EVIDENCE\n"
        "Evidence type: NTP / time synchronization\n"
        "Collection mode: read-only\n"
        "No remediation has been performed.\n\n"
        + json.dumps(evidence, indent=2)
    )
