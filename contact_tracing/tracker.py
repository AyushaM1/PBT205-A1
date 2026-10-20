
import json
import time
from datetime import datetime
import pika

# Store people's latest positions and contact history
positions = {}
contacts = {}

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost")
)
channel = connection.channel()

# RabbitMQ exchanges
for exchange in ["position", "query", "query-response"]:
    channel.exchange_declare(
        exchange=exchange,
        exchange_type="fanout"
    )

# Receive position updates
position_queue = channel.queue_declare(
    queue="", exclusive=True
).method.queue

channel.queue_bind(
    exchange="position",
    queue=position_queue
)

# Receive contact history queries
query_queue = channel.queue_declare(
    queue="", exclusive=True
).method.queue

channel.queue_bind(
    exchange="query",
    queue=query_queue
)


def handle_position(ch, method, properties, body):
    data = json.loads(body.decode("utf-8"))

    if data.get("type") == "remove":
        person = data["person"]
        positions.pop(person, None)
        print(f"{person} removed from tracking")
        return

    person = data["person"]
    x = data["x"]
    y = data["y"]

    positions[person] = (x, y)

    print(f"{person} moved to ({x}, {y})")

    # Detect people occupying the same square
    for other, other_position in positions.items():
        if other == person:
            continue

        if other_position == (x, y):
            timestamp = time.time()

            contacts.setdefault(person, []).append({
                "name": other,
                "timestamp": timestamp
            })

            contacts.setdefault(other, []).append({
                "name": person,
                "timestamp": timestamp
            })

            print(f"CONTACT: {person} and {other}")


def handle_query(ch, method, properties, body):
    person = body.decode("utf-8").strip()

    history = sorted(
        contacts.get(person, []),
        key=lambda record: record["timestamp"],
        reverse=True
    )

    response = {
        "person": person,
        "contacts": history
    }

    channel.basic_publish(
        exchange="query-response",
        routing_key="",
        body=json.dumps(response)
    )

    print(f"Query received for {person}")


channel.basic_consume(
    queue=position_queue,
    on_message_callback=handle_position,
    auto_ack=True
)

channel.basic_consume(
    queue=query_queue,
    on_message_callback=handle_query,
    auto_ack=True
)

print("Contact tracker running...")
print("Waiting for position updates and queries...")

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("\nTracker stopped.")
finally:
    connection.close()
