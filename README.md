# How to Run the Crypto Grid & Arbitrage Bot

This guide explains how to set up and run the Crypto Grid & Arbitrage Bot. Follow the steps below to get started.

---

## Requirements

1. **Python Version**:
   - Ensure you have Python 3.8 or higher installed on your system.

2. **Install Required Libraries**:
   - Install the necessary Python libraries by running the following command:
     ```bash
     pip install -r requirements.txt
     ```

3. **Set Up API Keys**:
   - Create a `.env` file in the project directory and add your Binance and KuCoin API keys as follows:
     ```
     BINANCE_API_KEY=your_binance_api_key
     BINANCE_API_SECRET=your_binance_api_secret
     KUCOIN_API_KEY=your_kucoin_api_key
     KUCOIN_API_SECRET=your_kucoin_api_secret
     KUCOIN_PASSPHRASE=your_kucoin_passphrase
     ```

---

## Running the Project

### 1. **Run the Dashboard**
   - The dashboard provides a web interface to monitor trade history and opportunities in real-time.
   - Start the dashboard by running:
     ```bash
     python [dashboard.py](http://_vscodecontentref_/0)
     ```
   - Open your browser and navigate to `http://localhost:8000` to access the dashboard.

---

### 2. **Run the Main Trading Script**
   - The main script executes the arbitrage strategies and listens to real-time price data.
   - Start the main script by running:
     ```bash
     python [main.py](http://_vscodecontentref_/1)
     ```
   - This script will:
     - Fetch real-time price data from Binance and KuCoin.
     - Execute **Grid Trading** and **Statistical Arbitrage** strategies.
     - Log trades and send updates to the dashboard.

---

### 3. **Test WebSocket Connections**
   - Test the WebSocket connections for Binance and KuCoin to ensure real-time data fetching works correctly.

   - To test Binance WebSocket:
     ```bash
     python [test_websocket.py](http://_vscodecontentref_/2)
     ```

   - To test KuCoin WebSocket:
     ```bash
     python [test_kucoin_websocket.py](http://_vscodecontentref_/3)
     ```

---

## Notes

- Ensure that your `.env` file contains valid API keys for Binance and KuCoin.
- The bot can run in simulation mode by setting `TEST_MODE = True` in `main.py`.
- Logs are saved in `binance_websocket.log` and `kucoin_websocket.log`.
- Trade history is saved in `trade_log.csv` for future analysis.

---

## License

This project is licensed under the MIT License.
