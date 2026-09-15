from aslab.core.loader import ModuleLoader


def test_discovers_port_scanner() -> None:
    loader = ModuleLoader()
    names = loader.discover()
    assert "aslab.modules.scanners.port_scan" in loader._loaded
    assert "scanner/port_scan" in names


def test_module_defaults() -> None:
    module = ModuleLoader().create("scanner/port_scan")
    assert module.options["PORTS"].value == "22,80,443,8080"
