import asyncio
import json
import os
from typing import Dict, Any
import pika
import redis
from fastapi import FastAPI, BackgroundTasks
import psycopg2
from datetime import datetime
import logging

app = FastAPI(title="Event Processor")

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
DB_HOST = os.getenv('DB_HOST', 'localhost')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventProcessor:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_HOST, 
            port=6379, 
            decode_responses=True
        )
        
    def get_db_connection(self):
        return psycopg2.connect(
            host=DB_HOST,
            database=os.getenv('DB_NAME', 'eventdb'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password')
        )
    
    def process_event(self, event_data: Dict[str, Any]):
        """Process incoming event"""
        try:
            # Add processing metadata
            event_data['processed_at'] = datetime.utcnow().isoformat()
            event_data['status'] = 'processed'
            
            # Apply business logic based on event type
            if event_data['event_type'] == 'security_alert':
                self.handle_security_alert(event_data)
            elif event_data['event_type'] == 'performance_metric':
                self.handle_performance_metric(event_data)
            elif event_data['event_type'] == 'application_log':
                self.handle_application_log(event_data)
            
            # Store in database
            self.store_event(event_data)
            
            # Update Redis cache
            event_id = f"processed:{event_data.get('timestamp', '')}"
            self.redis_client.hset(event_id, mapping=event_data)
            
            logger.info(f"Processed event: {event_data['event_type']}")
            
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")
            event_data['status'] = 'failed'
            event_data['error'] = str(e)
    
    def handle_security_alert(self, event_data: Dict[str, Any]):
        """Process security alerts"""
        if event_data['severity'] in ['critical', 'high']:
            # Send to security team notification
            self.send_notification(event_data, "security_team")
    
    def handle_performance_metric(self, event_data: Dict[str, Any]):
        """Process performance metrics"""
        # Check thresholds and trigger alerts
        metrics = event_data.get('metrics', {})
        if metrics.get('cpu_usage', 0) > 90:
            event_data['alert'] = 'High CPU Usage'
    
    def handle_application_log(self, event_data: Dict[str, Any]):
        """Process application logs"""
        # Parse and structure log data
        log_message = event_data.get('message', '')
        if 'ERROR' in log_message or 'Exception' in log_message:
            event_data['needs_attention'] = True
    
    def store_event(self, event_data: Dict[str, Any]):
        """Store processed event in database"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO processed_events 
                (event_type, source, severity, message, metadata, 
                 original_timestamp, processed_timestamp, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                event_data.get('event_type'),
                event_data.get('source'),
                event_data.get('severity'),
                event_data.get('message', ''),
                json.dumps(event_data),
                event_data.get('timestamp'),
                event_data.get('processed_at'),
                event_data.get('status', 'processed')
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
    
    def send_notification(self, event_data: Dict[str, Any], channel: str):
        """Send notification (placeholder implementation)"""
        logger.info(f"Notification sent via {channel}: {event_data.get('event_type')}")

@app.on_event("startup")
async def startup_event():
    """Start RabbitMQ consumer on startup"""
    background_tasks = BackgroundTasks()
    background_tasks.add_task(start_consumer)
    await background_tasks()

async def start_consumer():
    """Start consuming messages from RabbitMQ"""
    processor = EventProcessor()
    
    def callback(ch, method, properties, body):
        try:
            event_data = json.loads(body)
            processor.process_event(event_data)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error in consumer callback: {str(e)}")
    
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()
    channel.queue_declare(queue='event_queue', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='event_queue', on_message_callback=callback)
    
    logger.info("Event Processor started. Waiting for messages...")
    channel.start_consuming()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "event-processor"}

@app.get("/metrics")
async def get_metrics():
    """Get processing metrics"""
    try:
        conn = processor.get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                COUNT(*) as total_events,
                COUNT(CASE WHEN status = 'processed' THEN 1 END) as processed,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                event_type,
                severity
            FROM processed_events
            WHERE processed_timestamp > NOW() - INTERVAL '1 hour'
            GROUP BY event_type, severity
        """)
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return {"metrics": results}
        
    except Exception as e:
        return {"error": str(e)}