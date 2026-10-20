
import argparse
import json
import uuid
import pika

parser = argparse.ArgumentParser()
parser.add_argument("--name", required=True)
parser.add_argument("--host", default="localhost")
args = parser.parse_args()

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=args.host)
)
channel = connection.channel()

for exchange in ["query", "query-response"]:
    channel.exchange_declare(
        exchange=exchange,
        exchange_type="fanout"
    )

# Subscribe before sending the query
result = channel.queue_declare(queue="", exclusive=True)
queue_name = result.method.queue

channel.queue_bind(
    exchange="query-response",
    queue=queue_name
)

print(f"Searching contact history for {args.name}...")

channel.basic_publish(
    exchange="query",
    routing_key="",
    body=args.name
)

try:
    for method, properties, body in channel.consume(
        queue_name,
        inactivity_timeout=10,
        auto_ack=True
    ):
        if body is None:
            print("No response received from tracker.")
            break

        response = json.loads(body.decode("utf-8"))

        if response.get("person") != args.name:
            continue

        contacts = response.get("contacts", [])

        print(f"\nContact history for {args.name}")

        if not contacts:
            print("No contacts recorded.")
        else:
            for contact in contacts:
                print(
                    f"- {contact['name']} "
                    f"(timestamp: {contact['timestamp']})"
                )

        break

finally:
    channel.cancel()
    connection.close()
