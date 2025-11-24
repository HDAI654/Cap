import os
import django
import json
import asyncio
from aiokafka import AIOKafkaConsumer
import logging

# ---------------------------------------------------------------------------
# Django Setup
# ---------------------------------------------------------------------------
# We must load Django settings and initialize the ORM because this consumer
# runs OUTSIDE the Django web server. Without this, importing models or
# calling service-layer logic would fail.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auth_service.settings.prod")
django.setup()

# ---------------------------------------------------------------------------
# Import service-layer functions
# (Handlers that apply business logic when events arrive)
# ---------------------------------------------------------------------------
# from apps.accounts.services.user_service import mark_user_as_active
# from apps.auth.services.auth_service import handle_auth_event

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Event Routing Table
# Maps event names from Kafka to Python functions in the service layer.
# This keeps event dispatching clean, extendable, and decoupled.
# ---------------------------------------------------------------------------
EVENT_HANDLERS = {
    # "user_created": mark_user_as_active,
    # "auth_event": handle_auth_event,
}


# ---------------------------------------------------------------------------
# Kafka Consumer Coroutine
# Listens for messages on the "user_events" topic, decodes them, and dispatches
# to the correct handler function based on event type.
# ---------------------------------------------------------------------------
async def consume():
    consumer = AIOKafkaConsumer(
        "user_events",
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        group_id="auth-service",  # Ensures only one consumer in the group processes each message
        auto_offset_reset="earliest",  # Start from earliest if no committed offset exists
    )

    logger.info("Starting Kafka consumer for topic 'user_events'...")

    await consumer.start()
    try:
        async for msg in consumer:
            logger.info(
                f"Received message from Kafka. Offset={msg.offset}, Partition={msg.partition}"
            )

            try:
                # Decode JSON event
                event = json.loads(msg.value.decode("utf-8"))
                event_type = event.get("event")

                logger.info(f"Decoded event: {event_type}")

                # Find handler based on event type
                handler = EVENT_HANDLERS.get(event_type)

                if handler:
                    logger.info(f"Dispatching event '{event_type}' to handler")
                    handler(event["data"])  # Pass event payload to handler
                else:
                    logger.warning(f"Unhandled event type: {event_type}")

            except Exception as e:
                # Log per-message errors but keep consumer running
                logger.error(f"Error processing message at offset {msg.offset}: {e}")

    finally:
        logger.info("Stopping Kafka consumer...")
        await consumer.stop()


# ---------------------------------------------------------------------------
# Entry Point
# asyncio.run() is required because aiokafka is async.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Auth service Kafka consumer booting up...")
    asyncio.run(consume())
