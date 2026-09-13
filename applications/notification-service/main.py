import json
import logging
import os
import time

import pika
from prometheus_client import Counter, start_http_server

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "admin")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

NOTIFICATIONS_SENT = Counter(
    "notifications_sent_total",
    "Total simulated notifications sent",
    ["severity", "event_type"],
)


def connect():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials,
        )
    )


def main():
    start_http_server(9000)
    while True:
        try:
            connection = connect()
            channel = connection.channel()
            channel.queue_declare(queue="notification_queue", durable=True)

            def callback(ch, method, properties, body):
                event = json.loads(body)
                logger.warning(
                    "Simulated alert notification: severity=%s type=%s source=%s",
                    event.get("severity"),
                    event.get("event_type"),
                    event.get("source"),
                )
                NOTIFICATIONS_SENT.labels(
                    severity=event.get("severity", "unknown"),
                    event_type=event.get("event_type", "unknown"),
                ).inc()
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue="notification_queue",
                on_message_callback=callback,
            )
            logger.info("Notification service started")
            channel.start_consuming()
        except Exception:
            logger.exception("Notification service disconnected; retrying")
            time.sleep(5)


if __name__ == "__main__":
    main()
