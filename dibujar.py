import cv2
import numpy as np

drawing = False 
mode = True # si es true, dibuja un rectangulo 
valorx = 5
valory = 5

def draw(event, x,y, label, params):
    global drawing, valorx,valory, mode
    if event == cv2.EVENT_LBUTTONDOWN:   #boton izquierdo del mouse
        drawing= True
        valorx= x
        valory= y
    elif event == cv2.EVENT_MOUSEMOVE:  #mueve el mouse sin tocar ninguna tecla
        if drawing == True:
            if mode == True:
                cv2.rectangle(imagen,(valorx,valory), (x,y), (0,255,0),-1)  #BGR blue-green-red
            else:
                cv2.circle(imagen, (x,y),5 ,(255,0,255),-1)
    elif event == cv2.EVENT_LBUTTONUP: 
        drawing = False
        if mode == True:
            cv2.rectangle(imagen, (valorx,valory),(x,y), (0,255,255),1)
        else:
            cv2.circle(imagen,(x,y),30, (0,0,255),1)
    elif event == cv2.EVENT_LBUTTONDBLCLK:
        cv2.circle(imagen,(x,y), 10 ,(255,0,255),-1)


def capture():
    global imagen
    imagen = np.zeros((500,500,3), np.int8)
    cv2.namedWindow(winname='miDibujo')
    cv2.setMouseCallback('miDibujo', draw)

    while True:
        cv2.imshow('miDibujo', imagen)
        k = cv2.waitKey(1) & 0xFF

        if k == ord('t'):
            mode= not mode
        elif k == 27:
            break


    
    cv2.destroyAllWindows()