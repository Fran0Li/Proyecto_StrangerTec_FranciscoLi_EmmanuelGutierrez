import machine
import network # para el WiFi
import socket
from time import sleep
import time # Añadido para manejo de tiempos precisos del botón

# 1. CONFIGURACIÓN DE HARDWARE (PINES)

# Configuración de los registros de corrimiento 
AB = machine.Pin(14, machine.Pin.OUT)#GPIO 14
CLK = machine.Pin(15, machine.Pin.OUT)#GPIO 15

# LEDs de Filas (LED 14 al 16, conectados a la raspy)
# Se activan con 0 (Tierra) y se apagan con 1
led14 = machine.Pin(13, machine.Pin.OUT) # GPIO 13
led15 = machine.Pin(12, machine.Pin.OUT) # GPIO 12
led16 = machine.Pin(11, machine.Pin.OUT) # GPIO 11

# Configuración del Botón (Pin 16) y Buzzer (Pin 17)
# Se usa PULL_DOWN como requiere el diagrama de la maqueta
boton = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_DOWN)
buzzer = machine.PWM(machine.Pin(17))


#Diccionarios de traducción
#Traductor de Morse a texto
MORSE_DICC = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', 
    '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', 
    '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O', 
    '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T', 
    '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y', 
    '--..': 'Z', '.----': '1', '..---': '2', '...--': '3', '....-': '4', 
    '.....': '5', '-....': '6', '--...': '7', '---..': '8', '----.': '9', 
    '-----': '0', '.-.-.': '+', 
    '-....-': '-'}
#Patron en la maqueta
#La letrac(bits del registo, led14, led15, led 16) es decir, las filas
PATRONES_LEDMAQUE = { 'A': ('1000000000000000', 1, 0, 0),
    'B': ('0100000000000000', 1, 0, 0),
    'C': ('0010000000000000', 1, 0, 0),
    'D': ('0001000000000000', 1, 0, 0),
    'E': ('0000100000000000', 1, 0, 0),
    'F': ('0000010000000000', 1, 0, 0),
    'G': ('0000001000000000', 1, 0, 0),
    'H': ('0000000100000000', 1, 0, 0),
    'I': ('0000000010000000', 1, 0, 0),
    'J': ('0000000001000000', 1, 0, 0),
    'K': ('0000000000100000', 1, 0, 0),
    'L': ('0000000000010000', 1, 0, 0),
    'M': ('0000000000001000', 1, 0, 0),
    'N': ('0000000000000100', 0, 1, 0),
    'O': ('1111111111111111', 1, 1, 1), # Prende todo
    'P': ('0000000000000010', 0, 1, 0),
    'Q': ('0000000000000001', 0, 1, 0),
    'R': ('1100000000000000', 0, 1, 0),
    'S': ('0011000000000000', 0, 1, 0),
    'T': ('0000110000000000', 0, 1, 0),
    'U': ('0000001100000000', 0, 1, 0),
    'V': ('0000000011000000', 0, 0, 1),
    'W': ('0000000000110000', 0, 0, 1),
    'X': ('0000000000001100', 0, 0, 1),
    'Y': ('0000000000000011', 0, 0, 1),
    'Z': ('1010101010101010', 0, 0, 1),
    '+': ('0000111110000000', 0, 1, 0),
    '-': ('1111111111111111', 0, 0, 0) }


# FUNCIONES RASPYCONNECTION

ssid = "FranLi"  #nombre de la red
password = "RackitiLi081029" #contraseña de la red

def connectToWifi():
    try:
        wlan = network.WLAN(network.STA_IF) #crea la interfaz para la conexión
        wlan.active(True)
        wlan.connect(ssid, password) 
        while wlan.isconnected() == False: 
            print('Esperando la conexion...')
            sleep(1)
        picoIp = wlan.ifconfig()[0] #obtiene la ip asignada a la raspy
        print('Conectado exitosamente a la ip: ' + str(picoIp))
    except:
        print('Algo salio mal. Intente nuevamente')

# 3. FUNCIONES DE APOYO (LEDs y SONIDO)
def actualizar_maqueta(letra):
    """Esta función 'salta' aquí cuando hay una letra lista"""
    if letra in PATRONES_LEDMAQUE:
        bits_reg, l14, l15, l16 = PATRONES_LEDMAQUE[letra]
        #Enviar los 16 bits
        for bit in reversed(bits_reg):
            AB.value(int(bit))
            CLK.value(1)
            CLK.value(0)
        
        # Prender/Apagar los LEDs de la Raspy (0=prende, 1=apaga)
        led14.value(0 if l14 == 1 else 1)
        led15.value(0 if l15 == 1 else 1)
        led16.value(0 if l16 == 1 else 1)

def sonar_buzzer(estado):
    """Hace sonar el buzzer a 1kHz cuando el estado es True"""
    if estado:
        buzzer.freq(1000)
        buzzer.duty_u16(32768) # 50% de ciclo de trabajo (volumen)
    else:
        buzzer.duty_u16(0)

# 4. LÓGICA PRINCIPAL (BOTÓN + CLIENTE)


def iniciar_sistema():
    # 1. Conectar a la red
    connectToWifi()
    
    # 2. Configuración del servidor (IP de ServerR.py en Visual)
    server_address = ('10.210.86.206', 8001) 
    
    try:
        # Creamos el socket una sola vez para mantener la conexión abierta
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Creando socket...")
        client_socket.connect(server_address)
        print("Conectado al servidor en Visual Studio")

        codigo_acumulado = "" # Aquí guardamos los . y -
        last_time = time.ticks_ms()
        
        print("Esperando entrada Morse (Botón)...")
        
        while True:
            # Detección del botón
            if boton.value() == 1:
                inicio_pulso = time.ticks_ms()
                sonar_buzzer(True)
                
                # Bucle mientras el botón está hundido
                while boton.value() == 1:
                    pass
                
                duracion = time.ticks_diff(time.ticks_ms(), inicio_pulso)
                sonar_buzzer(False)

                # Clasificación de pulsos
                if duracion < 300: # Menos de 0.3s es punto
                    simbolo = "."
                else:              # Más de 0.3s es raya
                    simbolo = "-"
                
                codigo_acumulado += simbolo
                print("Capturado:", simbolo, "| Código actual:", codigo_acumulado)

                # Enviar el símbolo inmediatamente al servidor
                client_socket.sendall(simbolo.encode())
                last_time = time.ticks_ms() #Reinicia el tiempo de espera
            if codigo_acumulado != "" and time.ticks_diff(time.ticks_ms(), last_time) > 1500:
                letra = MORSE_DICC.get(codigo_acumulado, "?")
                print("Letra detectada:", letra)
                
                actualizar_maqueta(letra) #Va a  la maqueta(leds)
                client_socket.sendall(f"[{letra}]".endcode())
                codigo_acumulado = "" #Se limpia para siguiente letra
                
            sleep(0.01)
    
    except Exception as e:
        print("Error en el sistema:", e)
    finally:
        if 'client_socket' in locals():
            client_socket.close()
            print("Conexión cerrada.")

# Ejecutar el programa completo
iniciar_sistema()
