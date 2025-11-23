import json
import logging
import os
from confluent_kafka import Producer

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # ensure logs are outputted

# ---------------------------------------------------------------------------
# Kafka Configuration
# ---------------------------------------------------------------------------
# Bootstrap server is taken from environment variable or default
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# Kafka topic for user-related events
USER_TOPIC = "user_events"

# ---------------------------------------------------------------------------
# Kafka Producer Initialization
# ---------------------------------------------------------------------------
# This creates a Kafka producer instance that can publish messages to Kafka.
producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})

# ---------------------------------------------------------------------------
# Delivery callback
# ---------------------------------------------------------------------------
# This function is called asynchronously by confluent_kafka to report
# success or failure of message delivery.
def delivery_report(err, msg):
    if err is not None:
        # Log errors if message delivery failed
        logger.error(f"Message delivery failed: {err}")
    else:
        # Log successful delivery (topic + partition)
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")

# ---------------------------------------------------------------------------
# Event Publisher Function
# ---------------------------------------------------------------------------
# publish_user_created: publish a "user_created" event to Kafka
# Arguments:
#   - user_id: integer, unique ID of the user
#   - username: string, username of the created user
#   - email: string, email of the user
# ---------------------------------------------------------------------------
def publish_user_created(user_id: int, username: str, email: str):
    """
    Publishes a 'user_created' event to the Kafka 'user_events' topic.
    This event can then be consumed by other services asynchronously.
    """
    # Construct the event payload
    event = {
        "event": "user_created",
        "data": {
            "id": user_id,
            "username": username,
            "email": email,
        },
    }

    try:
        # Publish event to Kafka
        producer.produce(
            USER_TOPIC,
            value=json.dumps(event),      # encode event as JSON string
            callback=delivery_report       # report delivery success/failure
        )

        # Flush to ensure the message is sent immediately
        producer.flush()

    except Exception as e:
        # Log any exception that occurs while producing
        logger.error(f"Failed to publish message: {e}")
