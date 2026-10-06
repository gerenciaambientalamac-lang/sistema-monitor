from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os, webbrowser

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", "8001"))

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
url = f"http://127.0.0.1:{PORT}/index.html"
print("\nLA LIBERTAD ESTE - PRUEBA FUNCIONAL R1")
print(f"Interfaz: {url}")
print("Cierre esta ventana para detener el servidor.\n")
try:
    webbrowser.open(url)
except Exception:
    pass
server.serve_forever()
