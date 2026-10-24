package trading;

import com.rabbitmq.client.BuiltinExchangeType;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import com.rabbitmq.client.DeliverCallback;

public class TradeListener {
    public static void main(String[] args) throws Exception {
        int port = Integer.parseInt(args[0]);

        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        factory.setPort(port);

        Connection conn = factory.newConnection();
        Channel channel = conn.createChannel();
        channel.exchangeDeclare("trades", BuiltinExchangeType.FANOUT, true);
        String queue = channel.queueDeclare().getQueue();
        channel.queueBind(queue, "trades", "");

        DeliverCallback onTrade = (tag, delivery) ->
            System.out.println("Trade received: " + new String(delivery.getBody()));

        channel.basicConsume(queue, true, onTrade, tag -> {});
        System.out.println("Listening for trades...");
    }
}