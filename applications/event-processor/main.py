import json
import logging
import os
import threading
from datetime import datetime
from typing import Any, Dict

import pika
import psycopg2
import redis
from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from starlette.responses import Response

app = FastAPI(title="Event Processor")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "eventdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "admin")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

EVENTS_PROCESSED = Counter(
    "events_processed_total",
    "Total events processed by the processor",
    ["severity", "event_type", "status"],
)


class EventProcessor:
    def __init__(self) -> None:
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
        )

    def get_db_connection(self):
        return psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )

    def process_event(self, event_data: Dict[str, Any]) -> bool:
        status = "processed"
        try:
            event_data["processed_at"] = datetime.utcnow().isoformat()
            event_data["status"] = status

            if event_data.get("event_type") == "security_alert":
                self.handle_security_alert(event_data)
            elif event_data.get("event_type") == "performance_metric":
                self.handle_performance_metric(event_data)
            elif event_data.get("event_type") == "application_log":
                self.handle_application_log(event_data)

            self.store_event(event_data)
            event_id = f"processed:{event_data.get('timestamp', event_data['processed_at'])}"
            self.redis_client.hset(event_id, mapping=self._string_mapping(event_data))
            self.redis_client.expire(event_id, 3600)
            logger.info("Processed event: %s", event_data.get("event_type"))
            return True
        except Exception as exc:
            status = "failed"
            event_data["status"] = status
            event_data["error"] = str(exc)
            logger.exception("Error processing event")
            return False
        finally:
            EVENTS_PROCESSED.labels(
                severity=event_data.get("severity", "unknown"),
                event_type=event_data.get("event_type", "unknown"),
                status=status,
            ).inc()

    def handle_security_alert(self, event_data: Dict[str, Any]) -> None:
        if event_data.get("severity") in ["critical", "high"]:
            logger.warning("Security alert needs notification: %s", event_data)

    def handle_performance_metric(self, event_data: Dict[str, Any]) -> None:
        metrics = event_data.get("metrics", {})
        if metrics.get("cpu_percent", 0) > 90:
            event_data["alert"] = "High CPU Usage"

    def handle_application_log(self, event_data: Dict[str, Any]) -> None:
        log_message = event_data.get("message", "")
        if "ERROR" in log_message or "Exception" in log_message:
            event_data["needs_attention"] = True

    def store_event(self, event_data: Dict[str, Any]) -> None:
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO processed_events
                    (event_type, source, severity, message, metadata,
                     original_timestamp, processed_timestamp, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        event_data.get("event_type"),
                        event_data.get("source"),
                        event_data.get("severity"),
                        event_data.get("message", ""),
                        json.dumps(event_data),
                        event_data.get("timestamp"),
                        event_data.get("processed_at"),
                        event_data.get("status", "processed"),
                    ),
                )

    def publish_notification(self, event_data: Dict[str, Any]) -> None:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue="notification_queue", durable=True)
        channel.basic_publish(
            exchange="",
            routing_key="notification_queue",
            body=json.dumps(event_data),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()

    @staticmethod
    def _string_mapping(event_data: Dict[str, Any]) -> Dict[str, str]:
        return {
            key: value if isinstance(value, str) else json.dumps(value)
            for key, value in event_data.items()
        }


processor = EventProcessor()


def consume_events() -> None:
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    credentials=credentials,
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue="event_queue", durable=True)
            channel.basic_qos(prefetch_count=1)

            def callback(ch, method, properties, body):
                try:
                    event_data = json.loads(body)
                    processed = processor.process_event(event_data)
                    if processed and event_data.get("severity") in ["critical", "high"]:
                        processor.publish_notification(event_data)
                    if processed:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                except Exception:
                    logger.exception("Could not process queue message")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            channel.basic_consume(queue="event_queue", on_message_callback=callback)
            logger.info("Event processor consumer started")
            channel.start_consuming()
        except Exception:
            logger.exception("Event processor consumer disconnected; retrying")
            threading.Event().wait(5)


@app.on_event("startup")
async def startup_event() -> None:
    thread = threading.Thread(target=consume_events, daemon=True)
    thread.start()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "event-processor"}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
