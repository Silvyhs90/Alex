"""Lienzo simple para dibujar con el mouse.
Controles:
- Click y arrastrar: dibujar
- M: cambiar entre pincel y rectángulo
- C: limpiar
- S: guardar dibujo
- Q o Esc: salir
"""

import datetime
import cv2
import numpy as np

painting = False
start_x = 0
start_y = 0
mode = "brush"
canvas = None
preview = None


def mouse_callback(event, x, y, flags, param):
    global painting, start_x, start_y, canvas, preview

    if event == cv2.EVENT_LBUTTONDOWN:
        painting = True
        start_x, start_y = x, y
        preview = canvas.copy()

    elif event == cv2.EVENT_MOUSEMOVE and painting:
        if mode == "brush":
            cv2.circle(canvas, (x, y), 6, (255, 0, 255), -1)
        else:
            preview = canvas.copy()
            cv2.rectangle(preview, (start_x, start_y), (x, y), (0, 255, 255), 2)

    elif event == cv2.EVENT_LBUTTONUP:
        painting = False
        if mode == "rectangle":
            cv2.rectangle(canvas, (start_x, start_y), (x, y), (0, 255, 255), 2)
        preview = canvas.copy()


def capture():
    global canvas, preview, mode

    canvas = np.full((600, 800, 3), 255, dtype=np.uint8)
    preview = canvas.copy()

    window_name = "Alex Draw"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)

    while True:
        shown = preview.copy() if mode == "rectangle" and painting else canvas.copy()
        cv2.putText(shown, f"Modo: {mode} | M cambia | C limpia | S guarda | Q sale", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.imshow(window_name, shown)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord("m"):
            mode = "rectangle" if mode == "brush" else "brush"
        elif key == ord("c"):
            canvas[:] = 255
            preview = canvas.copy()
        elif key == ord("s"):
            filename = "dibujo_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
            cv2.imwrite(filename, canvas)
            print("Dibujo guardado:", filename)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    capture()
