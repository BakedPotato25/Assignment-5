import json
import logging
import os
from datetime import datetime, timezone

import pika

logger = logging.getLogger(__name__)


def _connection_parameters():
    return pika.ConnectionParameters(
        host=os.environ.get("RABBITMQ_HOST", "rabbitmq"),
        port=int(os.environ.get("RABBITMQ_PORT", "5672")),
        credentials=pika.PlainCredentials(
            os.environ.get("RABBITMQ_USER", "guest"),
            os.environ.get("RABBITMQ_PASSWORD", "guest"),
        ),
        heartbeat=30,
        blocked_connection_timeout=30,
    )


def publish_event(event_type, data, producer="order-service"):
    exchange = os.environ.get("BOOKSTORE_EVENT_EXCHANGE", "bookstore.events")
    payload = {
        "event_type": event_type,
        "producer": producer,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }

    try:
        connection = pika.BlockingConnection(_connection_parameters())
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
        channel.basic_publish(
            exchange=exchange,
            routing_key=event_type,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
            ),
        )
        connection.close()
        logger.warning("EVENT_PUBLISHED type=%s order_id=%s", event_type, data.get("order_id"))
    except Exception as exc:
        logger.warning("EVENT_PUBLISH_FAILED type=%s reason=%s", event_type, exc)