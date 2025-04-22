import asyncio
import os
from dotenv import load_dotenv
from binance_websocket import binance_listener
from kucoin_websocket import kucoin_listener
from binance.client import Client as BinanceClient
from kucoin.client import Trade  # KuCoin SDK'dan Trade sınıfını içe aktarın
from datetime import datetime
import platform
import os
import csv  # Loglama için
import random  # Basit tahmin modeli için
from ml_model import train_model, predict_price  # Makine öğrenimi fonksiyonlarını içe aktar
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice
import pandas as pd  # pandas kütüphanesini içe aktar
from grid_trading import grid_trading
from statistical_arbitrage import statistical_arbitrage
from websocket_manager import broadcast_trade_update  # WebSocket güncellemeleri için import
import json  # Eksik olan json modülünü içe aktarıyoruz

if platform.system() == 'Windows':
    import winsound

load_dotenv()

# --- Ayarlar ---
FEE_TOTAL = 0.002  # Toplam işlem ücreti (her borsada %0.1, toplam %0.2)

# İzlemek istediğiniz coin çiftleri (Binance formatında)
symbols_binance = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "SHIBUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT"]

def format_kucoin_symbol(symbol):
    """
    Binance formatındaki sembolü, KuCoin formatına çevirir.
    Örneğin: "SHIBUSDT" -> "SHIB-USDT"
    """
    return symbol[:-4] + "-" + symbol[-4:]

def get_exchange_symbol(exchange, symbol):
    """
    Emir gönderirken kullanılacak sembolü, borsa bazında ayarlar.
    Eğer exchange "kucoin" ise sembolü KuCoin formatına dönüştürür.
    """
    if exchange == "kucoin":
        return format_kucoin_symbol(symbol)
    return symbol

# KuCoin için sembol listesi (dinleyici tarafında ayrı oluşturuluyor)
symbols_kucoin = [format_kucoin_symbol(sym) for sym in symbols_binance]

# Hedef kâr yüzdeleri coin bazında (örneğin BTC için %0.2, ETH için %0.3, DOGE için %1.5, SHIB için %2, BNB için %0.5)
TARGET_PROFIT_PERCENTAGE = {
    "BTCUSDT": 0.002, "ETHUSDT": 0.003, "DOGEUSDT": 0.015, "SHIBUSDT": 0.02, 
    "BNBUSDT": 0.005, "SOLUSDT": 0.004, "ADAUSDT": 0.003, "XRPUSDT": 0.0025
}

# Global trade geçmişi; dashboard veya loglama amacıyla kullanılacak
trade_history = []

# --- Sesli Uyarı Fonksiyonu ---
def play_alert():
    if platform.system() == 'Windows':
        winsound.Beep(2500, 1000)
    elif platform.system() == 'Darwin':
        os.system('say "Arbitrage opportunity detected"')
    else:
        print('\a')

# --- Yardımcı Fonksiyonlar ---
def normalize_symbol(exchange, symbol):
    """
    KuCoin'ten gelen sembol formatını, Binance formatına dönüştürür.
    """
    if exchange == "kucoin":
        return symbol.replace("-", "")
    return symbol

def calculate_trade_size(balance, risk_percentage, price):
    return (balance * risk_percentage) / price

def get_coin_from_symbol(symbol):
    """Örneğin: BTCUSDT için coin kısmı 'BTC' dir."""
    return symbol[:-4]

# Pozisyon kontrolü: Eğer satış yapılacak borsada ilgili coin envanteri yetersizse,
# otomatik market alım emri vererek envanteri oluşturur (simülasyon amaçlı).
def ensure_coin_inventory(exchange, symbol, required_amount, binance_client, kucoin_client):
    coin = get_coin_from_symbol(symbol)
    coin_balance = 0.0  # Varsayılan: henüz coin yok.
    print(f"[{exchange}] Mevcut {coin} bakiyesi: {coin_balance}")
    
    if coin_balance < required_amount:
        needed = required_amount - coin_balance
        print(f"[{exchange}] {coin} envanteri yetersiz. {needed:.6f} {coin} almak için market alım emri veriliyor.")
        # Burada gerçek emir gönderme yapılmalı; simülasyon amaçlı, alımın başarılı olduğunu varsayıyoruz.
        coin_balance += needed
        print(f"[{exchange}] Yeni {coin} bakiyesi: {coin_balance}")
    else:
        print(f"[{exchange}] {coin} envanteri yeterli.")
    
    return coin_balance

# --- Dinamik Risk Yönetimi ---
def calculate_dynamic_risk(symbol, spread_percentage):
    """
    Spread yüzdesine göre dinamik risk yüzdesi hesaplar.
    Daha yüksek spread yüzdesi, daha yüksek risk yüzdesi anlamına gelir.
    """
    base_risk = 0.02  # Minimum risk yüzdesi (örneğin %2)
    max_risk = 0.1    # Maksimum risk yüzdesi (örneğin %10)
    risk = base_risk + (spread_percentage * (max_risk - base_risk))
    return min(max_risk, max(base_risk, risk))  # Risk yüzdesini sınırlandır

# --- Trade Execution (Otomatik Pozisyon Yönetimi ile) ---
# Test modu ayarı
TEST_MODE = True  # True olduğunda gerçek emir gönderilmez, işlemler simüle edilir.

async def execute_arbitrage_trade(symbol, buy_exchange, sell_exchange, buy_price, sell_price, binance_client, kucoin_client):
    global trade_history
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # İşlem başlangıç zamanı
    print(f"\n[{start_time}] [Trade Execution Triggered for {symbol}]")
    print(f"Plan: Buy on {buy_exchange} at {buy_price}, Sell on {sell_exchange} at {sell_price}")
    
    try:
        if buy_exchange == "binance":
            buy_balance_data = binance_client.futures_account_balance()
            buy_balance = float([asset['balance'] for asset in buy_balance_data if asset['asset'] == "USDT"][0])
        else:
            buy_accounts = kucoin_client.get_accounts(account_type="trade")
            buy_balance = float([acc['balance'] for acc in buy_accounts if acc['currency'] == "USDT"][0])
    except Exception as e:
        print(f"[{buy_exchange}] USDT bakiye kontrol hatası: {e}")
        return

    # Dinamik risk yüzdesini hesapla
    spread_percentage = abs(buy_price - sell_price) / ((buy_price + sell_price) / 2)
    dynamic_risk_percentage = calculate_dynamic_risk(symbol, spread_percentage)
    trade_size = calculate_trade_size(buy_balance, dynamic_risk_percentage, buy_price)
    
    print(f"[{buy_exchange}] Available USDT: {buy_balance:.2f}")
    print(f"Calculated trade size for {symbol}: {trade_size:.6f} (base asset miktarı)")
    print(f"Dynamic Risk Percentage: {dynamic_risk_percentage * 100:.2f}%")
    
    # Pozisyon kontrolü: Satış yapılacak borsada yeterli coin yoksa, otomatik alım yap.
    if sell_exchange == "binance":
        ensure_coin_inventory(sell_exchange, symbol, trade_size, binance_client, kucoin_client)
    else:
        ensure_coin_inventory(sell_exchange, symbol, trade_size, binance_client, kucoin_client)
    
    if TEST_MODE:
        print("[TEST MODE] Gerçek emir gönderilmiyor, işlem simüle ediliyor.")
        order_response_buy = {"status": "simulated", "side": "BUY", "quantity": trade_size}
        order_response_sell = {"status": "simulated", "side": "SELL", "quantity": trade_size}
    else:
        order_response_buy = None
        order_response_sell = None

        try:
            if buy_exchange == "binance":
                order_response_buy = binance_client.futures_create_order(
                    symbol=symbol,
                    side='BUY',
                    type='MARKET',
                    quantity=trade_size
                )
            else:
                # KuCoin emir gönderirken sembolü doğru formata çeviriyoruz.
                order_response_buy = kucoin_client.create_market_order(
                    symbol=get_exchange_symbol("kucoin", symbol),
                    side='buy',
                    size=trade_size
                )
        except Exception as e:
            print(f"[{buy_exchange}] Alış emri gönderiminde hata: {e}")
            return

        try:
            if sell_exchange == "binance":
                order_response_sell = binance_client.futures_create_order(
                    symbol=symbol,
                    side='SELL',
                    type='MARKET',
                    quantity=trade_size
                )
            else:
                order_response_sell = kucoin_client.create_market_order(
                    symbol=get_exchange_symbol("kucoin", symbol),
                    side='sell',
                    size=trade_size
                )
        except Exception as e:
            print(f"[{sell_exchange}] Satış emri gönderiminde hata: {e}")
            return

    # Stop-Loss ve Take-Profit kontrolü
    spread = (sell_price - buy_price) / buy_price
    target_profit = TARGET_PROFIT_PERCENTAGE.get(symbol, 0.005)  # Varsayılan hedef kâr %0.5
    if spread < -FEE_TOTAL:
        print(f"[{symbol}] Stop-Loss tetiklendi! İşlem iptal edildi. Spread: {spread * 100:.2f}%")
        return
    elif spread >= target_profit:
        print(f"[{symbol}] Take-Profit tetiklendi! İşlem başarıyla tamamlandı. Spread: {spread * 100:.2f}%")

    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # İşlem bitiş zamanı
    trade_message = {
        "time": end_time,
        "message": f"{symbol} satıldı, {sell_exchange} -> {buy_exchange} üzerinden {trade_size:.6f} miktarında işlem yapıldı."
    }
    print(trade_message)
    trade_history.append(trade_message)
    broadcast_trade_update(json.dumps(trade_message))  # WebSocket üzerinden güncelleme gönder
    print("-----\n")
    await asyncio.sleep(0)

# --- Loglama Fonksiyonu ---
def log_trade(trade_data):
    """
    İşlemleri bir CSV dosyasına kaydeder.
    """
    with open("trade_log.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(trade_data)

# --- Basit Tahmin Modeli ---
def predict_spread(base_price, intermediate_price, quote_price):
    """
    Basit bir tahmin modeli kullanarak spread tahmini yapar.
    """
    noise = random.uniform(-0.001, 0.001)  # Rastgele bir sapma ekler
    implied_quote = intermediate_price * quote_price
    predicted_spread = (implied_quote - base_price) / base_price + noise
    return predicted_spread

# --- Analyzer ---
async def analyzer(queue, exchange):
    """
    Gelen verileri işleyip, aynı borsa içinde dinamik üçlü arbitraj fırsatlarını analiz eder.
    Spread hesaplamasına işlem ücretleri dahil edilmiştir.
    """
    prices = {}  # { "BTCUSDT": fiyat, "ETHUSDT": fiyat, ... }
    trading_pairs = [
        ("BTCUSDT", "ETHBTC", "ETHUSDT"),
        ("BTCUSDT", "BNBBTC", "BNBUSDT"),
        ("ETHUSDT", "BNBETH", "BNBUSDT")
    ]

    while True:
        if queue.empty():
            print("Kuyruk boş, veri bekleniyor...")
        price_info = await queue.get()
        print(f"Queue'dan veri alındı: {price_info}")

        symbol = price_info["symbol"]
        price = price_info["price"]

        # Fiyatları güncelle
        prices[symbol] = price
        print(f"Fiyatlar güncellendi: {prices}")

        # Üçgen arbitraj fırsatlarını analiz et
        for pair in trading_pairs:
            if all(p in prices for p in pair):
                base, intermediate, quote = pair
                base_price = prices[base]
                intermediate_price = prices[intermediate]
                quote_price = prices[quote]

                # Üçgen arbitraj döngüsü
                implied_quote = (1 / base_price) * intermediate_price * quote_price
                profit = implied_quote - 1  # Döngü sonunda kâr oranı

                print(f"[{exchange}] {base} -> {intermediate} -> {quote} Döngü Kârı: {profit * 100:.2f}%")

                # İşlem ücretlerini hesaba kat
                effective_profit = profit - FEE_TOTAL
                if effective_profit >= 0.01:  # %1 kâr hedefi
                    # Momentum göstergelerini kontrol et
                    rsi = RSIIndicator(pd.Series([base_price])).rsi().iloc[-1]
                    macd = MACD(pd.Series([base_price])).macd().iloc[-1]

                    print(f"[{exchange}] RSI: {rsi:.2f}, MACD: {macd:.2f}")

                    if rsi < 30 and macd > 0:  # Momentum göstergeleri olumlu
                        play_alert()  # Alarm çal
                        print(f"[{exchange}] Üçgen arbitraj fırsatı tespit edildi! Kâr: {effective_profit * 100:.2f}%")
                        log_trade([datetime.now(), exchange, base, intermediate, quote, profit, effective_profit])

# --- Main ---
async def safe_task(task_func, *args):
    """
    Güvenli bir şekilde bir asyncio görevi çalıştırır.
    Hata oluşursa loglar ve görevi yeniden başlatır.
    """
    while True:
        try:
            await task_func(*args)
        except Exception as e:
            print(f"Hata oluştu: {e}. Görev yeniden başlatılıyor...")
            await asyncio.sleep(5)

async def fetch_initial_data(symbol, client, look_back=60):
    """
    Binance veya KuCoin'den başlangıç verilerini alır.
    """
    historical_data = []
    try:
        # Binance için doğru API çağrısı
        klines = client.get_historical_klines(symbol, BinanceClient.KLINE_INTERVAL_1MINUTE, f"{look_back} minutes ago UTC")
        historical_data = [float(kline[4]) for kline in klines]  # Kapanış fiyatlarını al
    except Exception as e:
        print(f"Başlangıç verisi alınırken hata oluştu: {e}")
    return historical_data

async def main():
    """
    Grid Trading ve Statistical Arbitrage stratejilerini paralel olarak çalıştırır.
    """
    # Binance ve KuCoin için ayrı kuyruklar oluştur
    queue_binance = asyncio.Queue()
    queue_kucoin = asyncio.Queue()

    # Binance istemcisi oluştur
    binance_client = BinanceClient(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))

    # Gerçek zamanlı başlangıç verilerini al
    historical_data_binance = await fetch_initial_data("BTCUSDT", binance_client, look_back=60)
    if not historical_data_binance or len(historical_data_binance) < 60:
        print("Başlangıç verisi alınamadı veya yeterli veri yok. Varsayılan veri kullanılacak.")
        historical_data_binance = [30000 + i * 10 for i in range(60)]  # Varsayılan veri

    historical_data_kucoin = [2000 + i * 5 for i in range(100)]  # KuCoin için örnek veri (güncellenmeli)

    # Görevleri tanımla
    tasks = [
        # Binance dinleyici
        asyncio.create_task(safe_task(binance_listener, queue_binance, symbols_binance)),

        # KuCoin dinleyici
        asyncio.create_task(safe_task(kucoin_listener, queue_kucoin, symbols_kucoin)),

        # Grid Trading
        asyncio.create_task(grid_trading(queue_binance, "BTCUSDT", grid_size=50, grid_count=5, historical_data=historical_data_binance)),

        # Statistical Arbitrage
        asyncio.create_task(statistical_arbitrage(queue_binance, "BTCUSDT", "ETHUSDT", threshold=2,
                                                  historical_data_pair1=historical_data_binance,
                                                  historical_data_pair2=historical_data_kucoin))
    ]

    # Tüm görevleri paralel olarak çalıştır
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    # Binance ve KuCoin istemcilerini oluştur
    binance_client = BinanceClient(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    kucoin_client = Trade(
        key=os.getenv("KUCOIN_API_KEY"),
        secret=os.getenv("KUCOIN_API_SECRET"),
        passphrase=os.getenv("KUCOIN_PASSPHRASE")
    )

    # Ana işlemi çalıştır
    asyncio.run(main())
