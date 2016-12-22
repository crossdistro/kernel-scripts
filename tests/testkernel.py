from kernel.config import KernelConfig

def test_from_file():
    config = KernelConfig.from_file("examples/user.config")
    assert "CONFIG_USB_STORAGE" in config.options
    assert "CONFIG_USB_STORAGE_DEBUG" in config.options
    assert "CONFIG_USB_STORAGE_REALTEK" not in config.options
