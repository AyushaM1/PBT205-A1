
import json
import queue
import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import pika
import subprocess
import sys
from pathlib import Path


class ContactGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Contact Tracing Dashboard")
        self.root.geometry("850x650")

        self.grid_size = 10
        self.positions = {}
        self.person_processes = {}
        self.messages = queue.Queue()
        self.running = True

        self.build_interface()

        threading.Thread(
            target=self.listen_rabbitmq,
            daemon=True
        ).start()

        self.root.after(100, self.process_messages)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build_interface(self):
        tk.Label(
            self.root,
            text="Contact Tracing Dashboard",
            font=("Arial", 22, "bold")
        ).pack(pady=15)

        controls = tk.Frame(self.root)
        controls.pack(pady=5)

        tk.Label(controls, text="Grid size:").pack(side="left")

        self.size_entry = tk.Entry(controls, width=8)
        self.size_entry.insert(0, "10")
        self.size_entry.pack(side="left", padx=5)

        tk.Button(
            controls,
            text="Apply Grid",
            command=self.change_grid
        ).pack(side="left")

        self.status_label = tk.Label(
            self.root,
            text="Connecting to RabbitMQ..."
        )
        self.status_label.pack(pady=5)
        
        # Add Person controls
        person_frame = tk.Frame(self.root)
        person_frame.pack(pady=10)

        tk.Label(
            person_frame,
            text="Add Person:"
        ).pack(side="left", padx=5)

        self.new_person_entry = tk.Entry(
            person_frame,
            width=15
        )
        self.new_person_entry.pack(side="left", padx=5)

        tk.Label(
            person_frame,
            text="Speed (seconds):"
        ).pack(side="left", padx=5)

        self.speed_entry = tk.Entry(
            person_frame,
            width=6
        )
        self.speed_entry.insert(0, "1")
        self.speed_entry.pack(side="left", padx=5)

        tk.Button(
            person_frame,
            text="Add Person",
            command=self.add_person
        ).pack(side="left", padx=5)

        tk.Button(
            person_frame,
            text="Remove Person",
            command=self.remove_person,
            width=15
        ).pack(side="left", padx=5)


        self.canvas = tk.Canvas(
            self.root,
            width=440,
            height=440,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray"
        )
        self.canvas.pack(pady=10)

        search = tk.Frame(self.root)
        search.pack(pady=5)

        tk.Label(search, text="Person name:").pack(side="left")

        self.name_entry = tk.Entry(search, width=20)
        self.name_entry.pack(side="left", padx=5)

        tk.Button(
            search,
            text="Search Contacts",
            command=self.search_contacts
        ).pack(side="left")

        self.results = tk.Text(
            self.root,
            width=75,
            height=6,
            state="disabled"
        )
        self.results.pack(pady=10)

        self.draw_grid()

    
    def add_person(self):
        name = self.new_person_entry.get().strip()

        if not name:
            messagebox.showwarning(
                "Missing name",
                "Please enter a person name."
            )
            return

        try:
            speed = float(self.speed_entry.get())

            if speed <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Invalid speed",
                "Enter a speed greater than zero."
            )
            return

        # Prevent duplicate people from this GUI
        if name in self.person_processes or name in self.positions:
            messagebox.showwarning(
                "Duplicate person",
                f"{name} already exists."
            )
            return

        script = Path(__file__).resolve().parent / "person.py"

        try:
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(script),
                    "--name", name,
                    "--speed", str(speed),
                    "--size", str(self.grid_size)
                ],
                cwd=str(script.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            self.person_processes[name] = process
            self.new_person_entry.delete(0, "end")

            self.status_label.config(
                text=f"Started simulation for {name}"
            )

        except Exception as exc:
            messagebox.showerror(
                "Error",
                f"Could not start person:\n{exc}"
            )

    
    def remove_person(self):
        name = self.new_person_entry.get().strip()

        if not name:
            messagebox.showwarning(
                "Missing name",
                "Enter the name of the person to remove."
            )
            return

        process = self.person_processes.get(name)

        if process is None:
            messagebox.showwarning(
                "Person not found",
                "This person was not started by this GUI."
            )
            return

        if process.poll() is None:
            process.terminate()

        del self.person_processes[name]
        try:
            with pika.BlockingConnection(
                pika.ConnectionParameters(host="localhost")
            ) as connection:
                channel = connection.channel()
                channel.exchange_declare(
                    exchange="position",
                    exchange_type="fanout"
                )
                channel.basic_publish(
                    exchange="position",
                    routing_key="",
                    body=json.dumps({
                        "type": "remove",
                        "person": name
                    })
                )
        except Exception as exc:
            messagebox.showwarning(
                "RabbitMQ warning",
                f"Removal message failed: {exc}"
            )

        # Remove person from the visual grid
        self.positions.pop(name, None)
        self.draw_grid()

        self.new_person_entry.delete(0, "end")

        self.status_label.config(
            text=f"Removed {name} from the simulation"
        )


    def change_grid(self):
        try:
            size = int(self.size_entry.get())
            if not 1 <= size <= 1000:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid size",
                "Enter a grid size between 1 and 1000."
            )
            return

        self.grid_size = size
        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        size = self.grid_size
        width = 440
        cell = width / size

        # Avoid drawing thousands of grid lines
        if size <= 50:
            for i in range(size + 1):
                p = i * cell
                self.canvas.create_line(p, 0, p, width,
                                        fill="#dddddd")
                self.canvas.create_line(0, p, width, p,
                                        fill="#dddddd")

        occupied = {}

        for person, (x, y) in self.positions.items():
            if 0 <= x < size and 0 <= y < size:
                occupied.setdefault((x, y), []).append(person)

        for (x, y), people in occupied.items():
            center_x = (x + 0.5) * cell
            center_y = (y + 0.5) * cell

            radius = min(12, max(2, cell * 0.38))

            color = "#e74c3c" if len(people) > 1 else "#3498db"

            self.canvas.create_oval(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                fill=color,
                outline=""
            )

            if size <= 20:
                self.canvas.create_text(
                    center_x,
                    center_y,
                    text=", ".join(people),
                    font=("Arial", 8),
                    fill="white"
                )

    def listen_rabbitmq(self):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="localhost")
            )
            channel = connection.channel()

            for exchange in ["position", "query-response"]:
                channel.exchange_declare(
                    exchange=exchange,
                    exchange_type="fanout"
                )

                result = channel.queue_declare(
                    queue="", exclusive=True
                )
                channel.queue_bind(
                    exchange=exchange,
                    queue=result.method.queue
                )

                channel.basic_consume(
                    queue=result.method.queue,
                    on_message_callback=self.receive_message,
                    auto_ack=True
                )

            self.messages.put(("status", "Connected to RabbitMQ"))

            while self.running:
                connection.process_data_events(time_limit=0.5)

            connection.close()

        except Exception as exc:
            self.messages.put(("status", f"Connection error: {exc}"))

    def receive_message(self, ch, method, properties, body):
        try:
            data = json.loads(body.decode("utf-8"))

            if "x" in data and "y" in data and "person" in data:
                self.messages.put(("position", data))

            elif "contacts" in data and "person" in data:
                self.messages.put(("contacts", data))

        except (ValueError, TypeError):
            pass

    def process_messages(self):
        while not self.messages.empty():
            kind, data = self.messages.get()

            if kind == "position":
                self.positions[data["person"]] = (
                    data["x"], data["y"]
                )
                self.draw_grid()

            elif kind == "contacts":
                if data["person"] == self.name_entry.get().strip():
                    self.show_contacts(data)

            elif kind == "status":
                self.status_label.config(text=data)

        if self.running:
            self.root.after(100, self.process_messages)

    def search_contacts(self):
        name = self.name_entry.get().strip()

        if not name:
            messagebox.showwarning(
                "Missing name",
                "Please enter a person name."
            )
            return

        try:
            with pika.BlockingConnection(
                pika.ConnectionParameters(host="localhost")
            ) as connection:
                channel = connection.channel()

                channel.exchange_declare(
                    exchange="query",
                    exchange_type="fanout"
                )

                channel.basic_publish(
                    exchange="query",
                    routing_key="",
                    body=name
                )

            self.set_results(f"Searching contacts for {name}...")

        except Exception as exc:
            messagebox.showerror("RabbitMQ error", str(exc))

    def show_contacts(self, data):
        name = data["person"]
        contacts = sorted(
            data.get("contacts", []),
            key=lambda c: c["timestamp"],
            reverse=True
        )

        text = f"Contact history for {name}\n\n"

        if not contacts:
            text += "No contacts recorded."
        else:
            for contact in contacts:
                time_text = datetime.fromtimestamp(
                    contact["timestamp"]
                ).strftime("%Y-%m-%d %H:%M:%S")

                text += f"{contact['name']} - {time_text}\n"

        self.set_results(text)

    def set_results(self, text):
        self.results.config(state="normal")
        self.results.delete("1.0", "end")
        self.results.insert("end", text)
        self.results.config(state="disabled")

    
    def close(self):
        self.running = False

        for process in self.person_processes.values():
            if process.poll() is None:
                process.terminate()

        self.root.destroy()



if __name__ == "__main__":
    root = tk.Tk()
    app = ContactGUI(root)
    root.mainloop()

