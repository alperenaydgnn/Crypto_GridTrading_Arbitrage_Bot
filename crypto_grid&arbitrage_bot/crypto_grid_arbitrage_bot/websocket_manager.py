import asyncio
import json

# WebSocket bağlantılarını takip etmek için bir liste
active_connections = []

def broadcast_trade_update(trade_message):
    """
    Tüm aktif WebSocket bağlantılarına yeni bir trade mesajı gönderir.
    """
    for connection in active_connections:
        try:
            asyncio.create_task(connection.send_text(trade_message))
        except Exception as e:
            print(f"WebSocket bağlantısına mesaj gönderilemedi: {e}")
            active_connections.remove(connection)

async def test_broadcast():
    """
    Test amaçlı bir mesajı tüm WebSocket bağlantılarına gönderir.
    """
    test_message = {"time": "2023-01-01 12:00:00", "message": "Test mesajı: WebSocket bağlantısı çalışıyor."}
    broadcast_trade_update(json.dumps(test_message))
