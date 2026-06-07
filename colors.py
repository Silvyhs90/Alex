"""Detector simple de colores con OpenCV.
Presioná Q o T para salir.
"""

import cv2
import numpy as np

COLOR_RANGES = {
    "Rojo": [((0, 100, 80), (10, 255, 255)), ((170, 100, 80), (180, 255, 255))],
    "Amarillo": [((20, 100, 100), (35, 255, 255))],
    "Verde": [((40, 70, 70), (85, 255, 255))],
    "Azul": [((90, 80, 70), (130, 255, 255))],
    "Negro": [((0, 0, 0), (180, 255, 55))],
    "Blanco": [((0, 0, 200), (180, 45, 255))],
}

DRAW_COLORS = {
    "Rojo": (0, 0, 255),
    "Amarillo": (0, 255, 255),
    "Verde": (0, 255, 0),
    "Azul": (255, 0, 0),
    "Negro": (0, 0, 0),
    "Blanco": (255, 255, 255),
}


def build_mask(hsv_frame, ranges):
    mask_total = None
    for lower, upper in ranges:
        mask = cv2.inRange(hsv_frame, np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))
        mask_total = mask if mask_total is None else cv2.add(mask_total, mask)
    kernel = np.ones((5, 5), np.uint8)
    mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)
    mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)
    return mask_total


def draw_color(frame, mask, name):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    color = DRAW_COLORS[name]

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 1200:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, name, (x, max(25, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)


def capture():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("No se pudo abrir la cámara.")
        return

    cv2.namedWindow("Detector de colores")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        for name, ranges in COLOR_RANGES.items():
            mask = build_mask(hsv, ranges)
            draw_color(frame, mask, name)

        cv2.putText(frame, "Q/T: salir", (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow("Detector de colores", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("t"), 27):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    capture()
