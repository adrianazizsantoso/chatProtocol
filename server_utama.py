import socket
import threading
import json
from pengguna import Pengguna
from komunikasi import Komunikasi

class ServerUtama:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.realms = {}  # Menyimpan referensi ke server realm
        self.pengguna = {}  # Menyimpan daftar pengguna terdaftar

    def run(self):
        print(f"Server Utama berjalan di {self.host}:{self.port}")
        while True:
            client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        data = client_socket.recv(1024)
        request = json.loads(data.decode())
        
        if request['tipe'] == 'daftar':
            # Proses pendaftaran pengguna
            username = request['username']
            realm = request['realm']
            password = request['password']
            if realm not in self.realms:
                # Realm belum terdaftar, tambahkan ke daftar
                self.realms[realm] = Komunikasi(realm)
            if username not in self.pengguna:
                # Pengguna belum terdaftar, buat akun baru
                self.pengguna[username] = Pengguna(username, realm, password)
                client_socket.sendall(json.dumps({'status': 'berhasil'}).encode())
            else:
                # Pengguna sudah terdaftar
                client_socket.sendall(json.dumps({'status': 'gagal',