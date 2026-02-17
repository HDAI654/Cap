from core.exceptions import IDGenerationError
import logging
import secrets
import uuid

logger = logging.getLogger(__name__)

class IDGenerator:
    @staticmethod
    def random_hex(length=32):
        return secrets.token_hex(length)

    @staticmethod
    def generate():
        try:
            return str(uuid.uuid4())
        except Exception as e:
            logger.exception("Unexpected error occurred during ID generation")
            raise IDGenerationError(str(e))

