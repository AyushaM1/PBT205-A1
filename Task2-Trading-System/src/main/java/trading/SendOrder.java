package trading;

import com.google.gson.Gson;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;

public class SendOrder {
    public static void main(String[] args) throws Exception {
        if (args.length < 5) {
            System.out.println("Usage: SendOrder <username> <port> <BUY|SELL> <quantity> <price> [symbol]");
            return;
        }

        String user = args[0];
        int port = Integer.parseInt(args[1]);
        String side = args[2].toUpperCase();
        int qty = Integer.parseInt(args[3]);
        double price = Double.parseDouble(args[4]);
        String symbol = args.length > 5 ? args[5].toUpperCase() : "XYZ";

        if (!side.equals("BUY") && !side.equals("SELL")) {
            System.out.println("Side must be BUY or SELL");
            return;
        }

        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        factory.setPort(port);

        try (Connection conn = factory.newConnection();
             Channel channel = conn.createChannel()) {
            channel.queueDeclare("orders", true, false, false, null);
            String json = new Gson().toJson(new Order(user, side, symbol, qty, price));
            channel.basicPublish("", "orders", null, json.getBytes());
            System.out.println("Sent: " + json);
        }
    }
}