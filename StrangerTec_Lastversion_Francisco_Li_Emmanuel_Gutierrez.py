import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import threading
import socket
import random
import os

# CONFIGURACIÓN DE RUTAS Y RED 
# Esto asegura que encuentre la imagen st2.jpg sin importar desde dónde  se corra 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_IMAGEN = os.path.join(BASE_DIR, "st2.jpg")

IP_SERVER = '10.210.86.206' 
PUERTO = 8001
SERVER_ADDRESS = (IP_SERVER, PUERTO)

MORSE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', ' ': '/', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..', 
    '9': '----.', '0': '-----', '+': '.-.-.', '-': '-....-'
}

PALABRAS = ["SOS", "SI", "NO", "TEC", "PYTHON", "PICO W", "COMPUTADORES", "C++"]
score_p1, score_p2, ronda_actual = 0, 0, 1
frase_objetivo = ""
cliente_maqueta = None

#  MOTOR DE RED 
def servidor_hilo(callback_update):
    global cliente_maqueta
    """Hilo encargado de recibir datos de la Raspberry"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #SO_REUSEADDR ayuda a que el puerto se libere rápido al cerrar/abrir
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind(SERVER_ADDRESS)
        server_socket.listen(1)
        print(f"Servidor activo. Esperando maqueta...")
        while True:
            client_socket, addr = server_socket.accept()
            cliente_maqueta = client_socket # Guarda la conexión
            print(f"Maqueta conectada desde: {addr}", flush=True)
            try:
                while True:
                    data = client_socket.recv(1024)
                    if not data: break
                    callback_update(data.decode())
            except: pass
            finally: 
                cliente_maqueta = None
                client_socket.close()
    except Exception as e:
        print(f"Error de red: {e}")

def enviar_frase_a_maqueta(frase):
    global cliente_maqueta
    if cliente_maqueta :
        try:
            cliente_maqueta.send((frase + "\n").encode())#Se envia frase a la raspy
            print(f"Transmitiendo frase: {frase}")
        except: 
            print("Error al enviar datos")


#  LÓGICA DE PUNTUACIÓN 
def calcular_puntos(original, entrada):
    puntos = 0
    original, entrada = original.upper(), entrada.upper()
    for i in range(min(len(original), len(entrada))):
        if original[i] == entrada[i]: puntos += 10 
    return puntos

#  INTERFACES (CRÉDITOS Y JUEGO) 
def about():
    """Ventana de créditos recuperada"""
    v = tk.Toplevel(ventana)
    v.title("Acerca de")
    v.geometry("400x320")
    tk.Label(v, text="StrangerTec\nTEC - Computadores\nFrancisco Li / Emanuel Gutiérrez", font=("Arial", 12, "bold")).pack(expand=True)

def pantalla_final(v_padre, modo_nombre):
    v_res = tk.Toplevel(v_padre)
    v_res.title("RESULTADOS")
    v_res.geometry("900x600")
    v_res.configure(bg="#050505")
    
    tk.Label(v_res, text="PUNTUACIÓN TOTAL", font=("Courier", 24, "bold"), fg="red", bg="#050505").pack(pady=30)
    
    if modo_nombre == "1 Jugador":
        tk.Label(v_res, text=f"{score_p1} PTS", font=("Courier", 35), fg="yellow", bg="#151515").pack(pady=20)
    else:
        ganador = "¡EMPATE!"
        if score_p1 > score_p2: ganador = "¡GANA JUGADOR A!"
        elif score_p2 > score_p1: ganador = "¡GANA JUGADOR B!"
        tk.Label(v_res, text=f"{ganador}\nA: {score_p1} | B: {score_p2}", font=("Courier", 20), fg="white", bg="#151515").pack(pady=20)
    
    tk.Button(v_res, text="REGRESAR AL MENÚ", bg="red", fg="white", command=lambda: [v_res.destroy(), v_padre.destroy()]).pack(pady=40)

def ventana_juego(modo_nombre):
    global score_p1, score_p2, ronda_actual, frase_objetivo
    score_p1, score_p2, ronda_actual = 0, 0, 1
    frase_objetivo = random.choice(PALABRAS)
    
    v_j = tk.Toplevel(ventana)
    v_j.geometry("1300x900")
    v_j.configure(bg="#0a0a0a")
    
    # Diccionario Morse lateral
    f_info = tk.Frame(v_j, bg="#111", width=220)
    f_info.pack(side=tk.LEFT, fill="y", padx=10, pady=10)
    lbl_ronda = tk.Label(f_info, text=f"RONDA: {ronda_actual}/3", bg="#111", fg="yellow", font=("Arial", 14, "bold"))
    lbl_ronda.pack(pady=20)
    
    txt_morse = tk.Text(f_info, bg="#111", fg="white", font=("Courier", 9), width=20, height=30, bd=0)
    txt_morse.pack(pady=5)
    for char, code in sorted(MORSE_DICT.items()): txt_morse.insert(tk.END, f"{char}: {code}\n")
    txt_morse.config(state=tk.DISABLED)

    # Área de Juego
    f_derecho = tk.Frame(v_j, bg="#0a0a0a")
    f_derecho.pack(side=tk.RIGHT, fill="both", expand=True)
    cv = tk.Canvas(f_derecho, width=800, height=150, bg="#000", highlightbackground="red")
    cv.pack(pady=15)
    
    def actualizar_pantalla():
        enviar_frase_a_maqueta(frase_objetivo)# transmision hacia la maqueta
        txt = frase_objetivo if modo_nombre == "1 Jugador" else "--- TURNO JUGADOR A ---"
        cv.delete("all")
        cv.create_text(400, 75, text=txt, fill="white", font=("Courier", 30, "bold"), tags="display")

    actualizar_pantalla()
    ent_text = tk.Entry(f_derecho, font=("Courier", 22), bg="#151515", fg="cyan", justify="center")
    ent_text.pack(fill="x", pady=5, padx=50)

    # Teclado en pantalla 
    f_teclado = tk.Frame(f_derecho, bg="#0a0a0a")
    f_teclado.pack(pady=10)
    teclas = ['Q','W','E','R','T','Y','U','I','O','P','A','S','D','F','G','H','J','K','L','Z','X','C','V','B','N','M','1','2','3','4','5','6','7','8','9','0',' ','+','-']
    r, c = 0, 0
    for t in teclas:
        tk.Button(f_teclado, text=t, width=4, height=2, bg="#333", fg="white", command=lambda char=t: ent_text.insert(tk.END, char)).grid(row=r, column=c, padx=2, pady=2)
        c += 1
        if c > 9: c = 0; r += 1
    tk.Button(f_teclado, text="⌫", width=4, height=2, bg="red", fg="white", command=lambda: ent_text.delete(len(ent_text.get())-1, tk.END)).grid(row=r, column=c, padx=2, pady=2)

    def recibir_maqueta(msj):
        """Traduce la señal de red a texto en pantalla"""
        if msj.startswith("[") and msj.endswith("]"):
            ent_text.insert(tk.END, msj[1:-1])
        elif msj == " ": ent_text.insert(tk.END, " ")

    # Inicia comunicación con Raspberry
    threading.Thread(target=servidor_hilo, args=(recibir_maqueta,), daemon=True).start()
    print("Esperando conexiones")

    def avanzar():
        global score_p1, score_p2, ronda_actual, frase_objetivo
        if modo_nombre == "1 Jugador":
            score_p1 += calcular_puntos(frase_objetivo, ent_text.get())
            if ronda_actual < 3:
                ronda_actual += 1
                frase_objetivo = random.choice(PALABRAS)
                ent_text.delete(0, tk.END)
                lbl_ronda.config(text=f"RONDA: {ronda_actual}/3")
                actualizar_pantalla()
            else: pantalla_final(v_j, modo_nombre)
        else: #MODO VERSUS (Transmisión y escucha)
            if "JUGADOR A" in cv.itemcget("display", "text") or "TRANSMITIENDO" in cv.itemcget("display", "text"):
                score_p1 += calcular_puntos(frase_objetivo, ent_text.get())
                ent_text.delete(0, tk.END)
                # Cambiamos a Jugador B pero mantenemos la frase para que la vuelva a oír/ver
                cv.itemconfig("display", text="--- TURNO JUGADOR B ---", fill="#00ffff")
                messagebox.showinfo("Cambio", "Turno de Jugador B. ¡Atento a la maqueta!")
                enviar_frase_a_maqueta(frase_objetivo) 
            else:
                score_p2 += calcular_puntos(frase_objetivo, ent_text.get())
                if ronda_actual < 3:
                    ronda_actual += 1
                    frase_objetivo = random.choice(PALABRAS)
                    ent_text.delete(0, tk.END)
                    lbl_ronda.config(text=f"RONDA: {ronda_actual}/3")
                    actualizar_pantalla()
                else: pantalla_final(v_j, modo_nombre)
                
    tk.Button(f_derecho, text="VALIDAR / SIGUIENTE", bg="red", fg="white", font=("Arial", 14, "bold"), command=avanzar).pack(pady=20)

#  MENÚ PRINCIPAL 
ventana = tk.Tk()
ventana.title('StrangerTec')
ventana.geometry("1100x700")

# Bloque de carga de imagen mejorado para evitar errores de ruta
if os.path.exists(PATH_IMAGEN):
    try:
        img_open = Image.open(PATH_IMAGEN).resize((1100, 700))
        fondo = ImageTk.PhotoImage(img_open)
        label_fondo = tk.Label(ventana, image=fondo)
        label_fondo.place(x=0, y=0)
        label_fondo.image = fondo # Persistencia de imagen en memoria
    except Exception as e:
        print(f"Error cargando imagen: {e}")
        ventana.configure(bg="black")
else:
    print(f"ERROR: No se encontró la imagen en {PATH_IMAGEN}")
    ventana.configure(bg="black")

# Botones de Menú
tk.Button(ventana, text='1 Jugador', command=lambda: ventana_juego("1 Jugador"), width=25, font=("Arial", 11, "bold")).place(x=150, y=500)
tk.Button(ventana, text='Modo Versus (2P)', command=lambda: ventana_juego("2 Jugadores"), width=25, font=("Arial", 11, "bold")).place(x=450, y=500)
tk.Button(ventana, text='Acerca de', command=about, bg="white", width=20, font=("Arial", 12, "bold")).place(x=780, y=500)
tk.Button(ventana, text='SALIR', bg="#8b0000", fg="white", width=25, font=("Arial", 11, "bold"), command=ventana.destroy).place(x=430, y=570)

ventana.mainloop()