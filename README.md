# PBT205 Assessment 1: Chat, Trading and Contact Tracing

PBT205 Project-based Learning Studio: Technology, Torrens University Australia.

Three prototypes that communicate through RabbitMQ: a chat application, a trading system and a contact-tracing simulation. Each prototype is made of command-line applications with a GUI built on top. All three share one RabbitMQ instance running in Docker, and exchange structured JSON messages.

## Team

| Member | Prototype | Role |
|---|---|---|
| Ayusha Manandhar | Task 1: Chat | Chat prototype, team communication |
| Shishir Khadka | Task 2: Trading system | Trading prototype, GUI and testing |
| Rouwen Rivaldo Sung | Task 3: Contact tracing | Contact-tracing prototype |
| Khulan Bayarerdene | Integration | Integration of the three prototypes, final submission |

## Repository structure

```
PBT205-A1/
|-- README.md
|-- docs/                        message format diagrams
|-- Task1-Chat/                  Python (pika)
|-- Task2-Trading-System/        Java 17, Maven
`-- Task3-Contact-Tracing/       python (Pika)
```

Each task folder has its own README with detailed run steps, tests and limitations, and an `evidence/` folder with screenshots.

## Requirements

| Tool | Used for |
|---|---|
| Docker (Docker Desktop) | Running RabbitMQ |
| Python 3 and `pika` | Task 1: Chat |
| Java 17 and Maven 3.x | Task 2: Trading system |
| [ADD: tools for Task 3] | Task 3: Contact tracing |

## Setup: start RabbitMQ (once, for all three tasks)

Run this in a terminal and leave it running:

```
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

- Applications connect on port **5672**.
- The management page is at http://localhost:15672 (login `guest` / `guest`). It shows the queues, exchanges and connections of all three tasks.
- Everyone should use the same RabbitMQ version. This is the version in the assessment brief. Newer RabbitMQ 4 rejects non-durable queues that version 3 accepts, so declare durable queues if you use it.

## Topics used by each task

| Task | Topics |
|---|---|
| Task 1: Chat | `room` (one per chat room) |
| Task 2: Trading | `orders` (durable queue) and `trades` (fanout exchange) |
| Task 3: Contact tracing | `position`, `query` and `query-response` |

The names do not overlap, so all three tasks can run against the same RabbitMQ at the same time.

## Task 1: Chat

A Python command-line chat built with RabbitMQ and `pika`. Users connect with a username, join a room, and exchange messages with the other users in that room. There is a GUI and support for multiple rooms.

```
cd Task1-Chat
pip install pika
python chat.py Alice general
```

Open a second terminal and start another user in the same room:

```
python chat.py Ayu general
```

Type a message and press Enter to send it. Type `/quit` to leave.



See `Task1-Chat/README.md` for more.

## Task 2: Trading system

Traders send BUY and SELL orders with a price (100 shares each). An exchange keeps an order book for each stock, matches orders at the price of the order that was already waiting, and publishes every trade. A GUI shows the latest price, a trade history and the previous closing price, and supports multiple stocks (XYZ and TORR).

```
cd Task2-Trading-System
mvn compile
```

Start each program in its own terminal:

```
mvn compile exec:java "-Dexec.mainClass=trading.Exchange" "-Dexec.args=5672"
mvn compile exec:java "-Dexec.mainClass=trading.PriceBoard" "-Dexec.args=5672"
mvn -q exec:java "-Dexec.mainClass=trading.SendOrder" "-Dexec.args=shishir 5672 SELL 100 10.00"
mvn -q exec:java "-Dexec.mainClass=trading.SendOrder" "-Dexec.args=sam 5672 BUY 100 11.00"
```

The exchange prints `TRADE: XYZ 100 @ 10.0 ...` and the price board shows 10.0. Start the price board before sending orders.

See `Task2-Trading-System/README.md` for more.

## Task 3: Contact tracing

A simulation of people moving around a grid. A tracker records positions and which people shared a square, and users can query the contact history of any person. There is a GUI showing the environment.



See `Task3-Contact-Tracing/README.md` for more.

## Running all three tasks together

1. Start RabbitMQ once (see Setup).
2. Start each task as described above, each program in its own terminal.
3. Check http://localhost:15672: the Queues and Exchanges tabs should list the queues and exchanges of all three tasks.

## Testing and evidence

- Each team member tested their own prototype. Test tables, results and screenshots are in each member's individual document.
- Screenshots are also kept in each task's `evidence/` folder.
- Integration testing (all three prototypes together on one RabbitMQ) was done by Khulan Bayarerdene.

## Known limitations

- Trading: the order book is held in memory, so it is lost when the exchange stops. Only closing prices are saved. There are no market orders, partial fills or settlement.
- Contact tracing: verification of the contact-search results was still in progress when this was written. 


## Troubleshooting

| Problem | Fix |
|---|---|
| `Connection refused` | RabbitMQ is not running or the port is wrong. Start the Docker command first. |
| Error about `transient_nonexcl_queues` | RabbitMQ 4 rejects non-durable queues. Use the RabbitMQ 3 image above, or declare queues as durable. |
| `ModuleNotFoundError: No module named 'pika'` | Run `pip install pika`. |
| `mvn` is not recognized | Install Maven, add its `bin` folder to your Path, set `JAVA_HOME` to JDK 17, and open a new terminal. |
| A GUI window does not appear | Check the taskbar. It can open behind other windows. |
| Prices or messages do not update | Make sure RabbitMQ and the exchange (or tracker) are running before the GUI. |