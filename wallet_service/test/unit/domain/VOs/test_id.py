import pytest
from shared.id_vo import ID
from shared.exceptions import InvalidIDError


class TestID:
    def test_not_str_user_id(self):
        with pytest.raises(InvalidIDError):
            ID(123)
            ID(None)
            ID(45.67)
            ID([])

    def test_empty_str_user_id(self):
        with pytest.raises(InvalidIDError):
            ID("")
            ID(" ")
            ID("    ")
            ID("\t")

    def test_invalid_uuid_format(self):
        invalid_uuids = [
            "not-a-uuid",  # Not UUID format
            "123e4567-e89b-12d3-a456-42661417400",  # Too short
            "123e4567-e89b-12d3-a456-4266141740000",  # Too long
            "123e4567-e89b-12d3-a456-42661417400x",  # Invalid hex
            "123e4567-e89b-12d3-a456-42661417400!",  # Special char
            "123e4567-e89b-12d3-a456-42661417400 ",  # Trailing space
            "123e4567-e89b-12d3-a456-42661417400",  # 35 chars
        ]

        for invalid in invalid_uuids:
            with pytest.raises(InvalidIDError):
                ID(invalid)

    def test_invalid_uuid_version(self):
        # UUID v1 (version 1)
        uuid_v1 = "uuid_v1 = '00000000-0000-1000-8000-000000000000'"

        with pytest.raises(InvalidIDError):
            ID(uuid_v1)

    def test_valid_uuid_v4(self):
        valid = "3bb6a3ca-66dc-440e-8d11-d8cca7ad7792"
        user_id = ID(valid)
        assert user_id.value == valid

    def test_uuid_strip(self):
        str_id = "    3bb6a3ca-66dc-440e-8d11-d8cca7ad7792    "
        user_id = ID(str_id)
        assert user_id.value == str_id.strip()

    def test_uuid_case_insensitive(self):
        upper = "123E4567-E89B-12D3-A456-426614174000"
        lower = "123e4567-e89b-12d3-a456-426614174000"

        user_id1 = ID(upper)
        user_id2 = ID(lower)

        assert user_id1.value == user_id1.value.lower()
        assert user_id1.value == user_id2.value

    def test_generate_user_id(self):
        user_id = ID.generate()

        assert isinstance(user_id, ID)
        assert len(user_id.value) == 36

    def test_generate_always_unique(self):
        ids = [ID.generate().value for _ in range(100)]
        assert len(ids) == len(set(ids))
