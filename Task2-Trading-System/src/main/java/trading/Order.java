package trading;

public record Order(String user, String side, String symbol, int qty, double price) {
    
}
