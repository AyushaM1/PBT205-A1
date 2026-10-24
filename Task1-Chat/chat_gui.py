import json
import queue
import threading
import tkinter as tk
from tkinter import messagebox
import pika


class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RabbitMQ Chat")
        self.root.geometry("600x500")

        self.username = ""
        self.room = ""
        self.connection = None
        self.channel = None
        self.messages = queue.Queue()
        self.running = False

        self.show_login()
        self.root.after(100, self.process_messages)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def show_login(self):
        self.login_frame = tk.Frame(self.root, padx=30, pady=30)
        self.login_frame.pack(expand=True)

        tk.Label(
            self.login_frame, text="RabbitMQ Chat",
            font=("Arial", 20, "bold")
        ).pack(pady=15)

        tk.Label(self.login_frame, text="Username").pack()
        self.username_entry = tk.Entry(self.login_frame, width=30)
        self.username_entry.pack(pady=5)

        tk.Label(self.login_frame, text="Chat room").pack()
        self.room_entry = tk.Entry(self.login_frame, width=30)
        self.room_entry.insert(0, "general")
        self.room_entry.pack(pady=5)

        tk.Button(
            self.login_frame, text="Join Chat",
            command=self.join_chat
        ).pack(pady=15)

    def join_chat(self):
        self.username = self.username_entry.get().strip()
        self.room = self.room_entry.get().strip()

        if not self.username or not self.room:
            messagebox.showwarning(
                "Missing information",
                "Enter a username and chat room."
            )
            return

        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="localhost", port=5672)
            )
            self.channel = self.connection.channel()

            self.channel.exchange_declare(
                exchange=self.room,
                exchange_type="fanout",
                durable=True
            )

            result = self.channel.queue_declare(
                queue="", exclusive=True
            )
            self.queue_name = result.method.queue

            self.channel.queue_bind(
                exchange=self.room,
                queue=self.queue_name
            )

            self.running = True
            self.login_frame.destroy()
            self.show_chat()

            threading.Thread(
                target=self.receive_messages,
                daemon=True
            ).start()

            self.display_message(
                f"Connected as {self.username} in room {self.room}"
            )

        except Exception as exc:
            messagebox.showerror(
                "Connection error",
                f"Could not connect to RabbitMQ:\n{exc}"
            )
            self.running = False
            if self.connection and self.connection.is_open:
                self.connection.close()

    def show_chat(self):
        top = tk.Frame(self.root, padx=10, pady=10)
        top.pack(fill="x")

        tk.Label(
            top,
            text=f"Room: {self.room}  |  User: {self.username}",
            font=("Arial", 12, "bold")
        ).pack(side="left")

        self.chat_box = tk.Text(
            self.root, state="disabled",
            wrap="word", font=("Arial", 11)
        )
        self.chat_box.pack(
            fill="both", expand=True, padx=10, pady=5
        )

        bottom = tk.Frame(self.root, padx=10, pady=10)
        bottom.pack(fill="x")

        self.message_entry = tk.Entry(bottom)
        self.message_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        self.message_entry.bind("<Return>", self.send_message)

        tk.Button(
            bottom, text="Send",
            command=self.send_message
        ).pack(side="right")

    def display_message(self, message):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", message + "\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def receive_messages(self):
        try:
            receive_connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="localhost", port=5672)
            )
            receive_channel = receive_connection.channel()

            receive_channel.exchange_declare(
                exchange=self.room,
                exchange_type="fanout",
                durable=True
            )

            result = receive_channel.queue_declare(
                queue="", exclusive=True
            )
            queue_name = result.method.queue

            receive_channel.queue_bind(
                exchange=self.room,
                queue=queue_name
            )

            for method, properties, body in receive_channel.consume(
                queue_name, inactivity_timeout=1, auto_ack=True
            ):
                if not self.running:
                    break

                if body:
                    try:
                        data = json.loads(body.decode("utf-8"))
                        text = f'{data["username"]}: {data["message"]}'
                    except (ValueError, KeyError, TypeError):
                        text = body.decode("utf-8", errors="replace")

                    self.messages.put(text)

            if receive_connection.is_open:
                receive_channel.cancel()
                receive_connection.close()

        except Exception as exc:
            if self.running:
                self.messages.put(f"Receive error: {exc}")

    def send_message(self, event=None):
        message = self.message_entry.get().strip()
        if not message:
            return

        data = {
            "type": "chat",
            "username": self.username,
            "room": self.room,
            "message": message
        }

        try:
            # Use a short-lived connection for each outgoing message.
            with pika.BlockingConnection(
                pika.ConnectionParameters(host="localhost", port=5672)
            ) as connection:
                channel = connection.channel()
                channel.exchange_declare(
                    exchange=self.room,
                    exchange_type="fanout",
                    durable=True
                )
                channel.basic_publish(
                    exchange=self.room,
                    routing_key="",
                    body=json.dumps(data)
                )

            self.message_entry.delete(0, "end")

        except Exception as exc:
            messagebox.showerror(
                "Send error", f"Could not send message:\n{exc}"
            )

    def process_messages(self):
        while not self.messages.empty():
            self.display_message(self.messages.get())

        self.root.after(100, self.process_messages)

    def close(self):
        self.running = False
        if self.connection and self.connection.is_open:
            self.connection.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatGUI(root)
    root.mainloop()
