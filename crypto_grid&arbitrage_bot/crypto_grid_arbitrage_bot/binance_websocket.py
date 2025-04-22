import websockets
import json
import asyncio
import logging

# Loglama ayarları
logging.basicConfig(
    filename="binance_websocket.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def binance_listener(queue, symbols):
    """
    Binance Testnet'ten birden fazla sembol için fiyat akışını dinler.
    Gelen her fiyat güncellemesi, aşağıdaki formatta kuyruğa eklenir:
      {
        "exchange": "binance",
        "symbol": symbol,
        "price": float
      }
    """
    uri = f"wss://testnet.binance.vision/ws"
    streams = "/".join([f"{symbol.lower()}@ticker" for symbol in symbols])
    uri = f"{uri}/{streams}"
    
    while True:
        try:
            async with websockets.connect(uri) as ws:
                while True:
                    data = await ws.recv()
                    price_data = json.loads(data)
                    if 's' in price_data and 'c' in price_data:
                        symbol = price_data['s']
                        price = float(price_data['c'])
                        await queue.put({
                            "exchange": "binance",
                            "symbol": symbol,
                            "price": price
                        })
        except Exception as e:
            logging.error(f"Bağlantı hatası: {e}")
            print(f"Bağlantı hatası: {e}. 5 saniye sonra yeniden denenecek...")
            await asyncio.sleep(5)
