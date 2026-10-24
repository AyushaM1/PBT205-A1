package trading;

import com.google.gson.Gson;
import com.rabbitmq.client.BuiltinExchangeType;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import com.rabbitmq.client.DeliverCallback;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Consumer;

public class Exchange {
    public static void main(String[] args) throws Exception {
        int port = Integer.parseInt(args[0]);

        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        factory.setPort(port);

        Connection conn = factory.newConnection();
        Channel channel = conn.createChannel();
        channel.queueDeclare("orders", true, false, false, null);
        channel.exchangeDeclare("trades", BuiltinExchangeType.FANOUT, true);

        Gson gson = new Gson();
        Map<String, OrderBook> books = new HashMap<>();

        Consumer<Trade> publish = trade -> {
            try {
                channel.basicPublish("trades", "", null, gson.toJson(trade).getBytes());
            } catch (IOException e) {
                System.out.println("Could not publish trade: " + e.getMessage());
            }
        };

        DeliverCallback onOrder = (tag, delivery) -> {
            Order order = gson.fromJson(new String(delivery.getBody()), Order.class);
            OrderBook book = books.computeIfAbsent(order.symbol(), s -> new OrderBook(publish));
            book.handle(order);
            channel.basicAck(delivery.getEnvelope().getDeliveryTag(), false);
        };

        channel.basicConsume("orders", false, onOrder, tag -> {});
        System.out.println("Exchange waiting for orders...");
    }
}