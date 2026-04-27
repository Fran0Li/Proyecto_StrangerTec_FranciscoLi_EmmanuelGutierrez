import socket

server_address = ('192.168.8.134', 8001)  # Dirección IP y puerto del server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # crea el socket 

try:   
    server_socket.bind(server_address) # Enlazar el socket al servidor
    server_socket.listen(1)  # Conexiones entrantes (solo es la raspy)
    print("Servidor iniciado. Escuchando en {}:{}".format(*server_address))

except OSError as e:
    print("Error al iniciar el servidor:", e)
    exit()

def handle_connection(client_socket): # Acá se maneja la conexión ya establecida
    try:
        print("Conexion establecida desde {}".format(client_socket.getpeername()))
        while True:
            data = client_socket.recv(1024) #1024 son la cantidad de bytes que recibe a la vez
            if not data:
                print("Cliente {} desconectado.".format(client_socket.getpeername()))
                break
            print("Mensaje recibido desde {}: {}".format(client_socket.getpeername(), data.decode()))

            # verificar el mensaje recibido y responder
            received_message = data.decode()
            expected_message = "Hola, este mensaje es enviado desde la raspy :)"
            response_message = "Hola, este mensaje es enviado desde el server :)"

            if received_message == expected_message:
                print("Mensaje de la Raspy confirmado. Enviando respuesta...")
                client_socket.sendall(response_message.encode()) # Codifica la respuesta a bytes y la envía
           
            # ##############################################################################

    except ConnectionError as e:
        print("Error de conexión con el cliente:", e)
    finally:
        client_socket.close()

while True:
    try:
        print("Esperando conexiones entrantes...")
        client_socket, client_address = server_socket.accept()
        print("aceptada")
        handle_connection(client_socket)
    except KeyboardInterrupt:
        print("Servidor detenido por el usuario")
        break
    except Exception as e:
        print("Error durante la aceptación de conexiones:", e)