from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, EMAIndicator, PSARIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice, OnBalanceVolumeIndicator, ChaikinMoneyFlowIndicator

def calculate_technical_indicators(data):
    """
    Teknik analiz göstergelerini hesaplar ve veri setine ekler.
    """
    df = pd.DataFrame(data)
    df['high'] = df['price']  # Eğer sadece 'price' varsa, 'high' olarak kullan
    df['low'] = df['price']   # Eğer sadece 'price' varsa, 'low' olarak kullan
    df['close'] = df['price'] # 'close' fiyatı olarak 'price' kullan
    df['volume'] = 1  # Eğer gerçek hacim verisi yoksa varsayılan olarak 1 kullan

    # Mevcut göstergeler
    df['RSI'] = RSIIndicator(df['close']).rsi()
    df['MACD'] = MACD(df['close']).macd()
    bollinger = BollingerBands(df['close'])
    df['Bollinger_Upper'] = bollinger.bollinger_hband()
    df['Bollinger_Lower'] = bollinger.bollinger_lband()
    stochastic = StochasticOscillator(df['high'], df['low'], df['close'])
    df['Stochastic'] = stochastic.stoch()
    vwap = VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'])
    df['VWAP'] = vwap.volume_weighted_average_price()

    # Yeni göstergeler
    df['ATR'] = AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
    df['EMA_10'] = EMAIndicator(df['close'], window=10).ema_indicator()
    df['EMA_50'] = EMAIndicator(df['close'], window=50).ema_indicator()
    df['OBV'] = OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume()
    df['CMF'] = ChaikinMoneyFlowIndicator(df['high'], df['low'], df['close'], df['volume']).chaikin_money_flow()
    
    # Williams %R hesaplama
    period = 14  # Williams %R için varsayılan periyot
    df['WilliamsR'] = ((df['high'].rolling(window=period).max() - df['close']) /
                       (df['high'].rolling(window=period).max() - df['low'].rolling(window=period).min())) * -100

    df['Parabolic_SAR'] = PSARIndicator(df['high'], df['low'], df['close']).psar()

    return df

def train_model(data):
    """
    Makine öğrenimi modeli için eğitim verilerini kullanarak bir model oluşturur.
    """
    df = calculate_technical_indicators(data)
    df = df.dropna()  # Eksik verileri kaldır

    # Veri setinin boş olup olmadığını kontrol et
    if df.empty or len(df) < 1:
        print("Yeterli veri yok, model eğitimi atlanıyor.")
        return None, None

    X = df[['RSI', 'MACD', 'Bollinger_Upper', 'Bollinger_Lower', 'Stochastic', 'VWAP',
            'ATR', 'EMA_10', 'EMA_50', 'OBV', 'CMF', 'WilliamsR', 'Parabolic_SAR']].values  # Teknik göstergeler
    y = df['price'].values  # Fiyatlar

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)
    return model, scaler

def predict_price(model, scaler, indicators):
    """
    Eğitilmiş modeli kullanarak fiyat tahmini yapar.
    """
    if model is None or scaler is None:
        print("Model veya scaler mevcut değil, tahmin yapılamıyor.")
        return None

    X = np.array([indicators])
    X_scaled = scaler.transform(X)
    predicted_price = model.predict(X_scaled)[0]
    return predicted_price
