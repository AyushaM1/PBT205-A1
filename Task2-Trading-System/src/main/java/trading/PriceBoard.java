package trading;

import com.google.gson.Gson;
import com.rabbitmq.client.BuiltinExchangeType;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import com.rabbitmq.client.DeliverCallback;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import javax.swing.BorderFactory;
import javax.swing.JFrame;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTable;
import javax.swing.SwingUtilities;
import javax.swing.table.DefaultTableModel;

public class PriceBoard {
    private static final Map<String, String> NAMES = Map.of(
        "XYZ", "XYZ Corp",
        "TORR", "Torrens University Australia");

    private static final int MAX_HISTORY = 200;
    private static final Path CLOSE_FILE = Path.of("closing_prices.csv");

    private static Map<String, String> loadPreviousCloses() {
        Map<String, String> closes = new LinkedHashMap<>();
        if (!Files.exists(CLOSE_FILE)) {
            return closes;
        }
        try {
            for (String line : Files.readAllLines(CLOSE_FILE)) {
                String[] parts = line.split(",");
                if (parts.length == 3 && !parts[0].equals("session_end")) {
                    closes.put(parts[1], parts[2]);
                }
            }
        } catch (IOException e) {
            System.out.println("Could not read " + CLOSE_FILE + ": " + e.getMessage());
        }
        return closes;
    }

    private static void saveClosingPrices(Map<String, Double> lastPrice) {
        if (lastPrice.isEmpty()) {
            return;
        }
        try {
            if (!Files.exists(CLOSE_FILE)) {
                Files.writeString(CLOSE_FILE, "session_end,symbol,closing_price" + System.lineSeparator());
            }
            String now = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
            StringBuilder sb = new StringBuilder();
            for (Map.Entry<String, Double> e : lastPrice.entrySet()) {
                sb.append(now).append(",").append(e.getKey()).append(",").append(e.getValue())
                  .append(System.lineSeparator());
            }
            Files.writeString(CLOSE_FILE, sb.toString(), StandardOpenOption.APPEND);
            System.out.println("Saved closing prices to " + CLOSE_FILE.toAbsolutePath());
        } catch (IOException e) {
            System.out.println("Could not save closing prices: " + e.getMessage());
        }
    }

    public static void main(String[] args) throws Exception {
        int port = Integer.parseInt(args[0]);

        Map<String, String> previousCloses = loadPreviousCloses();
        Map<String, Double> lastPrice = new ConcurrentHashMap<>();

        DefaultTableModel latestModel = new DefaultTableModel(
            new Object[] {"Symbol", "Company", "Latest price", "Previous close"}, 0);
        DefaultTableModel historyModel = new DefaultTableModel(
            new Object[] {"Time", "Symbol", "Price", "Qty", "Buyer", "Seller"}, 0);
        Map<String, Integer> rowOf = new HashMap<>();

        Set<String> symbols = new LinkedHashSet<>(java.util.List.of("XYZ", "TORR"));
        symbols.addAll(previousCloses.keySet());
        for (String symbol : symbols) {
            latestModel.addRow(new Object[] {
                symbol, NAMES.getOrDefault(symbol, symbol), "no trades yet",
                previousCloses.getOrDefault(symbol, "-")});
            rowOf.put(symbol, latestModel.getRowCount() - 1);
        }

        SwingUtilities.invokeLater(() -> {
            JScrollPane latestPane = new JScrollPane(new JTable(latestModel));
            latestPane.setBorder(BorderFactory.createTitledBorder("Latest price"));
            JScrollPane historyPane = new JScrollPane(new JTable(historyModel));
            historyPane.setBorder(BorderFactory.createTitledBorder("Trade history (newest first)"));

            JSplitPane split = new JSplitPane(JSplitPane.VERTICAL_SPLIT, latestPane, historyPane);
            split.setResizeWeight(0.3);

            JFrame frame = new JFrame("Trading board");
            frame.add(split);
            frame.setSize(680, 460);
            frame.addWindowListener(new WindowAdapter() {
                @Override
                public void windowClosing(WindowEvent e) {
                    saveClosingPrices(lastPrice);
                }
            });
            frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            frame.setVisible(true);
        });

        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        factory.setPort(port);

        Connection conn = factory.newConnection();
        Channel channel = conn.createChannel();
        channel.exchangeDeclare("trades", BuiltinExchangeType.FANOUT, true);
        String queue = channel.queueDeclare().getQueue();
        channel.queueBind(queue, "trades", "");

        Gson gson = new Gson();
        DateTimeFormatter clock = DateTimeFormatter.ofPattern("HH:mm:ss").withZone(ZoneId.systemDefault());

        DeliverCallback onTrade = (tag, delivery) -> {
            Trade trade = gson.fromJson(new String(delivery.getBody()), Trade.class);
            String time = clock.format(Instant.ofEpochMilli(trade.time()));
            lastPrice.put(trade.symbol(), trade.price());

            SwingUtilities.invokeLater(() -> {
                Integer row = rowOf.get(trade.symbol());
                if (row == null) {
                    latestModel.addRow(new Object[] {
                        trade.symbol(), NAMES.getOrDefault(trade.symbol(), trade.symbol()),
                        trade.price(), "-"});
                    rowOf.put(trade.symbol(), latestModel.getRowCount() - 1);
                } else {
                    latestModel.setValueAt(trade.price(), row, 2);
                }

                historyModel.insertRow(0, new Object[] {
                    time, trade.symbol(), trade.price(), trade.qty(), trade.buyer(), trade.seller()});
                if (historyModel.getRowCount() > MAX_HISTORY) {
                    historyModel.removeRow(historyModel.getRowCount() - 1);
                }
            });
        };

        channel.basicConsume(queue, true, onTrade, tag -> {});
    }
}