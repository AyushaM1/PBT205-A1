import sys
import threading
import pika

if len(sys.argv) < 3:
    print("Usage: python chat.py <username> <room>")
    sys.exit(1)

username = sys.argv[1]
room = sys.argv[2]


# -------------------------
# RECEIVE MESSAGES
# -------------------------
def receive_messages():

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost", port=5672)
    )

    channel = connection.channel()

    # Each room has its own fanout exchange
    channel.exchange_declare(
        exchange=room,
        exchange_type="fanout",
        durable=True
    )

    # Temporary queue for this user
    result = channel.queue_declare(
        queue="",
        exclusive=True
    )

    queue_name = result.method.queue

    # Join the selected room
    channel.queue_bind(
        exchange=room,
        queue=queue_name
    )

    def receive_message(ch, method, properties, body):
        print(f"\n{body.decode()}")
        print("> ", end="", flush=True)

    channel.basic_consume(
        queue=queue_name,
        on_message_callback=receive_message,
        auto_ack=True
    )

    channel.start_consuming()


# Start receiving messages
receiver_thread = threading.Thread(
    target=receive_messages,
    daemon=True
)

receiver_thread.start()


# -------------------------
# SEND MESSAGES
# -------------------------

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost", port=5672)
)

channel = connection.channel()

channel.exchange_declare(
    exchange=room,
    exchange_type="fanout",
    durable=True
)

print(f"Connected as {username}")
print(f"Room: {room}")
print("Type a message and press Enter.")
print("Type /quit to exit.")

while True:

    message = input("> ")

    if message == "/quit":
        break

    if message.strip():

        full_message = f"{username}: {message}"

        channel.basic_publish(
            exchange=room,
            routing_key="",
            body=full_message
        )

connection.close()

print("Disconnected.")