package trading;

import java.util.Comparator;
import java.util.PriorityQueue;
import java.util.function.Consumer;

public class OrderBook {
    private record Resting(Order order, long seq) {}

    private long counter = 0;
    private final Consumer<Trade> onTrade;

    private final PriorityQueue<Resting> buys = new PriorityQueue<>(
        Comparator.comparingDouble((Resting r) -> r.order().price()).reversed()
                  .thenComparingLong(Resting::seq));

    private final PriorityQueue<Resting> sells = new PriorityQueue<>(
        Comparator.comparingDouble((Resting r) -> r.order().price())
                  .thenComparingLong(Resting::seq));

    public OrderBook(Consumer<Trade> onTrade) {
        this.onTrade = onTrade;
    }

    public void handle(Order order) {
        if (order.side().equals("BUY")) {
            Resting best = sells.peek();
            if (best != null && best.order().price() <= order.price()) {
                sells.poll();
                executeTrade(order, best.order(), best.order().price());
            } else {
                buys.add(new Resting(order, counter++));
                System.out.println("BOOK: waiting BUY " + order.user() + " @ " + order.price());
            }
        } else {
            Resting best = buys.peek();
            if (best != null && best.order().price() >= order.price()) {
                buys.poll();
                executeTrade(best.order(), order, best.order().price());
            } else {
                sells.add(new Resting(order, counter++));
                System.out.println("BOOK: waiting SELL " + order.user() + " @ " + order.price());
            }
        }
    }

    private void executeTrade(Order buy, Order sell, double price) {
        Trade trade = new Trade(buy.symbol(), buy.qty(), price, buy.user(), sell.user(),
            System.currentTimeMillis());
        System.out.println("TRADE: " + trade.symbol() + " " + trade.qty() + " @ " + price
            + " buyer=" + trade.buyer() + " seller=" + trade.seller());
        onTrade.accept(trade);
    }
}