import pytest
from auth_app.domain.value_objects.id import ID


class TestID:
    def test_none_id(self):
        id = ID()

        assert id.value != None and isinstance(id.value, str)

    def test_not_str_id(self):
        with pytest.raises(TypeError):
            ID(25)

    def test_empty_str_id(self):
        with pytest.raises(ValueError):
            ID("")
            ID(" ")
            ID("    ")

    def test_id_strip(self):
        str_id = "        ID  "
        id = ID(str_id)

        assert id.value == str_id.strip()

    def test_non_ASCII_id(self):
        with pytest.raises(ValueError):
            ID("این یک آیدی است")

    def test_eq_id(self):
        id = ID("MyID")
        id2 = ID("MyID")
        id3 = ID()

        assert id == id2
        assert id == "MyID" and id2 == "MyID"
        assert id != id3 and id2 != id3
