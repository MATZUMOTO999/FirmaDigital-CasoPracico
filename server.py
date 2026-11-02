import json
import logging
import ssl
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path

from asn1crypto import x509
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko_certvalidator import ValidationContext


HOST = "127.0.0.1"
PORT = 8765
MAX_PDF_SIZE = 25 * 1024 * 1024
ROOT = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def load_system_trust_roots():
    certificates = ssl.create_default_context().get_ca_certs(binary_form=True)
    roots = [x509.Certificate.load(certificate) for certificate in certificates]
    if not roots:
        raise RuntimeError("No se encontraron CA confiables en el almacén del sistema.")
    return roots


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/health":
            self.send_json(200, {"ok": True})
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
        if self.path != "/api/validate":
            self.send_json(404, {"error": "Ruta no encontrada."})
            return
        if self.headers.get("Origin") not in (f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}"):
            self.send_json(403, {"error": "Origen de solicitud no permitido."})
            return
        if self.headers.get_content_type() != "application/pdf":
            self.send_json(415, {"error": "Solo se aceptan documentos PDF."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Tamaño de solicitud inválido."})
            return
        if length <= 0 or length > MAX_PDF_SIZE:
            self.send_json(413, {"error": "El PDF está vacío o supera el límite de 25 MB."})
            return

        document = self.rfile.read(length)
        if len(document) != length:
            self.send_json(400, {"error": "No se recibió el archivo completo."})
            return
        if b"%PDF-" not in document[:1024]:
            self.send_json(415, {"error": "El archivo no tiene una cabecera PDF válida."})
            return

        try:
            reader = PdfFileReader(BytesIO(document))
            signatures = []
            validation_context = ValidationContext(
                trust_roots=load_system_trust_roots(),
                allow_fetching=False,
            )
            for index, embedded_signature in enumerate(reader.embedded_signatures, start=1):
                try:
                    status = validate_pdf_signature(
                        embedded_signature,
                        signer_validation_context=validation_context,
                    )
                    coverage = getattr(status.coverage, "name", str(status.coverage))
                    intact = bool(status.intact)
                    signature_valid = bool(status.valid)
                    trusted = bool(status.trusted)
                    signatures.append({
                        "index": index,
                        "intact": intact,
                        "signature_valid": signature_valid,
                        "trusted": trusted,
                        "bottom_line": bool(status.bottom_line),
                        "coverage": coverage,
                        "accepted": bool(status.bottom_line),
                    })
                except Exception as error:
                    logging.info("PDF signature %s rejected: %s", index, error)
                    signatures.append({
                        "index": index,
                        "intact": False,
                        "signature_valid": False,
                        "trusted": False,
                        "bottom_line": False,
                        "coverage": "UNKNOWN",
                        "accepted": False,
                        "error": "No se pudo validar la firma o la cadena del certificado.",
                    })

            has_full_document_signature = any(
                signature["coverage"] == "ENTIRE_FILE" for signature in signatures
            )
            accepted = (
                bool(signatures)
                and all(signature["accepted"] for signature in signatures)
                and has_full_document_signature
            )
            if not signatures:
                message = "PDF rechazado: no contiene firmas digitales compatibles."
            elif accepted:
                message = "PDF aceptado: sus firmas cubren el documento completo y sus certificados son de confianza."
            elif all(signature["accepted"] for signature in signatures):
                message = "PDF rechazado: ninguna firma cubre la versión completa del documento."
            else:
                message = "PDF rechazado: una firma no es íntegra, el certificado no es de confianza o la firma no cubre el documento completo."
            self.send_json(200, {"valid": accepted, "error": message if not accepted else None, "signatures": signatures})
        except Exception as error:
            logging.info("PDF validation failed: %s", error)
            self.send_json(422, {"error": "No se pudo leer o validar el documento PDF."})

    def log_message(self, format_string, *args):
        logging.info("%s - %s", self.address_string(), format_string % args)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    logging.info("Local PDF certificate validator running at http://localhost:%s", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Stopping local validator.")
    finally:
        server.server_close()
