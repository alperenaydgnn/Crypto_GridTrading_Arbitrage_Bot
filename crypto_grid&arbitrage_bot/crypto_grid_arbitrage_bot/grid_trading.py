from lstm_model import train_model, predict_model
import numpy as np

async def grid_trading(queue, symbol, grid_size, grid_count, historical_data):
    """
    Grid Trading stratejisini uygular.
    """
    prices = []
    grid_levels = []

    # Yeterli veri kontrolü
    if not historical_data or len(historical_data) < 60:
        print(f"Başlangıç verisi yetersiz. Varsayılan veri kullanılacak. (Mevcut uzunluk: {len(historical_data) if historical_data else 0})")
        historical_data = [30000 + i * 10 for i in range(60)]  # Varsayılan veri

    # RandomForest modelini eğit
    try:
        model, scaler = train_model(np.array(historical_data), look_back=60)
        if model is None or scaler is None:
            print("Model veya scaler oluşturulamadı. İşlem durduruluyor.")
            return
    except ValueError as e:
        print(f"Model eğitimi sırasında hata oluştu: {e}")
        return  # Hata oluştuğunda işlemi durdur

    while True:
        price_info = await queue.get()
        price = price_info["price"]
        prices.append(price)

        # Yeterli veri olup olmadığını kontrol et
        if len(prices) < 60:
            print(f"Yeterli veri yok, fiyatlar toplanıyor... (Şu anki uzunluk: {len(prices)})")
            continue

        # RandomForest ile fiyat tahmini
        try:
            predicted_price = predict_model(model, scaler, np.array(prices[-60:]), look_back=60)
            if predicted_price is None:
                print("Tahmin yapılamadı. Model veya scaler eksik.")
                continue
            print(f"Predicted Price for {symbol}: {predicted_price}")
        except ValueError as e:
            print(f"Fiyat tahmini sırasında hata oluştu: {e}")
            continue

        # Grid seviyelerini oluştur
        if not grid_levels:
            mid_price = predicted_price
            grid_levels = [mid_price + (i * grid_size) for i in range(-grid_count, grid_count + 1)]

        # Grid seviyelerinde işlem yap
        for level in grid_levels:
            if price <= level:
                print(f"Grid Trading | Symbol: {symbol} | Level: {level} | Action: Buying | Price: {price}")
                grid_levels.remove(level)
                grid_levels.append(level - grid_size)
            elif price >= level:
                print(f"Grid Trading | Symbol: {symbol} | Level: {level} | Action: Selling | Price: {price}")
                grid_levels.remove(level)
                grid_levels.append(level + grid_size)
