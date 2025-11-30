import secrets
import uuid

class IDGenerator:
    @staticmethod
    def random_hex(length=32):
        return secrets.token_hex(length)

    @staticmethod
    def uuid4():
        return uuid.uuid4().hex
