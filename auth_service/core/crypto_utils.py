from core.exceptions import IDGenerationError
import secrets
import uuid


class IDGenerator:
    @staticmethod
    def random_hex(length=32):
        return secrets.token_hex(length)

    @staticmethod
    def generate():
        try:
            return str(uuid.uuid4())
        except Exception as e:
            raise IDGenerationError(f"Unexpected error occurred during ID generation:\n{str(e)}")

