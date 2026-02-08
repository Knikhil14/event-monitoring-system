#!/usr/bin/env python3
"""
Real-time monitoring script
"""
import psutil
import time
import requests
import json
from datetime import datetime

def collect_system_metrics():
    """Collect system metrics"""
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'network_io': psutil.net_io_counters()._asdict()
    }

def send_metrics(endpoint_url):
    """Send metrics to monitoring endpoint"""
    metrics = collect_system_metrics()
    
    try:
        response = requests.post(
            endpoint_url,
            json={
                'event_type': 'system_metrics',
                'source': 'monitoring_agent',
                'severity': 'info',
                'metrics': metrics
            },
            timeout=5
        )
        return response.status_code == 202
    except Exception as e:
        print(f"Failed to send metrics: {e}")
        return False

def main():
    endpoint = "http://events.yourdomain.com/api/events"
    
    print("Starting real-time monitoring...")
    print(f"Sending metrics to: {endpoint}")
    
    while True:
        success = send_metrics(endpoint)
        status = "✓" if success else "✗"
        print(f"{datetime.now().strftime('%H:%M:%S')} - Sent metrics {status}")
        time.sleep(30)  # Send every 30 seconds

if __name__ == "__main__":
    main()