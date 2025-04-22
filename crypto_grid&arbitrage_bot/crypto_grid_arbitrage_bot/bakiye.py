from binance.client import Client
from kucoin.client import Client as KucoinClient
from dotenv import load_dotenv
import os

load_dotenv()

# Binance Bakiyesi (Sadeleştirilmiş)
def get_binance_balance(client):
    balances = client.futures_account_balance()
    simplified = []
    for asset in balances:
        if float(asset['balance']) > 0:  # Sadece pozitif bakiyeleri göster
            simplified.append({
                "Asset": asset['asset'],
                "Balance": asset['balance']
            })
    return simplified

# KuCoin Bakiyesi (Sadeleştirilmiş)
def get_kucoin_balance(client):
    accounts = client.get_accounts(account_type="trade")  # Sadece trade hesabı
    simplified = []
    for acc in accounts:
        if float(acc['balance']) > 0:  # Sadece pozitif bakiyeleri göster
            simplified.append({
                "Currency": acc['currency'],
                "Type": acc['type'],
                "Balance": acc['balance']
            })
    return simplified

# Ana Kod
if __name__ == "__main__":
    # Binance
    binance_client = Client(
        os.getenv("BINANCE_API_KEY"),
        os.getenv("BINANCE_API_SECRET"),
        testnet=True
    )
    binance_balance = get_binance_balance(binance_client)
    print("\n=== Binance Bakiyesi ===")
    for item in binance_balance:
        print(f"{item['Asset']}: {item['Balance']}")

    # KuCoin
    kucoin_client = KucoinClient(
        os.getenv("KUCOIN_API_KEY"),
        os.getenv("KUCOIN_API_SECRET"),
        os.getenv("KUCOIN_PASSPHRASE")
    )
    kucoin_balance = get_kucoin_balance(kucoin_client)
    print("\n=== KuCoin Bakiyesi ===")
    for item in kucoin_balance:
        print(f"{item['Currency']} ({item['Type']}): {item['Balance']}")