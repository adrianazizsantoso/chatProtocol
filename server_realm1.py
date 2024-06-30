import socket
import threading
import json
from pengguna import Pengguna
from komunikasi import Komunikasi

class ServerRealm1:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.pengguna = {}  # Menyimpan daftar pengguna dalam realm ini
        self.percakapan = {}  # Menyimpan daftar percakapan

    def run(self):
        print(f"Server Realm 1 berjalan di {self.host}:{self.port}")
        while True:
            client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        data = client_socket.recv(1024)
        request = json.loads(data.decode())

        if request['tipe'] == 'login':
            # Proses login pengguna
            username = request['username']
            password = request['password']
            if username in self.pengguna and self.pengguna[username].password == password:
                # Login berhasil, kirim informasi ke client
                client_socket.sendall(json.dumps({'status': 'berhasil'}).encode())
            else:
                # Login gagal
                client_socket.sendall(json.dumps({'status': 'gagal', 'pesan': 'Username atau password salah'}).encode())

        elif request['tipe'] == 'kirim':
            # Proses pengiriman pesan
            from_username = request['from']
            to_username = request['to']
            message = request['message']
            if to_username in self.pengguna:
                # Pengguna tujuan ditemukan, simpan pesan dalam percakapan
                if from_username not in self.percakapan:
                    self.percakapan[from_username] = []
                self.percakapan[from_username].append({'from': from_username, 'to': to_username, 'message': message})
                client_socket.sendall(json.dumps({'status': 'berhasil'}).encode())
            else:
                # Pengguna tujuan tidak ditemukan
                client_socket.sendall(json.dumps({'status': 'gagal', 'pesan': 'Pengguna tujuan tidak ditemukan'}).encode())

        elif request['tipe'] == 'terima':
            # Proses penerimaan pesan
            username = request['username']
            if username in self.percakapan:
                # Kirim daftar percakapan ke client
                client_socket.sendall(json.dumps({'status': 'berhasil', 'percakapan': self.percakapan[username]}).encode())
                self.percakapan[username] = []  # Hapus percakapan setelah dikirim
            else:
                # Tidak ada percakapan untuk pengguna tersebut
                client_socket.sendall(json.dumps({'status': 'gagal', 'pesan': 'Tidak ada percakapan'}).encode())

        client_socket.close()

if __name__ == "__main__":
    server = ServerRealm1("localhost", 8001)
    server.run()