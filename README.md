# Alex AI mejorado

Ejecutar recomendado con Python 3.11:

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 alex_gui.py
```

## Comandos principales

- `reproduce Queen`: abre YouTube y reproduce la búsqueda.
- `wikipedia Disney`: muestra el resumen en el cuadro izquierdo y lo lee.
- `busca Netflix`: busca en Google.
- `alarma 09:30`: reproduce `wake_me.mp3` a esa hora. Presioná `T` para detener cuando suene.
- `colores`: abre detector de colores con cámara. Salir con `Q`, `T` o `Esc`.
- `dibujar`: abre lienzo. `M` cambia modo, `C` limpia, `S` guarda, `Q` sale.
- `abre google`: abre una página o app cargada desde los formularios.
- `archivo contrato`: abre un archivo cargado desde los formularios.
- `nota comprar leche`: crea/abre `nota.txt`.
- `mensaje`: envía WhatsApp Web usando contactos guardados.
- `terminar`: pausa el asistente.
- `hasta luego`: cierra la app.

La app escucha una sola frase por click para evitar loops infinitos.
