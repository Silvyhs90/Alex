import speech_recognition as sr
import subprocess as sub
import pyttsx3
import pywhatkit
import wikipedia
import datetime
import keyboard
import colors
import os
from tkinter import *
from PIL import Image, ImageTk
from pygame import mixer
import threading as tr
import whats as wp
import dibujar as draw

# Interfaz ventana raiz imagen, botones, texto#
main_window = Tk()
main_window.title("Alex AI")

main_window.geometry("1000x680")
main_window.resizable(0,0)
main_window.configure(background='#B9B3E7')
main_window.iconbitmap('alex_ico.ico')

##Canvas
commands = """
        Comandos: Esperar que diga "Dime"
        -Reproduce.. (ej:Queen)
        -Wikipedia.. (ej:Disney)
        -Busca.. (ej: Netflix)
        -Alarma.. (decir 9y30 o 21y30)
        -Colores (se sale con la t)
        -Dibujar (se sale con la t)
        -Abre (pagina o programa windows cargado)
        -Abrir Archivo (nombre)
        -Nota (crea un txt)
        -Mensaje (Manda un Whatsapp)
        -Terminar
        -Hasta luego
"""
#etiquetas, canvas, foto del asistente#
label_title = Label(main_window, text="Alex AI", background='#7F7FD5', fg='#C6FFDD',
                    font=('Roboto', 30, 'bold'))
label_title.pack(pady=10)

canvas_commands = Canvas(bg="#86A8E7", height=200, width=260)
canvas_commands.place(x=0, y=0)
canvas_commands.create_text(120,105, text= commands, fill="black", font="Roboto 8 bold") #anchoxlargo

text_info = Text(main_window, bg="#86A8E7", fg="black")
text_info.place(x=2, y=215, height=380, width=260)
text_info.focus()

alex_photo = ImageTk.PhotoImage(Image.open("alex_photo.png"))
window_photo = Label(main_window, image=alex_photo)
window_photo.pack(pady=8)

#Codigo Alex#
name = "alex"
listener = sr.Recognizer() #Asigno el objeto Recognizer a listener 
engine = pyttsx3.init()  #voz del asistente que se haya instalado en la maquina, texto a voz. 

voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 145)

def charge_data(name_dict, name_file):  ##nombre del diccionario, y el nombre del archivo .txt
    try:
        with open(name_file) as f:
            for line in f:
                (key, val) = line.split(",")
                val = val.rstrip("\n")
                name_dict[key] = val
    except FileNotFoundError as e:
        pass

#diccionario, estructura de datos, clave/valor#
sites = dict()
charge_data(sites, "paginas.txt")
files = dict()
charge_data(files, "archivos.txt")
programs = dict()
charge_data(programs, "apps.txt")
contacts = dict()
charge_data(contacts, "contacts.txt")


def talk(text):
    engine.say(text)
    engine.runAndWait()

##
def read_and_talk():
    text = text_info.get("1.0", "end") #obtener todo el texto de principio a fin#
    talk(text)

def delete_text(): #borrar texto
    text_info.delete(1.0, END)

def write_text(text_wikipedia): #escribe lo que lee de wikipedia 
    text_info.insert(INSERT,text_wikipedia)


def listen():
    listener = sr.Recognizer() #Asigna el objeto a la variable listener
    with sr.Microphone() as source:
        listener.adjust_for_ambient_noise(source)
        talk("Dime..")
        pc = listener.listen(source)  # microfono de la pc#
    try:
        rec = listener.recognize_google(pc, language='es-ES')
        rec = rec.lower()
    except sr.UnknownValueError: #
        print("No te entendí, por favor, intenta de nuevo")
    except sr.RequestError as e: #error del recognize de google
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
    return rec


#funciones asociadas a las palabras claves
def reproduce(rec):
    # reemplaza reproduce por un string vacio con la funcion replace#
    music = rec.replace('reproduce', '')
    #print("Reproduciendo" + music)
    talk("Reproduciendo" + music)
    pywhatkit.playonyt(music)

def googlea(rec):
    g = rec.replace('busca', '')
    #print("Buscando en google..")
    talk("Abriendo google..." + g)
    pywhatkit.search(g)

def busca(rec):
    search = rec.replace('wikipedia', '')
    wikipedia.set_lang("es")
    wiki = wikipedia.summary(search, 1)
    talk(wiki)
    write_text(search + ": " + wiki)

def thread_alarma(rec):
    #se usan hilos para poder usar otros procesos mientras la alarma espera para sonar
    alarm = tr.Thread(target=clock, args=(rec,))
    alarm.start()

def colores(rec):
    talk("Abriendo camara")
    t = tr.Thread(target=colors.capture)
    t.start()

def dibujar(rec):
    talk("Abriendo lienzo")
    t = tr.Thread(target=draw.capture)
    t.start()
    
def abre(rec):
    task = rec.replace('abre', '').strip() #se reemplaza la palabra abre por string vacio para tener la app que quiera abrir y strip cortar espacio vacio al inicio
    print(task) #sin el strip() la palabra buscada empieza con un espacio y no la deja abrir
    if task in sites:
        for task in sites:
            if task in rec:
                sub.call(f'start chrome.exe {sites[task]}',shell=True)
                talk(f'Abriendo {task}')
    elif task in programs:
        for task in programs:
            if task in rec:
                talk(f'Abriendo {task}')
                sub.Popen(programs[task])
    else:
        talk("Perdona, aún no agregaste esa app o página web. Agregala con el botón de Agregar Página web o agregar app")

def archivo(rec):
    file = rec.replace('abrir archivo', '').strip()
    if file in files:
        for file in files:
            if file in rec:
                sub.Popen([files[file]], shell=True)
                talk(f'Abriendo {file}')
    else:
        talk("Perdona,aún no agregaste ese archivo. Agregalo con el botón Agregar Archivo")

def escribe(rec):
    try:
        with open("nota.txt", 'a') as f:
            write(f)
            
    except FileNotFoundError as e:
        file = open("nota.txt", 'w')
        write(file)


#alarma
def clock(rec):
    num = rec.replace('alarma', '')
    num = num.strip()
    talk("Alarma activada a las  " + num + " horas")
    if num[0] != '0' and len(num) < 5:  
        num = '0' + num #ejemplo 09:30, le agrega el 0
    #print(num)
    while True:
        if datetime.datetime.now().strftime('%H:%M') == num:
            #print("HORA DE DESPERTARSE!!")
            mixer.init()  # pygame#
            mixer.music.load('wake_me.mp3')
            mixer.music.play()
        else:
            continue
        if keyboard.read_key() == "t":
            mixer.music.stop()
            break

#enviar mensaje whatsapp
def enviar_mensaje(rec):
    talk("¿A quién quieres enviar el mensaje?")
    contact = listen()
    contact = contact.strip()

    if contact in contacts:
        for cont in contacts:
            if cont == contact:
                contact = contacts[cont]  #acceder al valor de la clave, su num celular
                talk("¿Qué quieres que diga?")
                message = listen()
                talk("Enviando mensaje...")
                wp.send_message(contact, message)
    else:
        talk("Aún no has agregado a ese contacto, usa el botón de agregar contacto")


def cerrar(rec):
    for task in programs:
        if task in programs:
            kill_task = programs[task].split('\\') #lista
            kill_task = kill_task[-1] #ultimo elemento de la lista, empieza desde 0
            if task in rec:
                sub.call(f'TASKKILL /IM {kill_task} /F', shell=True)  #la F es forzar
                talk(f'Cerrando {task}')
            if 'todo' in rec:
                sub.call(f'TASKKILL /IM {kill_task} /F', shell=True)  #la F es forzar
                talk(f'Cerrando {task}')
    if 'hasta luego' in rec:
        talk("¡¡Nos vemos!!")
        sub.call(f'TASKKILL /IM alex_gui.exe /F', shell=True)


#diccionario
key_words = {
    #clave        valor
    'reproduce': reproduce,
    'busca':googlea,
    'wikipedia': busca,
    'alarma': thread_alarma,
    'colores':colores,
    'dibujar':dibujar,
    'abre':abre,
    'abrir archivo':archivo,
    'nota':escribe,
    'mensaje':enviar_mensaje,
    'hasta luego':cerrar
}

#inicio de la app 
def run_alex():
    while True:
        try:
            rec = listen()
        except UnboundLocalError:
            talk("No te puedo entender, intenta de nuevo")
            continue            
        if 'busca' in rec:
            key_words['busca'](rec) #valor de esta clave
            break
        elif 'googlear' in rec:
            key_words['googlear'](rec) #valor de esta clave
            break
        else:
            for word in key_words:
                if word in rec:
                    key_words[word](rec)
        if 'terminar' in rec:
            talk("ok")
            break

    main_window.update() # ventana se refresque

#metodo escribir en la nota
def write(f):
    talk("¿Qué quieres que escriba en la nota?")
    rec_write = listen()
    f.write(rec_write + os.linesep)
    f.close()
    talk("Nota creada, puedes verla")
    sub.Popen("nota.txt", shell=True)

#metodo de cargar archivos, paginas, apps
def open_files():
    global namefile_entry, pathf_entry
    window_files = Toplevel()
    window_files.title("Agregar Archivos")
    window_files.configure(bg="#b20a2c")
    window_files.geometry("400x200")
    window_files.resizable(0,0)
    main_window.eval(f'tk::PlaceWindow {str(window_files)} center')
    title_label = Label(window_files, text="Agrega un archivo", fg="white", bg="#b20a2c", font=('Arial', 15, 'bold'))
    title_label.pack(pady=3)
    
    name_label = Label(window_files, text="Nombre del archivo", fg="white", bg="#b20a2c", font=('Arial', 10, 'bold'))
    name_label.pack(pady=2)
    namefile_entry = Entry(window_files)
    namefile_entry.pack(pady=1)
    
    path_label = Label(window_files, text="Ruta del archivo", fg="white", bg="#b20a2c", font=('Arial', 10, 'bold'))
    path_label.pack(pady=2)

    path_label = Label(window_files, text="C: \ Users\ PC\ Pictures\ Wallpapers\ descarga.jpg", fg="white", bg="#b20a2c", font=('Arial', 10, 'bold'))
    path_label.pack(pady=2)

    pathf_entry = Entry(window_files, width=40)
    pathf_entry.pack(pady=1)

    save_button = Button(window_files, text="Guardar", fg="black",bg="#fffbd5", width=8, height=1, command=add_files)
    save_button.pack(pady=4)

def open_apps():
    global nameapp_entry, patha_entry
    window_apps = Toplevel()
    window_apps.title("Agregar Apps")
    window_apps.configure(bg="#b20a2c")
    window_apps.geometry("400x200")
    window_apps.resizable(0,0)
    main_window.eval(f'tk::PlaceWindow {str(window_apps)} center')

    title_label = Label(window_apps, text="Agrega una app", fg="white", bg="#b20a2c", font=('Arial', 15, 'bold'))
    title_label.pack(pady=3)
    name_label = Label(window_apps, text="Nombre de la App", fg="white", bg="#b20a2c", font=('Arial', 10, 'bold'))
    name_label.pack(pady=2)
    
    nameapp_entry = Entry(window_apps)
    nameapp_entry.pack(pady=1)
    
    path_label = Label(window_apps, text="Ruta del archivo", fg="white", bg="#b20a2c", font=('Arial', 10, 'bold'))
    path_label.pack(pady=2)
    path_label = Label(window_apps, text="Ej: C:\ Program Files\ iTunes\ iTunes.exe", fg="white", bg="#b20a2c", font=('Arial', 10, 'bold'))
    path_label.pack(pady=2)
    patha_entry = Entry(window_apps, width=40)
    patha_entry.pack(pady=1)

    save_button = Button(window_apps, text="Guardar", bg="#fffbd5", width=8, height=1, command=add_apps)
    save_button.pack(pady=4)

def open_pages():
    global namepages_entry, pathp_entry
    window_pages = Toplevel()
    window_pages.title("Agregar Apps")
    window_pages.configure(bg="#b20a2c")
    window_pages.geometry("400x200")
    window_pages.resizable(0,0)
    main_window.eval(f'tk::PlaceWindow {str(window_pages)} center')

    title_label = Label(window_pages, text="Agrega una página Web", fg="white", bg="#b20a2c", font=('Arial', 15, 'bold'))
    title_label.pack(pady=3)
    name_label = Label(window_pages, text="Nombre de la página", fg="white", bg="#b20a2c", font=('Arial', 10, 'bold'))
    name_label.pack(pady=2)
    
    namepages_entry = Entry(window_pages)
    namepages_entry.pack(pady=1)
    
    path_label = Label(window_pages, text="URL de la página Ej:www.google.com ", fg="white", bg="#b20a2c", font=('Arial', 10, 'bold'))
    path_label.pack(pady=2)
    
    pathp_entry = Entry(window_pages, width=40)
    pathp_entry.pack(pady=1)

    save_button = Button(window_pages, text="Guardar", bg="#fffbd5", width=8, height=1, command=add_pages)
    save_button.pack(pady=4)

    #abrir contactos
def open_contacts():
    global namecontact_entry , phonecontact_entry
    window_contacts = Toplevel()
    window_contacts.title("Agregar un contacto")
    window_contacts.configure(bg="#b20a2c")
    window_contacts.geometry("400x200")
    window_contacts.resizable(0,0)
    main_window.eval(f'tk::PlaceWindow {str(window_contacts)} center')

    title_label = Label(window_contacts, text="Agrega un contacto",
                        fg="white", bg="#b20a2c", font=('Arial', 15, "bold"))
    title_label.pack(pady=3)
    name_label = Label(window_contacts, text="Nombre del contacto",
                        fg="white", bg="#b20a2c", font=("Arial",10, "bold"))
    name_label.pack(pady=2)

    namecontact_entry = Entry(window_contacts)
    namecontact_entry.pack(pady=1)

    phone_label = Label(window_contacts, text="Telefono (con código de área Ej:+5491158226978)",
                        fg="white", bg="#b20a2c", font=("Arial",10, "bold"))
    phone_label.pack(pady=2)

    phonecontact_entry = Entry(window_contacts, width=35)
    phonecontact_entry.pack(pady=1)

    save_button = Button(window_contacts, text="Guardar", bg="#fffbd5",
                            fg="black",width=8, height=1, command=add_contacts)
    save_button.pack(pady=4)

def save_data(key, value, file_name):
    try:
        with open(file_name, 'a') as f:
            f.write(key + "," + value + "\n")
    except FileNotFoundError():
        file = open(file_name, 'a')
        file.write(key + "," + value + "\n")

def add_files(): #guardar en los diccionarios
    name_file = namefile_entry.get().strip()
    path_file = pathf_entry.get().strip()
    
    files[name_file] = path_file
    save_data(name_file, path_file, "archivos.txt")
    namefile_entry.delete(0, "end") #borre de inicio a fin la cajita de texto
    pathf_entry.delete(0, "end")
def add_apps():
    name_file = nameapp_entry.get().strip()
    path_file = patha_entry.get().strip()
    
    programs[name_file] = path_file
    save_data(name_file, path_file, "apps.txt")
    nameapp_entry.delete(0, "end") #borre de inicio a fin la cajita de texto
    patha_entry.delete(0, "end")
def add_pages():
    name_page = namepages_entry.get().strip()
    url_pages = pathp_entry.get().strip()
    
    sites[name_page] = url_pages
    save_data(name_page, url_pages, "paginas.txt")
    namepages_entry.delete(0, "end") #borre de inicio a fin la cajita de texto
    pathp_entry.delete(0, "end")

def add_contacts():
    name_contact = namecontact_entry.get().strip()
    phone_contact = phonecontact_entry.get().strip()

    contacts[name_contact] = phone_contact
    save_data(name_contact, phone_contact, "contacts.txt")
    namecontact_entry.delete(0, "end")
    phonecontact_entry.delete(0, "end")

#Leer BOTONES
def talk_pages():
    if bool(sites) == True:
        talk("Has agregado las siguientes páginas web")
        for site in sites:
            talk(site)
    else:
        talk("Aún no agregaste páginas web")
def talk_apps():
    if bool(programs) == True:
        talk("Has agregado las siguientes apps")
        for program in programs:
            talk(program)
    else:
        talk("Aún no agregaste apps")
def talk_files():
    if bool(files) == True:
        talk("Has agregado los siguientes archivos")
        for file in files:
            talk(file)
    else:
        talk("Aún no agregaste archivos")
#contactos leer
def talk_contacts():
    if bool(contacts) == True:
        talk("Has agregado los siguientes contactos")
        for cont in contacts:
            talk(cont)
    else:
        talk("Aún no has agregado contactos!")

def give_name():
    talk("Hola, ¿Cómo te llamas?, Mi nombre es Alex")
    name = listen()
    name = name.strip()
    talk(f"Bienvenido/a {name}")

    try:
        with open("name.txt", 'w') as f:
            f.write(name)
    except FileNotFoundError:
        file = open("name.txt", 'w')
        file.write(name)

def hello():
    
        if os.path.exists("name.txt"):
            with open("name.txt") as f:
             for name in f:
                talk(f"Hola, bienvenido {name}")
        else:
            give_name()
   

def thread_hello(): #convertir una funcion en un hilo 
    t = tr.Thread(target=hello)
    t.start()


thread_hello()


#BOTONES
#boton escuchar
button_listen = Button(main_window, text="Escuchar", fg="#eaafc8", bg="#240b36",
                        font=("Arial", 15, "bold"),width=30, height=1, command=run_alex)
button_listen.pack(side=BOTTOM, pady=10)
#boton hablar 
button_speak = Button(main_window, text="Hablar", fg="white", bg="#00B4DB",
                        font=("Arial", 8, "bold"), command=read_and_talk) 
button_speak.place(x=100, y=600, width=50, height=35)
#boton borrar
button_speak = Button(main_window, text="Limpiar", fg="white", bg="#00B4DB",
                        font=("Arial", 8, "bold"), command=delete_text) 
button_speak.place(x=10, y=600, width=50, height=35)
#boton agregar archivos, paginas, apps, contactos
button_add_files = Button(main_window, text="Agregar archivos", fg="white", bg="#7F7CF6",
                        font=("Arial", 10, "bold"), command=open_files) 
button_add_files.place(x=800, y=100, width=120, height=30)

button_add_apps = Button(main_window, text="Agregar apps", fg="white", bg="#7F7CF6", 
                        font=("Arial", 10, "bold"), command=open_apps) 
button_add_apps.place(x=800, y=140, width=120, height=30)

button_add_pages = Button(main_window, text="Agregar páginas", fg="white", bg="#7F7CF6",
                        font=("Arial", 10, "bold"), command=open_pages) 
button_add_pages.place(x=800, y=180, width=120, height=30)

button_add_contacts = Button(main_window, text="Agregar contactos", fg="white", bg="#7F7CF6",
                        font=("Arial", 10, "bold"), command=open_contacts) 
button_add_contacts.place(x=800, y=220, width=140, height=35)

#botones paginas/apps/archivos que agregue
button_tell_pages = Button(main_window, text="Páginas agregadas", fg="white", bg="#c060a0",
                        font=("Arial", 10, "bold"), command=talk_pages) 
button_tell_pages.place(x=800, y=340, width=140, height=35)

button_tell_apps = Button(main_window, text="Apps agregadas", fg="white", bg="#c060a0",
                        font=("Arial", 10, "bold"), command=talk_apps) 
button_tell_apps.place(x=800, y=380, width=130, height=35)

button_tell_files = Button(main_window, text="Archivos agregados", fg="white", bg="#c060a0",
                        font=("Arial", 10, "bold"), command=talk_files) 
button_tell_files.place(x=800, y=420, width=140, height=35)

button_leer_contacts = Button(main_window, text="Contactos agregados", fg="white", bg="#c060a0",
                        font=("Arial", 10, "bold"), command=talk_contacts) 
button_leer_contacts.place(x=800, y=460, width=140, height=35)

main_window.mainloop()