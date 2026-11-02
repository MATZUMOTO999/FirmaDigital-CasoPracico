# Confianza Digital — HTTPS y firmas

Aplicación educativa en español para estudiar TLS, certificados y validación de documentos. La pestaña **Validar PDF** solo acepta documentos PDF con firma digital íntegra, certificado de confianza y una firma que cubra la versión completa del documento.

## Iniciar en Windows

Se requiere Python 3.10 o posterior.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python server.py
```

Abre <http://localhost:8765>. Para detener el servidor, pulsa `Ctrl+C`. No abras `index.html` directamente: la validación del certificado necesita el servidor local.

## Qué comprueba la validación PDF

- Rechaza archivos que no son PDF, documentos sin firmas digitales compatibles y archivos mayores de 25 MB.
- Comprueba la integridad criptográfica de cada firma y la cadena del certificado contra las CA confiables disponibles para pyHanko en este equipo.
- Rechaza certificados no confiables y documentos donde ninguna firma cubre el archivo completo.
- No descarga certificados ni consulta servicios externos. La revocación en línea OCSP/CRL no se comprueba; una firma aceptada aquí no garantiza que el certificado no haya sido revocado.
- El PDF se procesa en el servidor local enlazado solo a `127.0.0.1`; no se sube a un servicio remoto. No expongas este servidor a una red pública.

Los resultados son una comprobación técnica educativa y no sustituyen una validación legal, una política institucional de confianza ni la revisión en un lector PDF especializado.

## Hoja de ruta

1. **Fundamentos:** confidencialidad con TLS, integridad con hashes y firmas, y autenticación mediante certificados X.509.
2. **Identidad:** diferencia entre un certificado autofirmado para pruebas y uno emitido por una CA confiable. Protege cualquier archivo PFX/PKCS#12 que contenga una clave privada.
3. **HTTPS:** publica el sitio con un certificado válido para el dominio, cadena CA completa y TLS en el puerto 443. La aplicación informa si se abrió con HTTPS, pero no sustituye la inspección del certificado en el navegador.
4. **Documentos firmados:** usa la pestaña **Validar PDF** para comprobar firma, integridad y confianza del certificado. Para Authenticode en ejecutables Windows se necesita un certificado de firma de código y herramientas compatibles como `osslsigncode`.
5. **Evaluación:** prueba un PDF con firma válida y modifica una copia; la copia alterada debe rechazarse. Comprueba también un PDF sin firma y uno con certificado no confiable.

La aplicación conserva herramientas de codificación Base64/URL/hex/binario, hashes SHA-256/384/512 y cifrado de texto AES-256-GCM.
