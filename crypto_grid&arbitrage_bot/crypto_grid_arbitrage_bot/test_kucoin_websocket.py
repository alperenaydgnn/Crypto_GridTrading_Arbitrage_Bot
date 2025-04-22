import asyncio
from kucoin_websocket import kucoin_listener

async def main():
    symbol = "BTC-USDT"  # KuCoin sembol formatı
    queue = asyncio.Queue()
    task = asyncio.create_task(kucoin_listener(queue, symbol))
    
    while True:
        price_info = await queue.get()
        print(f"Received: {price_info}")

if __name__ == "__main__":
    asyncio.run(main())
