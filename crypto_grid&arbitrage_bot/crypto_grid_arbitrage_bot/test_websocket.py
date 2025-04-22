import asyncio
from binance_websocket import binance_listener

async def main():
    symbol = "BTCUSDT"  # İzlemek istediğiniz sembol
    # Asyncio kuyruğu oluştur
    queue = asyncio.Queue()
    # Binance listener'ı ayrı bir görev olarak başlat
    task = asyncio.create_task(binance_listener(queue, symbol))
    
    # Kuyruktan gelen verileri dinle
    while True:
        price_info = await queue.get()
        print(f"Received: {price_info}")

if __name__ == "__main__":
    asyncio.run(main())
