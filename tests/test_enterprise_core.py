from aslab.core.bas import SafeBASRunner, ScenarioStep
from aslab.core.events import EventBus
from aslab.core.manifests import ManifestVerifier, ModuleManifest
from aslab.core.policy import Policy, PolicyEngine, PolicyViolation
from aslab.core.rbac import Principal, Role


def test_policy_blocks_public_target() -> None:
    policy = PolicyEngine(Policy())
    try:
        policy.authorize("scan", "8.8.8.8", authorized=True)
    except PolicyViolation:
        return
    raise AssertionError("public target should be blocked")


def test_rbac() -> None:
    assert Principal("viewer", Role.VIEWER).can("read")
    assert not Principal("viewer", Role.VIEWER).can("run")


def test_manifest_signature() -> None:
    verifier = ManifestVerifier(b"x" * 32)
    manifest = ModuleManifest("scanner/port_scan", "1.0.0", "abc", ("network_audit",))
    assert verifier.verify(manifest, verifier.sign(manifest))


def test_safe_bas() -> None:
    events = EventBus()
    runner = SafeBASRunner(PolicyEngine(), events)
    result = runner.run("connectivity", [ScenarioStep("loopback", "scan", "127.0.0.1", lambda: "ok")], authorized=True)
    assert result == ["ok"]
