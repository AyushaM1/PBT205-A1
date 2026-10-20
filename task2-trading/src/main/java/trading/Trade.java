package trading;

public record Trade(String symbol, int qty, double price, String buyer, String seller, long time) {
    
}
