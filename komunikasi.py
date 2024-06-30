import socket
import threading
from protokol import Protokol

class ClientRealm:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        self.running = False
        self.message_handlers = {
            'terima': self.handle_pesan_terima
        }

    def connect(self, username, password):
        self.socket.connect((self.host, self.port))
        login_pesan = Protokol.buat_pesan_login(username, password)
        self.socket.sendall(login_pesan)
        self.username = username
        self.running = True
        self.receive_thread = threading.Thread(target=self.receive_loop)
        self.receive_thread.start()

    def send_pesan(self, to_username, message):
        pesan = Protokol.buat_pesan_kirim(self.username, to_username, message)
        self.socket.sendall(pesan)

    def receive_loop(self):
        while self.running:
            data = self.socket.recv(1024)
            if not data:
                break
            pesan = Protokol.parse_pesan(data)
            self.handle_pesan(pesan)

    def handle_pesan(self, pesan):
        tipe = pesan['tipe']
        if tipe in self.message_handlers:
            self.message_handlers[tipe](pesan)
        else:
            print(f'Pesan tidak dikenali: {pesan}')

    def handle_pesan_terima(self, pesan):
        from_username = pesan['from']
        message = pesan['message']
        print(f'Pesan dari {from_username}: {message}')

    def disconnect(self):
        self.running = False
        self.socket.close()

class ServerRealm:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(1)
        self.clients = {}
        self.message_handlers = {
            'login': self.handle_login,
            'kirim': self.handle_kirim
        }

    def run(self):
        print(f'Server berjalan pada {self.host}:{self.port}')
        while True:
            conn, addr = self.socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(conn,))
            client_thread.start()

    def handle_client(self, conn):
        try:
            data = conn.recv(1024)
            pesan = Protokol.parse_pesan(data)
            self.handle_pesan(pesan, conn)
        except:
            pass
        finally:
            conn.close()

    def handle_pesan(self, pesan, conn):
        tipe = pesan['tipe']
        if tipe in self.message_handlers:
            self.message_handlers[tipe](pesan, conn)
        else:
            print(f'Pesan tidak dikenali: {pesan}')

    def handle_login(self, pesan, conn):
        username = pesan['username']
        password = pesan['password']
        # Verifikasi login di sini
        self.clients[username] = conn
        print(f'Pengguna {username} terhubung')

    def handle_kirim(self, pesan, conn):
        from_username = pesan['from']
        to_username = pesan['to']
        message = pesan['message']
        to_conn = self.clients.get(to_username, None)
        if to_conn:
            to_pesan = Protokol.buat_pesan_kirim(from_username, to_username, message)
            to_conn.sendall(to_pesan)
        else:
            print(f'Pengguna {to_username} tidak ditemukan')