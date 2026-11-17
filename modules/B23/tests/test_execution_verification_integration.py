from tap_b22.kubernetes_adapter import KubernetesDeploymentTarget

from tap_b23 import (
    SQLiteAppendOnlyRecorder,
    VerificationEngine,
    VerificationRecordingService,
    VerificationStatus,
)

from modules.B22.tests.test_execution_dispatcher import (
    FakeAdapter,
    make_prepared_plan,
    make_dispatcher,
    resource_map,
)

from modules.B23.tests.test_kubernetes_verifier import (
    FakeAppsAPI,
    make_deployment,
)

from tap_b23.kubernetes_verifier import KubernetesDeploymentVerifier


def test_dispatch_verify_and_durable_recording(tmp_path):
    # 1. B22: perform simulated, policy-guarded adapter dispatch.
    adapter = FakeAdapter()
    prepared, actions = make_prepared_plan(adapter)

    dispatch = make_dispatcher().dispatch(
        prepared,
        resource_map(actions),
    )

    assert dispatch.action_records
    assert dispatch.action_records[0].adapter_result is not None

    # 2. B23: independently verify the resulting Kubernetes state.
    record = dispatch.action_records[0]
    api = FakeAppsAPI(deployment=make_deployment(record))

    verifier = KubernetesDeploymentVerifier(
        apps_api=api,
        targets={
            "payments-api": KubernetesDeploymentTarget(
                namespace="default",
                deployment="payments-api",
            )
        },
        timeout_seconds=0.01,
        poll_interval_seconds=0.001,
        request_timeout_seconds=1.0,
    )

    engine = VerificationEngine(
        verifiers={"kubernetes": verifier}
    )

    # 3. B23: record the dispatch and verification in SQLite.
    database = tmp_path / "tap-integration-audit.db"
    recorder = SQLiteAppendOnlyRecorder(database)

    service = VerificationRecordingService(
        verification_engine=engine,
        recorder=recorder,
    )

    entry = service.verify_and_record(dispatch)

    assert entry.verification.status is VerificationStatus.VERIFIED
    assert entry.verification.results[0].status is VerificationStatus.VERIFIED
    assert entry.dispatch.dispatch_id == dispatch.dispatch_id

    # 4. Reopen the database through a new recorder and verify persistence.
    restored = SQLiteAppendOnlyRecorder(database).get(
        dispatch.dispatch_id
    )

    assert restored is not None
    assert restored.dispatch == dispatch
    assert restored.verification == entry.verification
    assert restored.verification.status is VerificationStatus.VERIFIED
