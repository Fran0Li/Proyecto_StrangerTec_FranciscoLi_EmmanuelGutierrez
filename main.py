import machine
import network # para el WiFi
import socket
from time import sleep
import time # Añadido para manejo de tiempos precisos del botón

# 1. CONFIGURACIÓN DE HARDWARE (PINES)

# Configuración de los registros de corrimiento
#Primer registro (columnas 1-4, 6-8 y el pin 10 muerto)
AB = machine.Pin(17, machine.Pin.OUT)#data va al pin 17 de la raspy
CLK = machine.Pin(18, machine.Pin.OUT)#clock va al pin 18 de la raspy
#Segundo registro(columnas 5, 9-13, pines 3 y 10 muertos)
#la data va al pin 20 de la raspy
AB2 =machine.Pin(20,machine.Pin.OUT)#el led de la columna 5 esta en este registro en el pin 13 y el led de la columna 9 está en el pin 12 de este registro 
CLK2 = machine.Pin(19, machine.Pin.OUT)#clock va al pin 19 de la raspy

# LEDs de Filas (LED 14 al 16, conectados a la raspy)
# Se activan con 0 (Tierra) y se apagan con 1
#Filas de la maqueta
led14 = machine.Pin(15, machine.Pin.OUT) # GPIO 15, fila 1
led15 = machine.Pin(14, machine.Pin.OUT) # GPIO 14, fila 2
led16 = machine.Pin(13,machine.Pin.OUT) # GPIO 13, fila 3

# Configuración del Botón (Pin 16) y Buzzer (Pin 17)
# Se usa PULL_DOWN como requiere el diagrama de la maqueta
boton = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_DOWN)#el botón va al pin 16 de la raspy
buzzer = machine.PWM(machine.Pin(5))#buzzer va al pin 5 de la raspy con PWM

# PROYECTO II: Pines del circuito incrementador en 5 
# Salidas hacia las entradas A, B, C, D del circuito físico (nibble)
pin_A = machine.Pin(21, machine.Pin.OUT)  # bit más significativo (MSB)
pin_B = machine.Pin(22, machine.Pin.OUT)
pin_C = machine.Pin(26, machine.Pin.OUT)
pin_D = machine.Pin(27, machine.Pin.OUT)  # bit menos significativo (LSB)

# Switch de activación del circuito incrementador (con pull-down interno)
switch_incrementador = machine.Pin(28, machine.Pin.IN, machine.Pin.PULL_DOWN)


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
#Mapa de bits debido a los cambios en la parte física
#Cada "C" se refiere a un led que representa una columna
#Registro1:[C1, C2, C3, C4, 0, C6, C7, C8] el 0 en los 8 bits es el pin 10 (Q4) muerto
#Registro2:[ 0, C10, C11, C12,  0, C13, C9, C5] -> El 0 inicial es el Pin 3 muerto, el 2do 0 es el Pin 10.
PATRONES_LEDMAQUE = { 
    # Formato: 'LETRA': (Bits_Reg1, Bits_Reg2, Fila1, Fila2, Fila3)
    # Siguiendo la lógica de prueba1.py: El primer bit de la cadena es el índice [0]
    
    # --- FILA 1 (Fila1=0) ---
    'A': ('10000000', '00000000', 1, 0, 0), # Col 1 (Pin 3 Reg 1)
    'C': ('01000000', '00000000', 1, 0, 0), # Col 2 (Pin 4 Reg 1)
    'E': ('00100000', '00000000', 1, 0, 0), # Col 3 (Pin 5 Reg 1)
    'G': ('00010000', '00000000', 1, 0, 0), # Col 4 (Pin 6 Reg 1)
    'I': ('00000000', '00000001', 1, 0, 0), # Col 5 (Pin 13 Reg 2)
    'K': ('00000100', '00000000', 1, 0, 0), # Col 6 (Pin 11 Reg 2 -> Q3)
    'M': ('00000010', '00000000', 1, 0, 0), # Col 7 (Pin 12 Reg 2 -> Q4)
    'O': ('00000001', '00000000', 1, 0, 0), # Col 8 (Pin 13 Reg 1 -> Q5)
    'Q': ('00000000', '00000010', 1, 0, 0), # Col 9 (Pin 12 Reg 2)
    'S': ('00000000', '01000000', 1, 0, 0), # Col 10 (Pin 4 Reg 2)
    'U': ('00000000', '00100000', 1, 0, 0), # Col 11 (Pin 5 Reg 2)
    'W': ('00000000', '00010000', 1, 0, 0), # Col 12 (Pin 6 Reg 2)
    'Y': ('00000000', '00000100', 1, 0, 0), # Col 13 (Pin 11 Reg 2)

    # --- FILA 2 (Fila2=0) ---
    'B': ('10000000', '00000000', 0, 1, 0), # Col 1
    'D': ('01000000', '00000000', 0, 1, 0), # Col 2
    'F': ('00100000', '00000000', 0, 1, 0), # Col 3
    'H': ('00010000', '00000000', 0, 1, 0), # Col 4
    'J': ('00000000', '00000001', 0, 1, 0), # Col 5
    'L': ('00000100', '00000000', 0, 1, 0), # Col 6
    'N': ('00000010', '00000000', 0, 1, 0), # Col 7
    'P': ('00000001', '00000000', 0, 1, 0), # Col 8
    'R': ('00000000', '00000010', 0, 1, 0), # Col 9
    'T': ('00000000', '01000000', 0, 1, 0), # Col 10
    'V': ('00000000', '00100000', 0, 1, 0), # Col 11
    'X': ('00000000', '00010000', 0, 1, 0), # Col 12
    'Z': ('00000000', '00000100', 0, 1, 0), # Col 13

    # --- FILA 3 (Fila3=0) ---
    '0': ('10000000', '00000000', 0, 0, 1), # Col 1
    '1': ('01000000', '00000000', 0, 0, 1), # Col 2
    '2': ('00100000', '00000000', 0, 0, 1), # Col 3
    '3': ('00010000', '00000000', 0, 0, 1), # Col 4
    '4': ('00000000', '00010000', 0, 0, 1), # Col 5
    '5': ('00000100', '00000000', 0, 0, 1), # Col 6
    '6': ('00000010', '00000000', 0, 0, 1), 
    '7': ('00000001', '00000000', 0, 0, 1), 
    '8': ('00000000', '00000010', 0, 0, 1), 
    '9': ('00000000', '01000000', 0, 0, 1), 
    '-': ('00000000', '00100000', 0, 0, 1), 
    '+': ('00000000', '00010000', 0, 0, 1),

    'LIMPIAR': ('00000000', '00000000', 0, 0, 0),
    'O_ANM': ('11111111', '11111111', 1, 1, 1)
}


# FUNCIONES DE APOYO (LEDs y SONIDO)
def actualizar_maqueta(letra):
    """Esta función 'salta' aquí cuando hay una letra lista"""
    if letra in PATRONES_LEDMAQUE:
        reg1_bits, reg2_bits, l1, l2, l3 = PATRONES_LEDMAQUE[letra]
        #Registro 1 (leds de las columnas 1-8 excluyendo la 5)
        #Se recorre la cadena de texto de bits de izquierda a derecha
        for i in range (8):
            bit = int(reg1_bits[7-i])
            AB.value(bit)     # Pone el valor del bit (0 o 1) en el pin de datos
            CLK.value(1)           # Genera un pulso de reloj (flanco de subida)
            CLK.value(0)           # Baja el reloj para preparar el siguiente bit
        #Registro 2 (Columnas 5 y 9-13, la nueve al pin 12 y la 5 al pin 13)
        #Se repite la lógica del primero
        for j in range(8):
            bit = int(reg2_bits[7-j])
            AB2.value(bit)     
            CLK2.value(1)           
            CLK2.value(0)
            
        #Control de las Filas
        #Leds de filas encienden con un 0 (tierra)
        #Si el dicc dice 1 (encender), se manda un 0 al pin
        led14.value(l1) # Fila 1 (GP15)
        led15.value(l2) # Fila 2 (GP14)
        led16.value(l3) # Fila 3 (GP13)
    else:
        #si la letra no existe: se limpia la maqueta
        # se envian los 8 ceros a los dos registros
        for _ in range(8):
            AB(0); CLK(1); CLK(0)
            AB2(0); CLK2(1); CLK2(0)
        # Apaga las filas poniendo los pines en 1 (reposo).
        led14.value(0); led15.value(0); led16.value(0)
      

def sonar_buzzer(estado):
    """Hace sonar el buzzer a 1kHz cuando el estado es True"""
    if estado:
        buzzer.freq(1000) # establece el tono, este es el estandar del morse
        buzzer.duty_u16(32768) # 50% de potencia de volumen
    else:
        buzzer.duty_u16(0) # apaga el sonido
        
def enviar_nibble_incrementador(letra):
    """
    Toma el código ASCII de la letra detectada, extrae los 4 bits
    menos significativos (nibble) y los envía a los pines A,B,C,D
    que alimentan el circuito incrementador en 5 (hardware físico).
    También calcula el resultado +5 en software (módulo 16) para
    poder compararlo con lo que muestran los LEDs físicos.
    Retorna el resultado en binario de 4 bits como string "WXYZ".
    """
    ascii_val = ord(letra)
    nibble = ascii_val & 0x0F  # 4 bits menos significativos del ASCII

    # Enviar cada bit al pin correspondiente (A=MSB ... D=LSB)
    pin_A.value((nibble >> 3) & 1)
    pin_B.value((nibble >> 2) & 1)
    pin_C.value((nibble >> 1) & 1)
    pin_D.value(nibble & 1)

    # Cálculo en software del resultado +5 (mod 16) para mostrar en pantalla
    resultado = (nibble + 5) % 16
    resultado_bin = format(resultado, '04b')  # ej: "0110" -> W X Y Z
    return resultado_bin

# FUNCIONES RASPYCONNECTION

ssid = "FranLi"  #nombre de la red
password = "Lrf291424" #contraseña de la red

def connectToWifi():
    try:
        wlan = network.WLAN(network.STA_IF) #crea la interfaz para la conexión
        wlan.active(True) #wnciende antena
        wlan.config(pm = 0xa11140)#Evita que el WiFi se "duerma" por falta de energía de la batería
        wlan.connect(ssid, password) #intenta conexión
        while wlan.isconnected() == False: 
            print('Esperando la conexion...')#espera activa hasta confirmas conexion
            sleep(1)
        picoIp = wlan.ifconfig()[0] #obtiene la ip asignada a la raspy
        print('Conectado exitosamente a la ip: ' + str(picoIp))
    except Exception as e:
        print('Algo salio mal. Intente nuevamente', e)



# 4. LÓGICA PRINCIPAL (BOTÓN + CLIENTE)

def animacion_deinicio():#Parpadeo de bienvenida al juego
    print("Ejecutando animación de inicio...")
    for _ in range(3): # Parpadea 3 veces
        # Prender todo 
        actualizar_maqueta('O_ANM') 
        sleep(0.3)
        # Apagar todo (Usando una letra que no exista para que el else apague todo)
        actualizar_maqueta('LIMPIAR') 
        sleep(0.3)
    #para que el conteo empiece en 0
    last_time = time.ticks_ms()
    codigo_acumulado = ""
    espacio_enviado = True# para que no mande espacio hasta escribir algo
def iniciar_sistema():
    # 1. Conectar a la red
    connectToWifi()
    
    # 2. Configuración del servidor (IP de ServerR.py en Visual)
    server_address = ('10.192.247.206', 8001) 
    
    try:
        # Creamos el socket una sola vez para mantener la conexión abierta
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Creando socket...")
        client_socket.connect(server_address)
        print("Conectado al servidor en Visual Studio")
        client_socket.settimeout(0.1) # Para que también pusa escuchar
        
        #Llamada a la animación de inicio()
        animacion_deinicio()
        print("Maqueta preparada, esperando Stranger Morse!")
        
        codigo_acumulado = "" # Aquí guardamos los . y -
        #Resetear last_time antes del bucle
        last_time = time.ticks_ms()# registra tiempo de la ultima actividad
        espacio_enviado = True
        estado_switch_anterior = -1 #fuerza el primer envío del estado
        print("Esperando entrada Morse (Botón)...")

        
        while True:
            #Sección para escuchar al PC
            try:
                # Intenta recibir la frase de la interfaz (PC)
                datos = client_socket.recv(1024).decode().strip()
                if datos:
                    print("Frase recibida de PC:", datos)
                    # Recorremos cada letra de la palabra recibida
                    for caracter in datos.upper():
                        if caracter in PATRONES_LEDMAQUE:
                            actualizar_maqueta(caracter) # Enciende el LED
                            sonar_buzzer(True)           # Suena el buzzer
                            sleep(0.5)                   # Tiempo que queda encendido
                            actualizar_maqueta('LIMPIAR')# Apaga
                            sonar_buzzer(False)
                            sleep(0.2)                   # Pausa entre letras
            except:
                # Si no hay datos de la PC, simplemente sigue adelante sin trabarse
                pass
            
            # Proyecto II: Verificación del switch de activación
            estado_switch_actual = switch_incrementador.value()
            if estado_switch_actual != estado_switch_anterior:
                if estado_switch_actual == 1:
                    client_socket.sendall("[SW:ON]".encode())
                else:
                    client_socket.sendall("[SW:OFF]".encode())
                    # Al desactivar, apagamos las salidas del circuito
                    pin_A.value(0); pin_B.value(0); pin_C.value(0); pin_D.value(0)
                estado_switch_anterior = estado_switch_actual
                
            # Detección del botón
            if boton.value() == 1:# si el botón esta presionado
                inicio_pulso = time.ticks_ms()#marca el inicio del pulso
                sonar_buzzer(True)# suena el buzzer mientras se presiona
                sleep(0.05)
                
                # Bucle mientras el botón está hundido
                while boton.value() == 1:
                    pass
                
                duracion = time.ticks_diff(time.ticks_ms(), inicio_pulso)# calcula cuanto duro presionado
                sonar_buzzer(False)#apaga el sonido del buzzer

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
                espacio_enviado = False
                
                #Traducción por tiempo y silencio
            time_out = time.ticks_diff(time.ticks_ms(), last_time)
            if codigo_acumulado != "" and time_out > 1500:#Si el código acumulado no está vacío y han pasado 1.5 segundos, desde la ultima presion al boton se traduce
                letra = MORSE_DICC.get(codigo_acumulado, "?")#Busca el código en el dicc, si no existe, devuelve un "?" para que no haya crash
                print("Letra detectada:", letra)#Muestra la letra en la consola de Thonny
                #Se llama a la maqueta
                actualizar_maqueta(letra) #Va a  la maqueta(leds), a la función que apaga/enciende filas
                client_socket.sendall(f"[{letra}]".encode())#envía letra entre llaves al server
                
                #  PROYECTO II: Si el switch está activo, alimenta el circuito incrementador ---
                if switch_incrementador.value() == 1 and letra != "?":
                    resultado_bin = enviar_nibble_incrementador(letra)
                    client_socket.sendall(f"[INC:{resultado_bin}]".encode())
                
                codigo_acumulado = "" #Se limpia la variable para escribir la siguiente letra
            #Silencio de 3s es un espacio/ final de palabra
            if time_out > 3000 and not espacio_enviado:
                print("-Espacio-")
                client_socket.sendall(" ".encode())
                actualizar_maqueta('LIMPIAR')
                espacio_enviado = True
               
            sleep(0.01)# pausa minima para estabilidad
    
    except Exception as e:
        print("Error en el sistema:", e)# si hay error de red
    finally:
        if 'client_socket' in locals():#hace que el socket se cierre bien si el programa se detiene
            client_socket.close()
            print("Conexión cerrada.")

# Ejecutar el programa completo
iniciar_sistema()
