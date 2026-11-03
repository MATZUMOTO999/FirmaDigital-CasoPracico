# Confianza Digital — HTTPS local

Aplicación educativa en español para estudiar HTTPS y validación local de documentos PDF sin exigir firma digital.

## Iniciar en Windows

Se requiere Python 3.10 o posterior.

En PowerShell, primero cambia a la carpeta donde está el proyecto. Por ejemplo:

```powershell
Set-Location "C:\FirmaDigital-CasoPracico"
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python server.py
```

Si guardaste el proyecto en otra carpeta, reemplaza la ruta de `Set-Location`. Después abre <http://localhost:8765>. Para detener el servidor, pulsa `Ctrl+C`.

## Qué comprueba la validación PDF

- Rechaza archivos que no son PDF o que superan 25 MB.
- Comprueba que la cabecera del documento comienza por `%PDF-`.
- No exige firma digital ni certificados X.509.
- Procesa todo localmente en el equipo y no consulta servicios externos.

La validación se limita a verificar que el archivo es un PDF válido para la demo y no sustituye ninguna comprobación legal ni técnica de firma digital real.

## Hoja de ruta

1. **HTTPS:** revisa si la página se sirve por `https://` y observa el comportamiento del navegador con los certificados del sitio.
2. **Documentos PDF:** usa la pestaña **Validar PDF** para aceptar archivos PDF con una cabecera válida sin requerir firma digital.
3. **Criptografía práctica:** sigue explorando las herramientas de codificación Base64/URL/hex/binario, hashes SHA-256/384/512 y cifrado AES-256-GCM.

La aplicación conserva herramientas útiles para trabajar con texto y hashes, pero la validación de PDF queda orientada a una comprobación local simple y sin firma digital.
