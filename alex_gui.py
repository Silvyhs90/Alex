import datetime
import difflib
import json
import os
import re
import sys
import base64
import subprocess as sub
import threading as tr
import time
import unicodedata
import webbrowser
from urllib.parse import quote

import keyboard
import pyttsx3
import pywhatkit
import speech_recognition as sr
import tkinter as tk
from tkinter import filedialog, messagebox
import wikipedia
from PIL import Image, ImageTk
from pygame import mixer

import colors
import dibujar as draw
import whats as wp

# ================================================================
# Configuración general
# ================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
SITES_FILE = os.path.join(BASE_DIR, "paginas.txt")
FILES_FILE = os.path.join(BASE_DIR, "archivos.txt")
APPS_FILE = os.path.join(BASE_DIR, "apps.txt")
CONTACTS_FILE = os.path.join(BASE_DIR, "contacts.txt")
ALARM_SOUND = os.path.join(BASE_DIR, "wake_me.mp3")

BG_MAIN = "#B9B3E7"
BG_PANEL = "#86A8E7"
BG_TITLE = "#7F7FD5"
FG_TITLE = "#C6FFDD"
BG_CARD = "#E8E6FA"

FONT_TITLE = ("Roboto", 34, "bold")
FONT_SUBTITLE = ("Arial", 15, "bold")
FONT_NORMAL = ("Arial", 11)
FONT_COMMANDS = ("Arial", 9, "bold")
FONT_BUTTON = ("Arial", 11, "bold")

listening_lock = tr.Lock()

# ================================================================
# Utilidades
# ================================================================


def remove_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text or "")
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def normalize_text(text: str) -> str:
    """Normaliza texto reconocido o escrito para que los comandos sean más tolerantes."""
    text = remove_accents(text or "").lower().strip()
    text = re.sub(r"[¿?¡!.,;:]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Frases de relleno que suele entender el reconocimiento.
    prefixes_to_remove = [
        "alex ", "oye alex ", "hey alex ", "hola alex ", "por favor ", "che ",
    ]
    for prefix in prefixes_to_remove:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break

    replacements = [
        ("abrime ", "abre "),
        ("abreme ", "abre "),
        ("abri ", "abre "),
        ("abrir ", "abre "),
        ("abre la pagina ", "abre "),
        ("abre pagina ", "abre "),
        ("abrir pagina ", "abre "),
        ("abreme ", "abre "),
        ("a ver ", "abre "),
        ("haber ", "abre "),
        ("a ver si abre ", "abre "),
        ("quiero abrir ", "abre "),
        ("quiero que abras ", "abre "),
        ("podrias abrir ", "abre "),
        ("abre el programa ", "abre "),
        ("abrir programa ", "abre "),
        ("abrir archivo ", "archivo "),
        ("abre archivo ", "archivo "),
        ("abre el archivo ", "archivo "),
        ("busqueda ", "busca "),
        ("buscar ", "busca "),
        ("buscame ", "busca "),
        ("googlea ", "busca "),
        ("buscalo ", "busca "),
        ("reproducir ", "reproduce "),
        ("reproduci ", "reproduce "),
        ("poneme ", "reproduce "),
        ("pon ", "reproduce "),
        ("toca ", "reproduce "),
        ("musica ", "reproduce "),
        ("wiki ", "wikipedia "),
        ("que es ", "wikipedia "),
        ("quien es ", "wikipedia "),
        ("quien fue ", "wikipedia "),
        ("buscar en wikipedia ", "wikipedia "),
        ("busca en wikipedia ", "wikipedia "),
        ("anota ", "nota "),
        ("anotar ", "nota "),
        ("tomar nota", "nota"),
        ("crear nota", "nota"),
        ("nueva nota", "nota"),
        ("mandar mensaje", "mensaje"),
        ("enviar mensaje", "mensaje"),
        ("manda mensaje", "mensaje"),
        ("whatsapp", "mensaje"),
        ("detener", "terminar"),
        ("para", "terminar"),
        ("pausa", "terminar"),
        ("salir", "hasta luego"),
        ("cerrar alex", "hasta luego"),
        ("cerrar programa", "hasta luego"),
    ]

    for old, new in replacements:
        if text == old.strip() or text.startswith(old):
            text = text.replace(old, new, 1).strip()
            break

    # Correcciones frecuentes del reconocimiento de voz.
    common_mistakes = {
        "abre gogol": "abre google",
        "abre gugul": "abre google",
        "abre gugel": "abre google",
        "abre go gol": "abre google",
        "abre kic": "abre kick",
        "abre kik": "abre kick",
        "busca gogol": "busca google",
    }
    return common_mistakes.get(text, text)


def ensure_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def load_dict(file_name: str) -> dict:
    data = {}
    if not os.path.exists(file_name):
        return data

    with open(file_name, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "," not in line:
                continue
            key, value = line.split(",", 1)
            key = normalize_text(key)
            value = value.strip()
            if key and value:
                data[key] = value
    return data


def save_dict(file_name: str, data: dict) -> None:
    with open(file_name, "w", encoding="utf-8") as f:
        for key in sorted(data):
            f.write(f"{key},{data[key]}\n")


def closest_key(query: str, data: dict, cutoff: float = 0.72) -> str | None:
    """Permite abrir algo aunque el reconocimiento no sea exacto."""
    query = normalize_text(query)
    if query in data:
        return query
    if not query or not data:
        return None
    matches = difflib.get_close_matches(query, list(data.keys()), n=1, cutoff=cutoff)
    return matches[0] if matches else None


def set_status(text: str) -> None:
    try:
        status_var.set(text)
    except Exception:
        print(text)


def append_log(message: str) -> None:
    def _write():
        text_info.insert(tk.END, f"\n{message}")
        text_info.see(tk.END)
    try:
        main_window.after(0, _write)
    except Exception:
        print(message)


# ================================================================
# Ventana principal
# ================================================================

main_window = tk.Tk()
main_window.title("Alex AI")
main_window.configure(background=BG_MAIN)
try:
    main_window.state("zoomed")
except Exception:
    main_window.geometry("1420x860")

try:
    main_window.iconbitmap(os.path.join(BASE_DIR, "alex_ico.ico"))
except Exception:
    pass

main_window.grid_columnconfigure(0, weight=0, minsize=430)
main_window.grid_columnconfigure(1, weight=1, minsize=470)
main_window.grid_columnconfigure(2, weight=0, minsize=530)
main_window.grid_rowconfigure(0, weight=1)

left_frame = tk.Frame(main_window, bg=BG_MAIN)
left_frame.grid(row=0, column=0, sticky="nsw", padx=(20, 10), pady=20)

center_frame = tk.Frame(main_window, bg=BG_MAIN)
center_frame.grid(row=0, column=1, sticky="n", padx=10, pady=20)

right_frame = tk.Frame(main_window, bg=BG_MAIN)
right_frame.grid(row=0, column=2, sticky="nse", padx=(10, 30), pady=70)

# ================================================================
# Panel izquierdo
# ================================================================

commands = """Comandos de voz / texto:

reproduce Queen
wikipedia Disney
busca Netflix
alarma 09:30
colores
dibujar
abre google
archivo contrato
nota comprar leche
mensaje
terminar
hasta luego

Variantes aceptadas:
abrí google / abrir google
buscar Netflix / pon Queen
wiki Disney / nueva nota"""

commands_frame = tk.Frame(left_frame, bg=BG_PANEL, width=400, height=455, highlightthickness=1, highlightbackground="white")
commands_frame.grid(row=0, column=0, sticky="nw")
commands_frame.grid_propagate(False)

label_commands = tk.Label(
    commands_frame,
    text=commands,
    bg=BG_PANEL,
    fg="black",
    font=FONT_COMMANDS,
    justify="left",
    anchor="nw",
    wraplength=360,
)
label_commands.place(x=18, y=14, width=360, height=430)

manual_label = tk.Label(left_frame, text="Historial de Alex:", bg=BG_MAIN, fg="black", font=("Arial", 12, "bold"))
manual_label.grid(row=1, column=0, sticky="w", pady=(18, 6))

text_info = tk.Text(
    left_frame,
    bg="white",
    fg="black",
    font=FONT_NORMAL,
    relief="solid",
    bd=2,
    wrap="word",
    exportselection=False
)
text_info.grid(row=2, column=0, sticky="nw")
text_info.config(width=43, height=8)

command_label = tk.Label(left_frame, text="Escribí un comando o texto:", bg=BG_MAIN, fg="black", font=("Arial", 12, "bold"))
command_label.grid(row=3, column=0, sticky="w", pady=(10, 4))

command_entry = tk.Entry(left_frame, bg="white", fg="black", font=FONT_NORMAL, relief="solid", bd=2, width=43)
command_entry.grid(row=4, column=0, sticky="w")
command_entry.focus()
command_entry.bind("<Return>", lambda event: execute_manual_text())

manual_buttons = tk.Frame(left_frame, bg=BG_MAIN)
manual_buttons.grid(row=5, column=0, sticky="w", pady=(8, 0))

# ================================================================
# Centro
# ================================================================

label_title = tk.Label(center_frame, text="Alex AI", background=BG_TITLE, fg=FG_TITLE, font=FONT_TITLE)
label_title.grid(row=0, column=0, pady=(0, 18))

try:
    alex_image = Image.open(os.path.join(BASE_DIR, "alex_photo.png"))
    alex_image = alex_image.resize((390, 390))
    alex_photo = ImageTk.PhotoImage(alex_image)
    window_photo = tk.Label(center_frame, image=alex_photo, bg=BG_MAIN)
    window_photo.image = alex_photo
    window_photo.grid(row=1, column=0)
except Exception as e:
    window_photo = tk.Label(center_frame, text=f"No se pudo cargar alex_photo.png\n{e}", bg=BG_MAIN, font=FONT_NORMAL)
    window_photo.grid(row=1, column=0)

status_var = tk.StringVar(value="Listo")
status_label = tk.Label(center_frame, textvariable=status_var, bg=BG_MAIN, font=("Arial", 11, "bold"))
status_label.grid(row=2, column=0, pady=(12, 0))

# ================================================================
# Voz
# ================================================================
speech_lock = tr.Lock()


def _speak_with_windows_sapi(text: str) -> bool:
    """Habla usando la voz de Windows. Es más estable que pyttsx3 dentro de Tkinter."""
    if not sys.platform.startswith("win"):
        return False

    safe_text = (text or "").replace("@'", "@ ’")
    script = f"""
Add-Type -AssemblyName System.Speech
$voz = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voz.Rate = 0
$voz.Speak(@'
{safe_text}
'@)
"""
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    creationflags = getattr(sub, "CREATE_NO_WINDOW", 0)
    sub.run(
        ["powershell", "-NoProfile", "-EncodedCommand", encoded],
        creationflags=creationflags,
        check=False,
    )
    return True


def talk(text: str) -> None:
    if not text:
        return

    text = str(text).strip()
    if not text:
        return

    print("Alex:", text)
    append_log("Alex: " + text)

    def _worker():
        with speech_lock:
            try:
                if _speak_with_windows_sapi(text):
                    return

                # Fallback por si no está en Windows.
                local_engine = pyttsx3.init()
                local_engine.setProperty("rate", 145)
                local_engine.say(text)
                local_engine.runAndWait()
                local_engine.stop()
            except Exception as e:
                print("Error en voz:", e)

    tr.Thread(target=_worker, daemon=True).start()


def _get_text_to_read() -> str:
    """Lee la selección del campo escrito; si no hay selección, lee todo el campo."""
    try:
        selected = command_entry.selection_get().strip()
        if selected:
            return selected
    except Exception:
        pass
    return command_entry.get().strip()


def read_and_talk() -> None:
    text = _get_text_to_read()
    if not text:
        talk("No hay texto para leer.")
        return
    talk(text)


def delete_text() -> None:
    command_entry.delete(0, tk.END)


def clear_history() -> None:
    text_info.delete("1.0", tk.END)

def listen() -> str:
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            set_status("Escuchando...")
            append_log("Escuchando...")

            # Más tiempo de calibración = mejor tolerancia al ruido ambiente.
            recognizer.adjust_for_ambient_noise(source, duration=2.0)
            recognizer.pause_threshold = 1.0
            recognizer.phrase_threshold = 0.25
            recognizer.non_speaking_duration = 0.5

            audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)

        set_status("Procesando...")
        raw_text = recognizer.recognize_google(audio, language="es-AR")
        normalized = normalize_text(raw_text)

        append_log(f"Google entendió: {raw_text}")
        append_log(f"Comando interpretado: {normalized}")

        return normalized

    except sr.WaitTimeoutError:
        append_log("No escuché nada.")
        return ""
    except sr.UnknownValueError:
        append_log("No entendí el audio. Probá hablar más cerca o más despacio.")
        return ""
    except sr.RequestError as e:
        print("Error de conexión:", e)
        talk("Hubo un error con el reconocimiento de voz.")
        return ""
    except Exception as e:
        print("Error inesperado escuchando:", e)
        talk("No pude usar el micrófono.")
        return ""
    finally:
        set_status("Listo")

# ================================================================
# Datos
# ================================================================

sites = load_dict(SITES_FILE)
files = load_dict(FILES_FILE)
programs = load_dict(APPS_FILE)
contacts = load_dict(CONTACTS_FILE)

# ================================================================
# Comandos
# ================================================================


def reproduce(rec: str) -> None:
    music = rec.replace("reproduce", "", 1).strip()
    if not music:
        talk("Decime qué canción o banda querés reproducir.")
        return
    talk("Reproduciendo " + music)
    pywhatkit.playonyt(music)


def googlea(rec: str) -> None:
    query = rec.replace("busca", "", 1).strip()
    if not query:
        talk("Decime qué querés buscar.")
        return
    talk("Buscando " + query)
    webbrowser.open("https://www.google.com/search?q=" + quote(query), new=2)


def busca_wikipedia(rec: str) -> None:
    search = rec.replace("wikipedia", "", 1).strip()
    if not search:
        talk("Decime qué querés buscar en Wikipedia.")
        return

    wikipedia.set_lang("es")
    try:
        result = wikipedia.summary(search, sentences=2)
        append_log(f"Wikipedia - {search}:\n{result}")
        talk(result)
    except wikipedia.exceptions.DisambiguationError as e:
        opciones = ", ".join(e.options[:5])
        append_log("Opciones de Wikipedia: " + opciones)
        talk("Hay varios resultados. Mirá las opciones en el cuadro de texto.")
    except wikipedia.exceptions.PageError:
        talk("No encontré información.")
    except Exception as e:
        print("Error Wikipedia:", e)
        talk("Ocurrió un error buscando en Wikipedia.")


def thread_alarma(rec: str) -> None:
    tr.Thread(target=clock, args=(rec,), daemon=True).start()


def colores(rec: str) -> None:
    talk("Abriendo cámara para detectar colores. Presioná Q o T para salir.")
    tr.Thread(target=colors.capture, daemon=True).start()


def dibujar(rec: str) -> None:
    talk("Abriendo lienzo. Presioná M para cambiar modo, C para limpiar y Q para salir.")
    tr.Thread(target=draw.capture, daemon=True).start()


def abre(rec: str) -> None:
    command = rec.replace("abre", "", 1).strip()
    key_site = closest_key(command, sites)
    key_program = closest_key(command, programs)

    print("Comando a abrir:", command)
    print("Páginas disponibles:", sites)
    print("Apps disponibles:", programs)

    if key_site:
        url = ensure_url(sites[key_site])
        talk(f"Abriendo {key_site}")
        webbrowser.open(url, new=2)
        return

    if key_program:
        path = programs[key_program]
        talk(f"Abriendo {key_program}")
        try:
            os.startfile(path)
        except Exception:
            sub.Popen(path, shell=True)
        return

    talk("No encontré esa aplicación o página.")


def archivo(rec: str) -> None:
    filename = rec.replace("archivo", "", 1).strip()
    key = closest_key(filename, files)

    if key:
        path = files[key]
        talk(f"Abriendo {key}")
        try:
            os.startfile(path)
        except Exception:
            sub.Popen(path, shell=True)
        return

    talk("Ese archivo no está agregado.")


def escribe(rec: str) -> None:
    texto = rec.replace("nota", "", 1).strip()

    if not texto:
        talk("¿Qué querés escribir en la nota?")
        texto = listen()

    if not texto:
        talk("No escuché el contenido de la nota.")
        return

    note_path = os.path.join(BASE_DIR, "nota.txt")
    with open(note_path, "a", encoding="utf-8") as f:
        f.write(texto + os.linesep)

    talk("Nota creada, puedes verla.")
    try:
        os.startfile(note_path)
    except Exception:
        sub.Popen(note_path, shell=True)


def clock(rec: str) -> None:
    num = rec.replace("alarma", "", 1).strip()
    num = num.replace("y", ":").replace(".", ":").replace(" ", "")

    # Permite "930" como 09:30 y "2130" como 21:30.
    if re.fullmatch(r"\d{3,4}", num):
        if len(num) == 3:
            num = "0" + num
        num = num[:2] + ":" + num[2:]

    if re.fullmatch(r"\d{1,2}:\d{1,2}", num):
        hour, minute = num.split(":")
        hour_i = int(hour)
        minute_i = int(minute)
        if hour_i > 23 or minute_i > 59:
            talk("La hora de la alarma no es válida.")
            return
        num = f"{hour_i:02d}:{minute_i:02d}"
    else:
        talk("Formato de alarma no válido. Probá decir alarma 09:30.")
        return

    talk("Alarma activada a las " + num)
    append_log("Alarma activada. Presioná T para detenerla cuando suene.")

    while True:
        if datetime.datetime.now().strftime("%H:%M") == num:
            try:
                mixer.init()
                mixer.music.load(ALARM_SOUND)
                mixer.music.play()
            except Exception as e:
                print("Error alarma:", e)
                talk("No pude reproducir wake_me.mp3.")
                return

            while mixer.music.get_busy():
                if keyboard.is_pressed("t"):
                    mixer.music.stop()
                    return
                time.sleep(0.2)
            return
        time.sleep(1)


def enviar_mensaje(rec: str) -> None:
    talk("¿A quién querés enviar el mensaje?")
    contact = listen()
    key = closest_key(contact, contacts)

    if key:
        talk("¿Qué querés que diga?")
        message = listen()
        if not message:
            talk("No escuché el mensaje.")
            return
        talk("Abriendo WhatsApp Web para enviar el mensaje.")
        wp.send_message(contacts[key], message)
    else:
        talk("Ese contacto no está agregado.")


def terminar(rec: str) -> None:
    # Ahora Alex escucha una sola vez por botón, así que terminar queda como pausa/no-op.
    set_status("Pausado. Tocá el botón para escuchar de nuevo.")
    talk("Listo, quedo en pausa.")


def hasta_luego(rec: str) -> None:
    talk("Nos vemos.")
    main_window.after(500, main_window.destroy)


key_words = {
    "reproduce": reproduce,
    "busca": googlea,
    "wikipedia": busca_wikipedia,
    "alarma": thread_alarma,
    "colores": colores,
    "dibujar": dibujar,
    "archivo": archivo,
    "nota": escribe,
    "mensaje": enviar_mensaje,
    "abre": abre,
    "terminar": terminar,
    "hasta luego": hasta_luego,
}


def execute_command(rec: str) -> None:
    rec = normalize_text(rec)
    print("Reconocido:", rec)
    append_log("Reconocido: " + rec)

    if not rec:
        return

    # Atajos exactos para errores muy comunes.
    alias_map = {
        "reproduci": "reproduce",
        "reproducir": "reproduce",
        "poneme": "reproduce",
        "buscar": "busca",
        "buscame": "busca",
        "abrir": "abre",
        "abri": "abre",
        "anota": "nota",
        "anotar": "nota",
        "whatsapp": "mensaje",
        "mensaje de whatsapp": "mensaje",
    }

    parts = rec.split(maxsplit=1)
    first_word = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    if first_word in alias_map:
        rec = (alias_map[first_word] + " " + rest).strip()

    # Priorizar comandos de dos palabras como "hasta luego" antes de comandos cortos.
    for word in sorted(key_words, key=len, reverse=True):
        func = key_words[word]
        if rec == word or rec.startswith(word + " "):
            print("Ejecutando:", word)
            append_log("Ejecutando: " + word)
            func(rec)
            return

    # Último intento: si la primera palabra salió parecida a un comando, corregirla.
    command_names = list(key_words.keys()) + list(alias_map.keys())
    close = difflib.get_close_matches(first_word, command_names, n=1, cutoff=0.78)
    if close:
        corrected = alias_map.get(close[0], close[0])
        corrected_rec = (corrected + " " + rest).strip()
        append_log(f"Interpreto '{rec}' como '{corrected_rec}'")
        execute_command(corrected_rec)
        return

    talk("No entendí el comando. Probá escribirlo en el cuadro o decirlo de nuevo.")


def run_alex() -> None:
    def worker():
        if listening_lock.locked():
            append_log("Alex ya está escuchando. Esperá un momento.")
            return

        with listening_lock:
            main_window.after(0, lambda: listen_button.config(state="disabled", text="Escuchando..."))
            try:
                rec = listen()
                execute_command(rec)
            finally:
                main_window.after(0, lambda: listen_button.config(state="normal", text="Escuchar comando de voz"))

    tr.Thread(target=worker, daemon=True).start()


def execute_manual_text() -> None:
    text = command_entry.get().strip()
    if not text:
        talk("No escribiste ningún comando.")
        return
    append_log("Escrito: " + text)
    execute_command(text)


# ================================================================
# Botones manuales
# ================================================================

btn_execute_manual = tk.Button(manual_buttons, text="Ejecutar escrito", font=FONT_NORMAL, command=execute_manual_text)
btn_execute_manual.grid(row=0, column=0, padx=(0, 8))

tk.Button(manual_buttons, text="Leer texto", font=FONT_NORMAL, command=read_and_talk).grid(row=0, column=1, padx=(0, 8))
tk.Button(manual_buttons, text="Borrar escrito", font=FONT_NORMAL, command=delete_text).grid(row=0, column=2, padx=(0, 8))
tk.Button(manual_buttons, text="Limpiar historial", font=FONT_NORMAL, command=clear_history).grid(row=0, column=3)

# ================================================================
# Formularios de configuración
# ================================================================


def create_section(parent, title, row):
    section = tk.LabelFrame(parent, text=title, bg=BG_MAIN, fg="black", font=FONT_SUBTITLE, padx=14, pady=12)
    section.grid(row=row, column=0, sticky="ew", pady=(0, 16))
    section.grid_columnconfigure(0, weight=1)
    return section


def refresh_status_saved(kind: str, name: str) -> None:
    set_status(f"{kind} guardado: {name}")
    append_log(f"{kind} guardado: {name}")


def add_files() -> None:
    file_name = normalize_text(filename_entry.get())
    file_path = filepath_entry.get().strip()
    if not file_name or not file_path:
        talk("Completá nombre y ruta del archivo.")
        return
    files[file_name] = file_path
    save_dict(FILES_FILE, files)
    filename_entry.delete(0, "end")
    filepath_entry.delete(0, "end")
    refresh_status_saved("Archivo", file_name)


def add_apps() -> None:
    app_name = normalize_text(appname_entry.get())
    app_path = apppath_entry.get().strip()
    if not app_name or not app_path:
        talk("Completá nombre y ruta de la aplicación.")
        return
    programs[app_name] = app_path
    save_dict(APPS_FILE, programs)
    appname_entry.delete(0, "end")
    apppath_entry.delete(0, "end")
    refresh_status_saved("Aplicación", app_name)


def add_pages() -> None:
    page_name = normalize_text(pagename_entry.get())
    page_url = ensure_url(pageurl_entry.get())
    if not page_name or not page_url:
        talk("Completá nombre y URL de la página.")
        return
    sites[page_name] = page_url
    save_dict(SITES_FILE, sites)
    pagename_entry.delete(0, "end")
    pageurl_entry.delete(0, "end")
    refresh_status_saved("Página", page_name)


def add_contacts() -> None:
    name_contact = normalize_text(namecontact_entry.get())
    phone_contact = phonecontact_entry.get().strip()
    if not name_contact or not phone_contact:
        talk("Completá nombre y teléfono del contacto.")
        return
    contacts[name_contact] = phone_contact
    save_dict(CONTACTS_FILE, contacts)
    namecontact_entry.delete(0, "end")
    phonecontact_entry.delete(0, "end")
    refresh_status_saved("Contacto", name_contact)


def pick_file(entry: tk.Entry) -> None:
    path = filedialog.askopenfilename(title="Seleccionar archivo")
    if path:
        entry.delete(0, "end")
        entry.insert(0, path)


files_section = create_section(right_frame, "Archivos", 0)
tk.Label(files_section, text="Nombre del archivo:", bg=BG_MAIN, font=FONT_NORMAL).grid(row=0, column=0, sticky="w")
filename_entry = tk.Entry(files_section, width=42, font=FONT_NORMAL)
filename_entry.grid(row=1, column=0, sticky="ew", pady=(2, 8))
tk.Label(files_section, text="Ruta del archivo:", bg=BG_MAIN, font=FONT_NORMAL).grid(row=2, column=0, sticky="w")
filepath_entry = tk.Entry(files_section, width=42, font=FONT_NORMAL)
filepath_entry.grid(row=3, column=0, sticky="ew", pady=(2, 6))
tk.Button(files_section, text="Seleccionar archivo", font=FONT_NORMAL, command=lambda: pick_file(filepath_entry)).grid(row=4, column=0, sticky="w", pady=(0, 6))
tk.Button(files_section, text="Agregar archivo", font=FONT_NORMAL, command=add_files).grid(row=5, column=0, sticky="w")

apps_section = create_section(right_frame, "Aplicaciones", 1)
tk.Label(apps_section, text="Nombre de la aplicación:", bg=BG_MAIN, font=FONT_NORMAL).grid(row=0, column=0, sticky="w")
appname_entry = tk.Entry(apps_section, width=42, font=FONT_NORMAL)
appname_entry.grid(row=1, column=0, sticky="ew", pady=(2, 8))
tk.Label(apps_section, text="Ruta de la aplicación:", bg=BG_MAIN, font=FONT_NORMAL).grid(row=2, column=0, sticky="w")
apppath_entry = tk.Entry(apps_section, width=42, font=FONT_NORMAL)
apppath_entry.grid(row=3, column=0, sticky="ew", pady=(2, 6))
tk.Button(apps_section, text="Seleccionar app", font=FONT_NORMAL, command=lambda: pick_file(apppath_entry)).grid(row=4, column=0, sticky="w", pady=(0, 6))
tk.Button(apps_section, text="Agregar aplicación", font=FONT_NORMAL, command=add_apps).grid(row=5, column=0, sticky="w")

pages_section = create_section(right_frame, "Páginas web", 2)
tk.Label(pages_section, text="Nombre de la página:", bg=BG_MAIN, font=FONT_NORMAL).grid(row=0, column=0, sticky="w")
pagename_entry = tk.Entry(pages_section, width=42, font=FONT_NORMAL)
pagename_entry.grid(row=1, column=0, sticky="ew", pady=(2, 8))
tk.Label(pages_section, text="URL de la página:", bg=BG_MAIN, font=FONT_NORMAL).grid(row=2, column=0, sticky="w")
pageurl_entry = tk.Entry(pages_section, width=42, font=FONT_NORMAL)
pageurl_entry.grid(row=3, column=0, sticky="ew", pady=(2, 10))
tk.Button(pages_section, text="Agregar página", font=FONT_NORMAL, command=add_pages).grid(row=4, column=0, sticky="w")

contacts_section = create_section(right_frame, "Contactos WhatsApp", 3)
tk.Label(contacts_section, text="Nombre del contacto:", bg=BG_MAIN, font=FONT_NORMAL).grid(row=0, column=0, sticky="w")
namecontact_entry = tk.Entry(contacts_section, width=42, font=FONT_NORMAL)
namecontact_entry.grid(row=1, column=0, sticky="ew", pady=(2, 8))
tk.Label(contacts_section, text="Teléfono (+549...):", bg=BG_MAIN, font=FONT_NORMAL).grid(row=2, column=0, sticky="w")
phonecontact_entry = tk.Entry(contacts_section, width=42, font=FONT_NORMAL)
phonecontact_entry.grid(row=3, column=0, sticky="ew", pady=(2, 10))
tk.Button(contacts_section, text="Agregar contacto", font=FONT_NORMAL, command=add_contacts).grid(row=4, column=0, sticky="w")

listen_button = tk.Button(center_frame, text="Escuchar comando de voz", font=("Arial", 13, "bold"), command=run_alex)
listen_button.grid(row=3, column=0, pady=(22, 0))

close_button = tk.Button(center_frame, text="Cerrar Alex", font=FONT_NORMAL, command=lambda: execute_command("hasta luego"))
close_button.grid(row=4, column=0, pady=(10, 0))

append_log("Alex listo. Tocá 'Escuchar comando de voz' una vez por comando, o escribí en el campo de abajo y presioná 'Ejecutar escrito'.")
main_window.mainloop()
