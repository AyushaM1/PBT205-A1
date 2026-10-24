# Task 2: Trading System

PBT205 Project-based Learning Studio: Technology, Torrens University Australia, Assessment 1.

A small trading system built with Java and RabbitMQ. Traders send buy and sell orders, an exchange matches them, and a price board shows the latest trade prices. The programs never talk to each other directly. Everything goes through RabbitMQ.

Author: Shishir Khadka (Task 2, Trading System)

## How it works

```
SendOrder  ->  orders queue  ->  Exchange (order books)  ->  trades fanout exchange  ->  PriceBoard GUI / TradeListener
```

| Program | What it does |
|---|---|
| `SendOrder` | Command-line trader. Sends one order, then exits. |
| `Exchange` | Reads orders, matches buys and sells, and publishes trades. |
| `OrderBook` | The waiting buys and sells for one stock (used by `Exchange`). |
| `PriceBoard` | Swing window with the latest price, trade history and previous close. |
| `TradeListener` | Debug tool that prints every trade as JSON. |
| `Order`, `Trade` | The message classes, sent as JSON. |

### Topics

| Name | Type | Used for |
|---|---|---|
| `orders` | Durable queue | Orders from `SendOrder` to the exchange |
| `trades` | Fanout exchange | Every trade, copied to each listener (GUI, listener) |

A fanout exchange keeps nothing for programs that are not running, so start the GUI and the listener before sending orders.

### Matching rules

- Waiting buys are sorted highest price first. Waiting sells are sorted lowest price first. Ties go to the earlier order.
- An incoming BUY matches the lowest waiting SELL if the sell price is at or below the buy price.
- An incoming SELL matches the highest waiting BUY if the buy price is at or above the sell price.
- The trade happens at the price of the order that was already waiting.
- If there is no match, the order waits in the book.
- Every order is for 100 shares, and each stock has its own order book.

### Message formats

```json
{"user":"shishir","side":"SELL","symbol":"XYZ","qty":100,"price":10.0}
{"symbol":"XYZ","qty":100,"price":10.0,"buyer":"sam","seller":"shishir","time":1760000000000}
```

The first is an order. The second is a trade.

## Requirements

- Docker
- Java 17 (JDK)
- Maven (tested with 3.10.0)

Libraries (downloaded by Maven): RabbitMQ Java client 5.36.0, Gson 2.14.0, SLF4J 2.0.18.

## Setup

Run all commands from this folder (the one that contains `pom.xml`).

1. Start RabbitMQ in Docker and leave it running:

```
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

The management page is at http://localhost:15672 (login `guest` / `guest`). The code also works with `rabbitmq:4-management`.

2. Build the project:

```
mvn compile
```

## Running

Use one terminal for each program. The commands work in PowerShell and Git Bash. Start them in this order.

**Exchange** (terminal 2). Wait for `Exchange waiting for orders...`:

```
mvn compile exec:java "-Dexec.mainClass=trading.Exchange" "-Dexec.args=5672"
```

**Price board** (terminal 3). A window opens on your desktop:

```
mvn compile exec:java "-Dexec.mainClass=trading.PriceBoard" "-Dexec.args=5672"
```

**Trade listener** (optional, terminal 4):

```
mvn exec:java "-Dexec.mainClass=trading.TradeListener" "-Dexec.args=5672"
```

**Send orders** (terminal 5):

```
mvn -q exec:java "-Dexec.mainClass=trading.SendOrder" "-Dexec.args=<username> <port> <BUY|SELL> <quantity> <price> [symbol]"
```

| Argument | Meaning |
|---|---|
| `username` | Name of the trader |
| `port` | RabbitMQ port (5672) |
| `BUY` or `SELL` | Side of the order |
| `quantity` | Number of shares (100) |
| `price` | The most a buyer will pay, or the least a seller will accept |
| `symbol` | Optional stock symbol. Defaults to `XYZ`. |

## Example

```
mvn -q exec:java "-Dexec.mainClass=trading.SendOrder" "-Dexec.args=shishir 5672 SELL 100 10.00"
mvn -q exec:java "-Dexec.mainClass=trading.SendOrder" "-Dexec.args=sam 5672 BUY 100 11.00"
```

The exchange prints:

```
BOOK: waiting SELL shishir @ 10.0
TRADE: XYZ 100 @ 10.0 buyer=sam seller=shishir
```

The trade happens at 10.0, the price of the order that was already waiting. The price board shows 10.0 for XYZ.

A second stock works the same way. Add its symbol at the end:

```
mvn -q exec:java "-Dexec.mainClass=trading.SendOrder" "-Dexec.args=shishir 5672 SELL 100 20.00 TORR"
mvn -q exec:java "-Dexec.mainClass=trading.SendOrder" "-Dexec.args=sam 5672 BUY 100 20.00 TORR"
```

Orders for different symbols never match each other.

## Price board

- The top table shows the latest trade price and the previous close for each stock. XYZ and TORR are listed from the start, and any other symbol is added when it first trades.
- The bottom table shows the trade history, newest first (up to 200 trades) while the window is open.
- **Closing prices:** when you close the window with the X button, the last trade price of each stock that traded is saved to `closing_prices.csv` in the folder you ran Maven from. Next time, that price is shown as the previous close. Stopping the program with Ctrl+C or closing the terminal does not save it.

## Tests

| # | Orders (in order) | Expected |
|---|---|---|
| 1 | SELL 10.00, BUY 9.00 | No trade. Both orders wait. |
| 2 | SELL 10.00, BUY 10.00 | Trade at 10.0 |
| 3 | SELL 10.00, BUY 11.00 | Trade at 10.0 |
| 4 | SELL 10.00, SELL 10.50, BUY 11.00, BUY 10.50 | Trade at 10.0, then trade at 10.5 |
| 5 | BUY 11.00, BUY 10.00, SELL 9.50 | Trade at 11.0 |
| 6 | One XYZ pair and one TORR pair | Separate trades, and each stock updates on its own |
| 7 | Close the price board, then reopen it | Closing prices saved and shown as previous close |
| 8 | Side typed as `SEL` | Error message, nothing sent |

Restart the exchange between tests 1 to 5 so the order book starts empty. Results and screenshots are in the individual document.

## Project structure

```
Task2-Trading-System/
|-- pom.xml
|-- README.md
`-- src/main/java/trading/
    |-- Order.java
    |-- Trade.java
    |-- OrderBook.java
    |-- Exchange.java
    |-- SendOrder.java
    |-- PriceBoard.java
    `-- TradeListener.java
```

`closing_prices.csv` is created when you run the price board and is not committed to the repository.

## Limitations

- The order book is held in memory, so it is lost when the exchange stops. Only closing prices are saved.
- Trades are missed by any listener that is not running when they happen.
- There are no market orders, partial fills, cancellations, accounts or settlement.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Connection refused` | RabbitMQ is not running or the port is wrong. Start the Docker command first. |
| `release version 25 not supported` | In `pom.xml`, set `maven.compiler.release` to `17`. |
| `mvn` is not recognized | Add Maven's `bin` folder to your Path, set `JAVA_HOME` to JDK 17, and open a new terminal. |
| Error about `transient_nonexcl_queues` | RabbitMQ 4 rejects non-durable queues. The code declares `orders` as durable, so make sure you are running the latest code. |
| `SLF4J: Failed to load class` lines | A harmless logging warning. To remove it, add `org.slf4j:slf4j-api:2.0.18` to the dependencies in `pom.xml`. |
| The price board window does not appear | Check the taskbar. It can open behind other windows. |
| Prices do not update | Make sure the exchange is running, and start the price board before sending orders. |
