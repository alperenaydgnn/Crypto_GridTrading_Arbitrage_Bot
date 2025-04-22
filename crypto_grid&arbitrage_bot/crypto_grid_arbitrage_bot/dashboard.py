import asyncio  # Eksik olan asyncio modülünü içe aktarıyoruz
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn
from websocket_manager import active_connections  # WebSocket bağlantıları
from websocket_manager import test_broadcast  # Test fonksiyonunu içe aktar

app = FastAPI(title="Arbitraj Bot Dashboard")

@app.get("/", response_class=HTMLResponse)
async def read_dashboard():
    html_content = """
    <html>
      <head>
        <title>Arbitraj Bot Dashboard</title>
        <style>
          table {
            width: 100%;
            border-collapse: collapse;
          }
          th, td {
            border: 1px solid black;
            padding: 8px;
            text-align: left;
          }
          th {
            background-color: #f2f2f2;
          }
        </style>
      </head>
      <body>
        <h1>Trade History</h1>
        <table>
          <thead>
            <tr>
              <th>Zaman</th>
              <th>İşlem</th>
            </tr>
          </thead>
          <tbody id="trade-history">
          </tbody>
        </table>
        <script>
          const ws = new WebSocket("ws://localhost:8000/ws");
          ws.onopen = function() {
            console.log("WebSocket bağlantısı kuruldu.");
          };
          ws.onmessage = function(event) {
            try {
              console.log("WebSocket'ten mesaj alındı:", event.data);
              const tradeHistory = document.getElementById("trade-history");
              const tradeData = JSON.parse(event.data);
              const newRow = document.createElement("tr");
              newRow.innerHTML = `
                <td>${tradeData.time}</td>
                <td>${tradeData.message}</td>
              `;
              tradeHistory.appendChild(newRow);
            } catch (error) {
              console.error("WebSocket mesajı işlenirken hata oluştu:", error);
            }
          };
          ws.onerror = function(error) {
            console.error("WebSocket hatası:", error);
          };
          ws.onclose = function() {
            console.log("WebSocket bağlantısı kapatıldı.");
          };
        </script>
      </body>
    </html>
    """
    return html_content

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # WebSocket bağlantısını açık tutmak için
    except Exception:
        active_connections.remove(websocket)

@app.get("/test")
async def test_websocket():
    """
    WebSocket bağlantısını test etmek için bir endpoint.
    """
    await test_broadcast()
    return {"status": "Test mesajı gönderildi."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
