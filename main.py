import machine
import network # para el WiFi
import socket
from time import sleep
import time # Añadido para manejo de tiempos precisos del botón

# 1. CONFIGURACIÓN DE HARDWARE (PINES)

# Configuración de los registros de corrimiento 
AB = machine.Pin(14, machine.Pin.OUT)
CLK = machine.Pin(15, machine.Pin.OUT)

# Configuración del Botón (Pin 16) y Buzzer (Pin 17)
# Se usa PULL_DOWN como requiere el diagrama de la maqueta
boton = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_DOWN)
buzzer = machine.PWM(machine.Pin(17))


# 2. FUNCIONES RASPYCONNECTION

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

def EjecutarSecuencia(secuencia):
    """
    Función de prueba1.py integrada para los LEDs.
    Recibe una lista de 8 bits.
    """
    for i in range(8):
        bit = secuencia[7-i]
        AB.value(bit) # Usamos .value() para asignar el bit
        CLK.value(1)
        CLK.value(0)

def sonar_buzzer(estado):
    """Hace sonar el buzzer a 1kHz cuando el estado es True"""
    if estado:
        buzzer.freq(1000)
        buzzer.duty_u16(32768) # 50% de ciclo de trabajo (volumen)
    else:
        buzzer.duty_u16(0)

# 4. LÓGICA INTEGRADA (BOTÓN + CLIENTE)


def iniciar_sistema():
    # 1. Conectar a la red
    connectToWifi()
    
    # 2. Configuración del servidor (IP de tu ServerR.py en Visual Studio)
    server_address = ('192.168.8.134', 8001) 
    
    try:
        # Creamos el socket una sola vez para mantener la conexión abierta
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Creando socket...")
        client_socket.connect(server_address)
        print("Conectado al servidor en Visual Studio")

        # Limpiar LEDs al iniciar (secuencia de ceros)
        EjecutarSecuencia([0,0,0,0,0,0,0,0])

        codigo_acumulado = "" # Aquí guardamos los . y -
        
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
                
                # Opcional: Mostrar algo en los LEDs al presionar
                EjecutarSecuencia([1,1,1,1,1,1,1,1]) # Prende todos momentáneamente
                sleep(0.1)
                EjecutarSecuencia([0,0,0,0,0,0,0,0]) # Apaga

    except Exception as e:
        print("Error en el sistema:", e)
    finally:
        if 'client_socket' in locals():
            client_socket.close()
            print("Conexión cerrada.")

# Ejecutar el programa completo
iniciar_sistema()
