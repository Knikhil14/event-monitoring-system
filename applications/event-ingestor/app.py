from flask import Flask, request, jsonify
import redis
import psycopg2
import json
import os
from datetime import datetime
import pika

app = Flask(__name__)

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'eventdb')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')

# Initialize connections
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def publish_to_queue(event_data):
    """Publish event to RabbitMQ for async processing"""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()
    channel.queue_declare(queue='event_queue', durable=True)
    
    channel.basic_publish(
        exchange='',
        routing_key='event_queue',
        body=json.dumps(event_data),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        )
    )
    connection.close()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "event-ingestor"}), 200

@app.route('/api/events', methods=['POST'])
def receive_event():
    try:
        event_data = request.json
        
        # Validate required fields
        required_fields = ['event_type', 'source', 'severity']
        for field in required_fields:
            if field not in event_data:
                return jsonify({"error": f"Missing field: {field}"}), 400
        
        # Add metadata
        event_data['timestamp'] = datetime.utcnow().isoformat()
        event_data['ingestion_time'] = datetime.utcnow().isoformat()
        event_data['status'] = 'pending'
        
        # Store in Redis for real-time access
        event_id = f"event:{datetime.utcnow().timestamp()}"
        redis_client.hset(event_id, mapping=event_data)
        redis_client.expire(event_id, 3600)  # Expire after 1 hour
        
        # Publish to queue for async processing
        publish_to_queue(event_data)
        
        # Store in PostgreSQL (sync for critical events)
        if event_data['severity'] in ['critical', 'high']:
            store_in_database(event_data)
        
        return jsonify({
            "message": "Event received successfully",
            "event_id": event_id,
            "timestamp": event_data['timestamp']
        }), 202
        
    except Exception as e:
        app.logger.error(f"Error processing event: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def store_in_database(event_data):
    """Store event in PostgreSQL"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO events (event_type, source, severity, message, metadata, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            event_data.get('event_type'),
            event_data.get('source'),
            event_data.get('severity'),
            event_data.get('message', ''),
            json.dumps(event_data.get('metadata', {})),
            event_data.get('timestamp')
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        app.logger.error(f"Database error: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)