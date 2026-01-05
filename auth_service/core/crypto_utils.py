import secrets
import uuid


class IDGenerator:
    @staticmethod
    def random_hex(length=32):
        return secrets.token_hex(length)

    @staticmethod
    def generate():
        return str(uuid.uuid4())
