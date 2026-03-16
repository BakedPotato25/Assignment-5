import json
import logging
import os
import time

import pika
from django.db import close_old_connections

from .models import Shipment

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


def _upsert_shipment(order_id, address, method):
    shipment = Shipment.objects.filter(order_id=order_id).order_by("-created_at").first()
    next_status = "Processing" if address else "Failed"

    if shipment:
        shipment.address = address or shipment.address
        shipment.method = method or shipment.method
        shipment.status = next_status
        shipment.save(update_fields=["address", "method", "status"])
        return

    Shipment.objects.create(
        order_id=order_id,
        address=address or "",
        method=method or "Standard",
        status=next_status,
    )


def _handle_event(event_type, data):
    if event_type != "shipping.reserve.requested":
        return

    order_id = data.get("order_id")
    if not order_id:
        return

    _upsert_shipment(
        order_id=order_id,
        address=data.get("address", ""),
        method=data.get("method", "Standard"),
    )


def start_consumer():
    queue_name = os.environ.get("BOOKSTORE_SHIP_QUEUE", "ship-service.events")
    exchange = os.environ.get("BOOKSTORE_EVENT_EXCHANGE", "bookstore.events")
    binding_keys = ["shipping.reserve.requested"]

    while True:
        connection = None
        try:
            connection = pika.BlockingConnection(_connection_parameters())
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
            channel.queue_declare(queue=queue_name, durable=True)
            for key in binding_keys:
                channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=key)

            def _callback(ch, method, properties, body):
                del properties
                try:
                    payload = json.loads(body.decode("utf-8"))
                    event_type = payload.get("event_type", method.routing_key)
                    data = payload.get("data", {})
                    close_old_connections()
                    _handle_event(event_type, data)
                    logger.warning("EVENT_CONSUMED service=ship type=%s order_id=%s", event_type, data.get("order_id"))
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as exc:
                    logger.warning("EVENT_CONSUME_FAILED service=ship reason=%s", exc)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_qos(prefetch_count=10)
            channel.basic_consume(queue=queue_name, on_message_callback=_callback)
            logger.warning("EVENT_CONSUMER_READY service=ship queue=%s", queue_name)
            channel.start_consuming()
        except Exception as exc:
            logger.warning("EVENT_CONSUMER_RETRY service=ship reason=%s", exc)
            time.sleep(5)
        finally:
            close_old_connections()
            if connection and connection.is_open:
                connection.close()