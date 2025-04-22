import asyncio
import numpy as np
import json
import datetime
from lstm_model import train_model, predict_model
from websocket_manager import broadcast_trade_update  # WebSocket güncellemeleri için import


async def statistical_arbitrage(queue, pair1, pair2, threshold, historical_data_pair1, historical_data_pair2):
    """
    Statistical Arbitrage stratejisini uygular.
    """
    prices = {pair1: [], pair2: []}

    # Yeterli veri kontrolü
    if not historical_data_pair1 or len(historical_data_pair1) < 60:
        print(f"{pair1} için başlangıç verisi yetersiz. Varsayılan veri kullanılacak.")
        historical_data_pair1 = [30000 + i * 10 for i in range(60)]  # Varsayılan veri

    if not historical_data_pair2 or len(historical_data_pair2) < 60:
        print(f"{pair2} için başlangıç verisi yetersiz. Varsayılan veri kullanılacak.")
        historical_data_pair2 = [2000 + i * 5 for i in range(60)]  # Varsayılan veri

    # RandomForest modellerini eğit
    try:
        model1, scaler1 = train_model(np.array(historical_data_pair1), look_back=60)
        model2, scaler2 = train_model(np.array(historical_data_pair2), look_back=60)
    except ValueError as e:
        print(f"Model eğitimi sırasında hata oluştu: {e}")
        return  # Hata oluştuğunda işlemi durdur

    while True:
        price_info = await queue.get()
        symbol = price_info["symbol"]
        price = price_info["price"]

        if symbol in prices:
            prices[symbol].append(price)

        # Spread tahmini
        if len(prices[pair1]) > 60 and len(prices[pair2]) > 60:
            try:
                predicted_price1 = predict_model(model1, scaler1, np.array(prices[pair1][-60:]), look_back=60)
                predicted_price2 = predict_model(model2, scaler2, np.array(prices[pair2][-60:]), look_back=60)
                spread = predicted_price1 - predicted_price2

                print(f"Predicted Spread: {spread}")

                # Spread eşik değerini aştığında işlem yap
                if spread > threshold:
                    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    message = (
                        f"Spread genişledi: {pair1} {predicted_price1:.2f} fiyatından satıldı, "
                        f"{pair2} {predicted_price2:.2f} fiyatından alındı. İşlem saati: {current_time}."
                    )
                    print(f"WebSocket Mesajı Gönderiliyor: {message}")
                    broadcast_trade_update(json.dumps({"time": current_time, "message": message}))
                elif spread < -threshold:
                    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    message = (
                        f"Spread daraldı: {pair1} {predicted_price1:.2f} fiyatından alındı, "
                        f"{pair2} {predicted_price2:.2f} fiyatından satıldı. İşlem saati: {current_time}."
                    )
                    print(f"WebSocket Mesajı Gönderiliyor: {message}")
                    broadcast_trade_update(json.dumps({"time": current_time, "message": message}))
            except ValueError as e:
                print(f"Spread tahmini sırasında hata oluştu: {e}")
                continue
