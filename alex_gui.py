import speech_recognition as sr
import subprocess as sub
import pyttsx3
import pywhatkit
import wikipedia
import datetime
import keyboard
import colors
from tkinter import *
from PIL import Image, ImageTk
from pygame import mixer
import threading as tr
import whats as wp
import dibujar as draw

# Interfaz ventana import json
import json
import os

# -----------------------------------
# Gestión del nombre del usuario
# -----------------------------------

CONFIG_FILE = "config.json"

def load_user_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_user_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_name():
    config = load_user_config()
    if "user_name" in config and config["user_name"].strip() != "":
        return config["user_name"]

    print("¡Hola! No tengo registrado tu nombre.")
    user_name = input("¿Cómo te llamás?: ").strip()

    config["user_name"] = user_name
    save_user_config(config)

    return user_name

# -----------------------------------
# Ventana principal
# -----------------------------------

main_window = Tk()
main_window.title("Alex AI")

main_window.geometry("1000x680")
main_window.resizable(0,0)
main_window.configure(background='#B9B3E7')
main_window.iconbitmap('alex_ico.ico')

## Canvas de comandos
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

label_title = Label(main_window, text="Alex AI", background='#7F7FD5', fg='#C6FFDD',
                    font=('Roboto', 30, 'bold'))
label_title.pack(pady=10)

canvas_commands = Canvas(bg="#86A8E7", height=200, width=260)
canvas_commands.place(x=0, y=0)
canvas_commands.create_text(120,105, text=commands, fill="black", font="Roboto 8 bold")

text_info = Text(main_window, bg="#86A8E7", fg="black")
text_info.place(x=2, y=215, height=380, width=260)
text_info.focus()

alex_photo = ImageTk.PhotoImage(Image.open("alex_photo.png"))
window_photo = Label(main_window, image=alex_photo)
window_photo.pack(pady=8)

# -----------------------------------
# Inicialización de voz
# -----------------------------------

name = "alex"
listener = sr.Recognizer()
engine = pyttsx3.init()

voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 145)

def charge_data(name_dict, name_file):
    try:
        with open(name_file) as f:
            for line in f:
                (key, val) = line.split(",")
                val = val.rstrip("\n")
                name_dict[key] = val
    except FileNotFoundError:
        pass

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

def read_and_talk():
    text = text_info.get("1.0", "end")
    talk(text)

def delete_text():
    text_info.delete(1.0, END)

def write_text(text_wikipedia):
    text_info.insert(INSERT,text_wikipedia)

# -----------------------------------
# Escuchar micrófono
# -----------------------------------

def listen():
    listener = sr.Recognizer()
    with sr.Microphone() as source:
        listener.adjust_for_ambient_noise(source)
        talk("Dime..")
        pc = listener.listen(source)
    try:
        rec = listener.recognize_google(pc, language='es-ES')
        rec = rec.lower()
    except:
        rec = ""
    return rec

# -----------------------------------
# Funciones por comandos
# -----------------------------------

def reproduce(rec):
    music = rec.replace('reproduce', '')
    talk("Reproduciendo" + music)
    pywhatkit.playonyt(music)

def googlea(rec):
    g = rec.replace('busca', '')
    talk("Abriendo google..." + g)
    pywhatkit.search(g)

def busca(rec):
    search = rec.replace('wikipedia', '')
    wikipedia.set_lang("es")
    wiki = wikipedia.summary(search, 1)
    talk(wiki)
    write_text(search + ": " + wiki)

def thread_alarma(rec):
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
    task = rec.replace('abre', '').strip()
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
        talk("Perdona, aún no agregaste esa app o página web.")

def archivo(rec):
    file = rec.replace('abrir archivo', '').strip()
    if file in files:
        for file in files:
            if file in rec:
                sub.Popen([files[file]], shell=True)
                talk(f'Abriendo {file}')
    else:
        talk("Ese archivo no está agregado.")

def escribe(rec):
    try:
        with open("nota.txt", 'a') as f:
            write(f)
    except FileNotFoundError:
        file = open("nota.txt", 'w')
        write(file)

def clock(rec):
    num = rec.replace('alarma', '').strip()
    talk("Alarma activada a las " + num + " horas")

    if num[0] != '0' and len(num) < 5:
        num = '0' + num

    while True:
        if datetime.datetime.now().strftime('%H:%M') == num:
            mixer.init()
            mixer.music.load('wake_me.mp3')
            mixer.music.play()
        else:
            continue
        if keyboard.read_key() == "t":
            mixer.music.stop()
            break

def enviar_mensaje(rec):
    talk("¿A quién quieres enviar el mensaje?")
    contact = listen().strip()

    if contact in contacts:
        talk("¿Qué quieres que diga?")
        message = listen()
        talk("Enviando mensaje...")
        wp.send_message(contacts[contact], message)
    else:
        talk("Ese contacto no está agregado.")

def cerrar(rec):
    for task in programs:
        if task in programs:
            kill_task = programs[task].split('\\')
            kill_task = kill_task[-1]
            if task in rec:
                sub.call(f'TASKKILL /IM {kill_task} /F', shell=True)
                talk(f'Cerrando {task}')
            if 'todo' in rec:
                sub.call(f'TASKKILL /IM {kill_task} /F', shell=True)
                talk(f'Cerrando {task}')
    if 'hasta luego' in rec:
        talk("Nos vemos!!")
        sub.call(f'TASKKILL /IM alex_gui.exe /F', shell=True)

# -----------------------------------
# Diccionario de comandos
# -----------------------------------

key_words = {
    'reproduce': reproduce,
    'busca': googlea,
    'wikipedia': busca,
    'alarma': thread_alarma,
    'colores': colores,
    'dibujar': dibujar,
    'abre': abre,
    'abrir archivo': archivo,
    'nota': escribe,
    'mensaje': enviar_mensaje,
    'hasta luego': cerrar
}

# -----------------------------------
# Ciclo principal del asistente
# -----------------------------------

def run_alex():
    while True:
        try:
            rec = listen()
        except UnboundLocalError:
            talk("No te puedo entender, intenta de nuevo")
            continue

        if 'busca' in rec:
            key_words['busca'](rec)
            break
        else:
            for word in key_words:
                if word in rec:
                    key_words[word](rec)

        if 'terminar' in rec:
            talk("ok")
            break

    main_window.update()

# -----------------------------------
# Escribir nota
# -----------------------------------

def write(f):
    talk("¿Qué quieres que escriba en la nota?")
    rec_write = listen()
    f.write(rec_write + os.linesep)
    f.close()
    talk("Nota creada, puedes verla")
    sub.Popen("nota.txt", shell=True)

# -----------------------------------
# Ventanas para agregar datos
# -----------------------------------

def open_files():
    global filename_entry, filepath_entry
    window_files = Toplevel()
    window_files.title("Agregar Archivos")
    window_files.configure(bg="#b20a2c")
    window_files.geometry("400x200")
    main_window.eval(f'tk::PlaceWindow {str(window_files)} center')

    Label(window_files, text="Agrega un archivo", fg="white", bg="#b20a2c", font=('Arial', 15, 'bold')).pack(pady=3)
    Label(window_files, text="Nombre del archivo", fg="white", bg="#b20a2c").pack()

    filename_entry = Entry(window_files)
    filename_entry.pack()

    Label(window_files, text="Ruta del archivo", fg="white", bg="#b20a2c").pack()
    filepath_entry = Entry(window_files, width=40)
    filepath_entry.pack()

    Button(window_files, text="Guardar", command=add_files).pack(pady=4)

def open_apps():
    global appname_entry, apppath_entry
    window_apps = Toplevel()
    window_apps.title("Agregar Apps")
    window_apps.configure(bg="#b20a2c")
    window_apps.geometry("400x200")
    main_window.eval(f'tk::PlaceWindow {str(window_apps)} center')

    Label(window_apps, text="Agrega una app", fg="white", bg="#b20a2c", font=('Arial', 15, 'bold')).pack(pady=3)
    Label(window_apps, text="Nombre de la App", fg="white", bg="#b20a2c").pack()

    appname_entry = Entry(window_apps)
    appname_entry.pack()

    Label(window_apps, text="Ruta del archivo", fg="white", bg="#b20a2c").pack()
    apppath_entry = Entry(window_apps, width=40)
    apppath_entry.pack()

    Button(window_apps, text="Guardar", command=add_apps).pack(pady=4)

def open_pages():
    global pagename_entry, pageurl_entry
    window_pages = Toplevel()
    window_pages.title("Agregar Página Web")
    window_pages.configure(bg="#b20a2c")
    window_pages.geometry("400x200")
    main_window.eval(f'tk::PlaceWindow {str(window_pages)} center')

    Label(window_pages, text="Agrega una página Web", fg="white", bg="#b20a2c", font=('Arial', 15, 'bold')).pack(pady=3)
    Label(window_pages, text="Nombre de la página", fg="white", bg="#b20a2c").pack()

    pagename_entry = Entry(window_pages)
    pagename_entry.pack()

    Label(window_pages, text="URL (Ej: www.google.com)", fg="white", bg="#b20a2c").pack()

    pageurl_entry = Entry(window_pages, width=40)
    pageurl_entry.pack()

    Button(window_pages, text="Guardar", command=add_pages).pack(pady=4)

def open_contacts():
    global namecontact_entry, phonecontact_entry
    window_contacts = Toplevel()
    window_contacts.title("Agregar un contacto")
    window_contacts.configure(bg="#b20a2c")
    window_contacts.geometry("400x200")
    main_window.eval(f'tk::PlaceWindow {str(window_contacts)} center')

    Label(window_contacts, text="Agrega un contacto", fg="white", bg="#b20a2c", font=('Arial', 15, "bold")).pack(pady=3)
    Label(window_contacts, text="Nombre del contacto", fg="white", bg="#b20a2c").pack()

    namecontact_entry = Entry(window_contacts)
    namecontact_entry.pack()

    Label(window_contacts, text="Telefono (+549...)", fg="white", bg="#b20a2c").pack()
    phonecontact_entry = Entry(window_contacts, width=35)
    phonecontact_entry.pack()

    Button(window_contacts, text="Guardar", command=add_contacts).pack(pady=4)

# -----------------------------------
# Guardado de datos
# -----------------------------------

def save_data(key, value, file_name):
    try:
        with open(file_name, 'a') as f:
            f.write(key + "," + value + "\n")
    except:
        file = open(file_name, 'a')
        file.write(key + "," + value + "\n")

def add_files():
    file_name = filename_entry.get().strip()
    file_path = filepath_entry.get().strip()
    files[file_name] = file_path
    save_data(file_name, file_path, "archivos.txt")
    filename_entry.delete(0, "end")
    filepath_entry.delete(0, "end")

def add_apps():
    app_name = appname_entry.get().strip()
    app_path = apppath_entry.get().strip()
    programs[app_name] = app_path
    save_data(app_name, app_path, "apps.txt")
    appname_entry.delete(0, "end")
    apppath_entry.delete(0, "end")

def add_pages():
    page_name = pagename_entry.get().strip()
    page_url = pageurl_entry.get().strip()
    sites[page_name] = page_url
    save_data(page_name, page_url, "paginas.txt")
    pagename_entry.delete(0, "end")
    pageurl_entry.delete(0, "end")

def add_contacts():
    name_contact = namecontact_entry.get().strip()
    phone_contact = phonecontact_entry.get().strip()
    contacts[name_contact] = phone_contact
    save_data(name_contact, phone_contact, "contacts.txt")
    namecontact_entry.delete(0, "end")
    phonecontact_entry.delete(0, "end")

###################################################################
# Aquí empiezan los botones, etc.
###################################################################

# CAMPOS PARA ARCHIVOS
# -------------------------
tk.Label(window, text="Nombre del archivo:").pack()
filename_entry = tk.Entry(window)
filename_entry.pack()

tk.Label(window, text="Ruta del archivo:").pack()
filepath_entry = tk.Entry(window)
filepath_entry.pack()

files_button = tk.Button(window, text="Agregar archivo", command=add_files)
files_button.pack(pady=5)

# -------------------------
# CAMPOS PARA APLICACIONES
# -------------------------
tk.Label(window, text="Nombre de la aplicación:").pack()
appname_entry = tk.Entry(window)
appname_entry.pack()

tk.Label(window, text="Ruta de la aplicación:").pack()
apppath_entry = tk.Entry(window)
apppath_entry.pack()

apps_button = tk.Button(window, text="Agregar aplicación", command=add_apps)
apps_button.pack(pady=5)

CAMPOS PARA PÁGINAS
# -------------------------
tk.Label(window, text="Nombre de la página:").pack()
pagename_entry = tk.Entry(window)
pagename_entry.pack()

tk.Label(window, text="URL de la página:").pack()
pageurl_entry = tk.Entry(window)
pageurl_entry.pack()

pages_button = tk.Button(window, text="Agregar página", command=add_pages)
pages_button.pack(pady=5)

# -------------------------
# CAMPOS PARA CONTACTOS
# -------------------------
tk.Label(window, text="Nombre del contacto:").pack()
namecontact_entry = tk.Entry(window)
namecontact_entry.pack()

tk.Label(window, text="Teléfono del contacto:").pack()
phonecontact_entry = tk.Entry(window)
phonecontact_entry.pack()

contacts_button = tk.Button(window, text="Agregar contacto", command=add_contacts)
contacts_button.pack(pady=5)

window.mainloop()
