import pytest
from auth_app.domain.value_objects.device import Device


class TestDevice:
    def test_not_str_device(self):
        with pytest.raises(TypeError):
            Device(25)
            Device(None)

    def test_empty_str_device(self):
        with pytest.raises(ValueError):
            Device("")
            Device(" ")
            Device("    ")

    def test_device_strip(self):
        str_device = "        device  "
        device = Device(str_device)

        assert device.value == str_device.strip()

    def test_eq_device(self):
        device = Device("MyDevice")
        device2 = Device("MyDevice")

        assert device == device2
        assert device == "MyDevice" and device2 == "MyDevice"
