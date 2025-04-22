import websockets
import json
import asyncio
import aiohttp
import time
import logging

# Loglama ayarları
logging.basicConfig(
    filename="kucoin_websocket.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def get_kucoin_token():
    """
    KuCoin API'den token ve endpoint bilgilerini alır.
    """
    url = "https://api.kucoin.com/api/v1/bullet-public"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as resp:
            data = await resp.json()
            return data['data']['token'], data['data']['instanceServers'][0]['endpoint']

async def kucoin_listener(queue, symbols):
    """
    KuCoin üzerinden birden fazla sembol için fiyat akışını dinler.
    Gelen her fiyat güncellemesi aşağıdaki formatta kuyruğa eklenir:
      {
        "exchange": "kucoin",
        "symbol": symbol,
        "price": float
      }
    """
    while True:
        try:
            token, endpoint = await get_kucoin_token()
            ws_url = f"{endpoint}?token={token}&connectId=my_arbitrage_bot"
            async with websockets.connect(ws_url, ping_interval=20) as ws:
                # Semboller için subscribe ol
                for symbol in symbols:
                    await ws.send(json.dumps({
                        "id": int(time.time()),
                        "type": "subscribe",
                        "topic": f"/market/ticker:{symbol}",
                        "response": True
                    }))
                while True:
                    data = await ws.recv()
                    ticker = json.loads(data)
                    if 'data' in ticker and 'price' in ticker['data']:
                        symbol = ticker['topic'].split(":")[1]
                        price = float(ticker['data']['price'])
                        await queue.put({
                            "exchange": "kucoin",
                            "symbol": symbol,
                            "price": price
                        })
        except Exception as e:
            logging.error(f"KuCoin bağlantı hatası: {e}")
            print(f"KuCoin bağlantı hatası: {e}. 5 saniye sonra yeniden bağlanıyor...")
            await asyncio.sleep(5)
