import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler

def prepare_data(data, look_back=60):
    """
    Zaman serisi verilerini RandomForest için hazırlar.
    """
    if len(data) < look_back:
        print(f"Veri uzunluğu ({len(data)}), look_back ({look_back}) değerinden küçük. Varsayılan veri kullanılacak.")
        data = np.array([30000 + i * 10 for i in range(look_back + 1)])  # Varsayılan veri (look_back + 1)

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data.reshape(-1, 1))

    X, y = [], []
    for i in range(look_back, len(scaled_data)):
        X.append(scaled_data[i-look_back:i, 0])
        y.append(scaled_data[i, 0])

    X, y = np.array(X), np.array(y)

    # Boş veri kontrolü
    if X.size == 0 or y.size == 0:
        print(f"Hazırlanan veri boş. X shape: {X.shape}, y shape: {y.shape}. Varsayılan veri kullanılacak.")
        return prepare_data(np.array([30000 + i * 10 for i in range(look_back + 1)]), look_back)

    return X, y, scaler

def train_model(data, look_back=60):
    """
    RandomForest modelini eğitir.
    """
    if len(data) == 0:
        print("Eğitim için boş veri sağlandı. Varsayılan veri kullanılacak.")
        data = np.array([30000 + i * 10 for i in range(look_back + 1)])  # Varsayılan veri

    try:
        X, y, scaler = prepare_data(data, look_back)
    except ValueError as e:
        print(f"Veri hazırlama sırasında hata oluştu: {e}")
        return None, None

    # Veri şekillendirme kontrolü
    if len(X.shape) != 2 or len(y.shape) != 1 or X.shape[0] == 0 or y.shape[0] == 0:
        print(f"X ve y boyutları uygun değil. X shape: {X.shape}, y shape: {y.shape}")
        return None, None

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model, scaler

def predict_model(model, scaler, data, look_back=60):
    """
    RandomForest modeli ile fiyat tahmini yapar.
    """
    if model is None or scaler is None:
        print("Model veya scaler mevcut değil, tahmin yapılamıyor.")
        return None

    if len(data) < look_back:
        print(f"Tahmin için yeterli veri yok. Varsayılan veri kullanılacak.")
        data = np.array([30000 + i * 10 for i in range(look_back + 1)])  # Varsayılan veri

    scaled_data = scaler.transform(data.reshape(-1, 1))
    X = [scaled_data[-look_back:]]
    X = np.array(X).reshape((1, look_back))  # 3 boyutlu veriyi 2 boyutlu hale getiriyoruz
    prediction = model.predict(X)
    return scaler.inverse_transform(prediction.reshape(-1, 1))[0][0]
