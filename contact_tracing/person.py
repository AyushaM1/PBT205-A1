
import argparse
import json
import random
import time
import pika

parser = argparse.ArgumentParser()
parser.add_argument("--name", required=True)
parser.add_argument("--speed", type=float, default=1.0)
parser.add_argument("--size", type=int, default=10)
parser.add_argument("--host", default="localhost")
args = parser.parse_args()

if args.speed <= 0:
    parser.error("Speed must be greater than zero")

if not 1 <= args.size <= 1000:
    parser.error("Grid size must be between 1 and 1000")

x = random.randrange(args.size)
y = random.randrange(args.size)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=args.host)
)
channel = connection.channel()

channel.exchange_declare(
    exchange="position",
    exchange_type="fanout"
)

print(f"{args.name} started at ({x}, {y})")

try:
    while True:
        message = {
            "person": args.name,
            "x": x,
            "y": y,
            "timestamp": time.time()
        }

        channel.basic_publish(
            exchange="position",
            routing_key="",
            body=json.dumps(message)
        )

        print(f"{args.name} position: ({x}, {y})")

        time.sleep(args.speed)

        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])

        x = max(0, min(args.size - 1, x + dx))
        y = max(0, min(args.size - 1, y + dy))

except KeyboardInterrupt:
    print(f"\n{args.name} stopped.")

finally:
    connection.close()
