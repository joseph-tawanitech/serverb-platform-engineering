from __future__ import annotations

import pytest

from modules.B19.architecture.retrieval_sources import (
    RetrievalInterface,
    RetrievalSource,
    RetrievalSourceType,
)


def make_source() -> RetrievalSource:
    return RetrievalSource(
        name="prometheus",
        source_type=RetrievalSourceType.PROMETHEUS,
        interface=RetrievalInterface.API,
        description="Infrastructure metrics retrieval source",
    )


def test_valid_retrieval_source() -> None:
    source = make_source()

    source.validate()

    assert source.name == "prometheus"
    assert source.source_type == RetrievalSourceType.PROMETHEUS
    assert source.interface == RetrievalInterface.API
    assert source.enabled is True


def test_empty_name_rejected() -> None:
    source = make_source()
    source = RetrievalSource(
        name="",
        source_type=source.source_type,
        interface=source.interface,
        description=source.description,
    )

    with pytest.raises(ValueError, match="name must not be empty"):
        source.validate()


def test_empty_description_rejected() -> None:
    source = make_source()
    source = RetrievalSource(
        name=source.name,
        source_type=source.source_type,
        interface=source.interface,
        description="",
    )

    with pytest.raises(
        ValueError,
        match="description must not be empty",
    ):
        source.validate()


def test_all_major_source_types_are_defined() -> None:
    expected = {
        "kubernetes",
        "prometheus",
        "logs",
        "otel",
        "network",
        "security",
        "terraform",
        "ansible",
        "incident",
        "rca",
        "database",
        "itsm",
        "cmdb",
        "git",
        "cloud",
        "storage",
        "website",
        "business_system",
        "cctv",
    }

    actual = {source.value for source in RetrievalSourceType}

    assert expected.issubset(actual)


def test_all_controlled_interfaces_are_defined() -> None:
    expected = {
        "mcp",
        "api",
        "connector",
        "file",
        "database",
    }

    actual = {interface.value for interface in RetrievalInterface}

    assert expected.issubset(actual)
