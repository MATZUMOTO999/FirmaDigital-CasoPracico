import json
import logging
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765
# El límite reduce el uso accidental o abusivo de memoria al recibir archivos.
MAX_PDF_SIZE = 25 * 1024 * 1024
ROOT = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Sirve únicamente los archivos del directorio donde reside la aplicación.
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, status, payload):
        # Centraliza el formato de respuesta usado por los endpoints de la API.
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Health check para comprobar que el proceso local está disponible.
        if self.path == "/api/health":
            self.send_json(200, {"ok": True})
            return
        if self.path == "/style.css":
            stylesheet = (ROOT / "style.css").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/css; charset=utf-8")
            self.send_header("Content-Length", str(len(stylesheet)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(stylesheet)
            return
        if self.path not in ("/", "/index.html"):
            self.send_json(404, {"error": "Ruta no encontrada."})
            return
        page = (ROOT / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self):
        # El único POST permitido valida un PDF enviado desde la interfaz local.
        if self.path != "/api/validate":
            self.send_json(404, {"error": "Ruta no encontrada."})
            return
        if self.headers.get("Origin") not in (f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}"):
            self.send_json(403, {"error": "Origen de solicitud no permitido."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Tamaño de solicitud inválido."})
            return

        if length <= 0 or length > MAX_PDF_SIZE:
            self.send_json(413, {"error": "El PDF está vacío o supera el límite de 25 MB."})
            return

        # Lee exactamente el tamaño declarado y rechaza cargas incompletas o no PDF.
        document = self.rfile.read(length)
        if len(document) != length:
            self.send_json(400, {"error": "No se recibió el archivo completo."})
            return
        if b"%PDF-" not in document[:1024]:
            self.send_json(415, {"error": "El archivo no tiene una cabecera PDF válida."})
            return

        # Esta demo valida formato y límite de tamaño, no la autenticidad del documento.
        message = "PDF válido: el archivo tiene cabecera PDF válida y se procesa localmente sin exigir firma digital."
        payload = {
            "valid": True,
            "error": None,
            "message": message,
            "signatures": [{
                "index": 1,
                "accepted": True,
                "signature_valid": False,
                "intact": True,
                "trusted": False,
                "coverage": "SIN_FIRMA",
                "detail": "Esta demo no exige firma digital; solo comprueba que el archivo es un PDF válido y está dentro del límite permitido.",
            }],
        }
        self.send_json(200, payload)

    def log_message(self, format_string, *args):
        # Mantiene el registro HTTP integrado con el formato común de logging.
        logging.info("%s - %s", self.address_string(), format_string % args)


if __name__ == "__main__":
    # El enlace a loopback evita exponer el validador directamente a la red.
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    logging.info("Servidor local de PDF sin firma digital disponible en http://localhost:%s", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Deteniendo servidor local.")
    finally:
        server.server_close()
