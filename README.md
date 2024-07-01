# Final Project Kelompok "Chat Protocol"
oleh:
- Adrian Aziz Santoso (NRP 5025221229)
- David Ralphwaldo (NRP 05111940000190)
- Moh. Adib Syambudi (NRP 5025211017)
- Gilang Aliefidanto (NRP 5025211119)
- Dimas Aria Pujangga (NRP 5025211212)
- Anneu Tsabita (NRP 5025211026)

## Pembagian Tugas Antar Anggota Tim:
- Adrian Aziz Santoso: Mengimplementasikan private messaging
- David Ralphwaldo Martuaraja: implementasi UI
- Moh. Adib Syambudi: implementasi send/receive file
- Gilang Aliefidanto: implementasi group messaging
- Dimas Aria Pujannga: definisi protokol pertukaran antar server antar realm
- Anneu Tsabita: mengerjakan arsitektur implementasi 

## Pembagian Tugas Antar Anggota Tim:
Kami telah membuat repository GitHub untuk memudahkan dalam manajemen dan kolaborasi. Berikut adalah link untuk repository gitHub-nya:
[https://github.com/adrianazizsantoso/chatProtocol](https://github.com/adrianazizsantoso/chatProtocol)

## Definisi Protokol Chat:

**1. Definisi Protokol Chat (secara umum):**

```
// Implementasi protokol chat (secara umum)
// protokol.py


import json


class Protokol:
   @staticmethod
   def buat_pesan(tipe, **kwargs):
       pesan = {'tipe': tipe}
       pesan.update(kwargs)
       return json.dumps(pesan).encode()


   @staticmethod
   def parse_pesan(data):
       return json.loads(data.decode())


   @staticmethod
   def buat_pesan_login(username, password):
       return Protokol.buat_pesan('login', username=username, password=password)


   @staticmethod
   def buat_pesan_kirim(from_username, to_username, message):
       return Protokol.buat_pesan('kirim', from=from_username, to=to_username, message=message)


   @staticmethod
   def buat_pesan_terima(username):
       return Protokol.buat_pesan('terima', username=username)
```

**2. Definisi Protokol Komunikasi:**

```
// Implementasi protokol komunikasi
// komunikasi.py


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
```

**3. Definisi Protokol Private Messaging:**

```
// Implementasi private messaging di sisi server
// pengguna.py

from komunikasi import ClientRealm
import argparse

def main():
    parser = argparse.ArgumentParser(description='Aplikasi Chat Sederhana')
    parser.add_argument('--host', default='localhost', help='Alamat host server')
    parser.add_argument('--port', type=int, default=8000, help='Port server')
    parser.add_argument('--username', required=True, help='Nama pengguna')
    parser.add_argument('--password', required=True, help='Kata sandi pengguna')
    parser.add_argument('--to', help='Nama pengguna tujuan')
    parser.add_argument('--message', help='Pesan yang akan dikirim')

    args = parser.parse_args()

    client = ClientRealm(args.host, args.port)
    client.connect(args.username, args.password)

    if args.to and args.message:
        client.send_pesan(args.to, args.message)
        print(f'Pesan dikirim ke {args.to}: {args.message}')
    else:
        try:
            while True:
                user_input = input('> ')
                if user_input.startswith('/quit'):
                    break
                elif user_input.startswith('/send '):
                    parts = user_input.split(' ', 2)
                    if len(parts) == 3:
                        to_username, message = parts[1], parts[2]
                        client.send_pesan(to_username, message)
                        print(f'Pesan dikirim ke {to_username}: {message}')
                else:
                    print('Perintah tidak dikenali. Ketik /help untuk daftar perintah.')
        finally:
            client.disconnect()

if __name__ == '__main__':
    main()
```

**4: Definisi Protokol Group Messaging:**

```
// Implementasi group messaging di sisi server
// grup.py

from komunikasi import ServerRealm
import argparse

def main():
    parser = argparse.ArgumentParser(description='Aplikasi Chat Grup Sederhana')
    parser.add_argument('--host', default='localhost', help='Alamat host server')
    parser.add_argument('--port', type=int, default=8000, help='Port server')
    parser.add_argument('--username', required=True, help='Nama pengguna')
    parser.add_argument('--password', required=True, help='Kata sandi pengguna')
    parser.add_argument('--join', help='Nama grup untuk bergabung')
    parser.add_argument('--create', help='Nama grup baru untuk dibuat')
    parser.add_argument('--message', help='Pesan yang akan dikirim ke grup')

    args = parser.parse_args()

    server = ServerRealm(args.host, args.port)
    server.connect(args.username, args.password)

    if args.join:
        server.gabung_grup(args.join)
        print(f'Bergabung dengan grup "{args.join}"')
    elif args.create:
        server.buat_grup(args.create)
        print(f'Membuat grup baru "{args.create}"')

    if args.message:
        server.kirim_pesan_grup(args.message)
        print(f'Pesan dikirim ke grup: {args.message}')
    else:
        try:
            while True:
                user_input = input('> ')
                if user_input.startswith('/quit'):
                    break
                elif user_input.startswith('/join '):
                    grup_nama = user_input.split(' ', 1)[1]
                    server.gabung_grup(grup_nama)
                    print(f'Bergabung dengan grup "{grup_nama}"')
                elif user_input.startswith('/create '):
                    grup_nama = user_input.split(' ', 1)[1]
                    server.buat_grup(grup_nama)
                    print(f'Membuat grup baru "{grup_nama}"')
                elif user_input.startswith('/send '):
                    pesan = user_input.split(' ', 1)[1]
                    server.kirim_pesan_grup(pesan)
                    print(f'Pesan dikirim ke grup: {pesan}')
                else:
                    print('Perintah tidak dikenali. Ketik /help untuk daftar perintah.')
        finally:
            server.disconnect()

if __name__ == '__main__':
    main()
```

**5. Definisi Protokol Send dan Receive File:**

```
// Implementasi send file di sisi client
// client.py

# Import the necessary modules

import socket
import sys
import time

# Creating the socket and accepting user input hostname

socket_server = socket.socket()
server_host = socket.gethostname()
ip = socket.gethostbyname(server_host)
sport = 8080

# Connection to the server
print("This is your IP address:", ip)
server_host = input("Enter friend\'s IP address: ")
name = input("Enter Friend\'s name: ")

socket_server.connect((server_host, sport))

# Receiving the message from the server
socket_server.send(name.encode())
server_name = socket_server.recv(1024)
server_name = server_name.decode()

print(server_name, " has joined...")
while True:
    message = (socket_server.recv(1024)).decode()
    print(server_name, ":", message)
    message = input("Me: ")
    socket_server.send(message.encode())
```

**6. Definisi Protokol Utilitas:**

```
// Implementasi protokol utilitas
// utils.py

import datetime
import hashlib
import os
import random
import string

def generate_password(length=12):
    """
    Membuat kata sandi acak dengan panjang yang ditentukan.

    Args:
        length (int): Panjang kata sandi yang diinginkan.

    Returns:
        str: Kata sandi acak.
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def hash_password(password):
    """
    Melakukan hash terhadap kata sandi menggunakan SHA-256.

    Args:
        password (str): Kata sandi yang akan dihash.

    Returns:
        str: Hasil hash kata sandi.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_timestamp():
    """
    Mendapatkan timestamp saat ini dalam format ISO 8601.

    Returns:
        str: Timestamp saat ini.
    """
    return datetime.datetime.now().isoformat()

def create_temp_file(prefix='tmp_', suffix='.txt', directory=None):
    """
    Membuat file sementara dengan prefiks dan sufiks yang ditentukan.

    Args:
        prefix (str): Prefiks untuk nama file.
        suffix (str): Sufiks untuk nama file.
        directory (str): Direktori tempat file akan dibuat.

    Returns:
        str: Path file sementara yang dibuat.
    """
    if directory is None:
        directory = os.path.join(os.getcwd(), 'tmp')
    os.makedirs(directory, exist_ok=True)
    file_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    file_path = os.path.join(directory, f"{prefix}{file_name}{suffix}")
    return file_path
```

## Definisi Protokol Pertukaran Data Antar Server / Server Utama / Server Realm:

**1. Implementasi Pertukaran Data Antar Server (secara umum):**

```
// Implementasi pertukaran data antar server
// server.py

# Import the necessary modules

import socket
import sys
import time

# Creating the sockets and retrieving the hostname

new_socket = socket.socket()
host_name = socket.gethostname()
s_ip = socket.gethostbyname(host_name)
port = 8080

# Bind the host and port

new_socket.bind(host_name, port)
print("Binding successful...")
print("This is your ip: ", s_ip)

# Listening for connections
name = input("Enter your nickname: ")
new_socket.listen(1)

# Accepting incoming connections

conn, add = new_socket.accept()

print("Received connection from ", add[0])
print("connection Established. Connected from: ", add[0])

# Storing incoming connection data

client = (conn;recv(1024)).decode()
print(client + " has connected.")
conn.send(name.encode())

# Delivering messages

while True:
    message = input("Me : ")
    conn.send(message.encode())
    message = conn.recv(1024)
    message = message.decode()
    print(client, ":", message)
```

2. Implementasi Pertukaran Data Antar Server Utama:
```
// Implementasi pertukaran data antar server utama
// server_utama.py

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
```

3. Implementasi Pertukaran Data Antar Server Realm:
```
// Implementasi 1 pertukaran data antar server realm
// server_realm1.py

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
```

```
// Implementasi 2 pertukaran data antar server realm
// server_realm2.py

import socket
import threading
import json
from pengguna import Pengguna
from komunikasi import Komunikasi

class ServerRealm2:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.pengguna = {}  # Menyimpan daftar pengguna dalam realm ini
        self.percakapan = {}  # Menyimpan daftar percakapan

    def run(self):
        print(f"Server Realm 2 berjalan di {self.host}:{self.port}")
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
    server = ServerRealm2("localhost", 8002)
    server.run()
```

## Arsitektur Implementasi:
- Kami menggunakan arsitektur client-server.
- Server diimplementasikan menggunakan bahasa pemrograman Java.
- Client dapat diimplementasikan menggunakan berbagai bahasa pemrograman, seperti Java, Python, atau JavaScript.
- Server menggunakan port ID Address dan port sebagai berikut:
  - Server Utama: 192.168.1.100:8000
  - Server Realm 1: 192.168.1.101:8001
  - Server Realm 2: 192.168.1.102:8002
 
## Menjalankan Server dan Client:

Dengan menggunakan PyCharm, kita dapat menjalankan server dan client dengan menjalankan client.py selama kita sudah mengunduh kesemua kodingan python yang terdapat dalam repository Github berikut terlebih dahulu:

[https://github.com/adrianazizsantoso/chatProtocol](https://github.com/adrianazizsantoso/chatProtocol)

<img width="511" alt="image" src="https://github.com/adrianazizsantoso/chatProtocol/assets/115202624/ed40455b-1136-4b97-b66a-f35a1895c20e">

## IP Address dan Port Server:
- IP Address Server: 192.168.1.100
- Port Server: 8080

## Penggunaan Flet untuk membuat User Interface untuk Infrastruktur Chat:

Inilah ide yang kita gunakan untuk membangun arsitektur multi-realm chat dengan menggunakan Flet [https://flet.dev](https://flet.dev):

1. Protokol Komunikasi Antar Realm:
Untuk komunikasi antar realm, kita dapat menggunakan protokol berbasis REST API atau WebSocket.
Setiap server chat dalam realm masing-masing dapat terhubung ke server gateway yang bertanggung jawab untuk meneruskan pesan antar realm.
Server gateway ini dapat menggunakan protokol autentikasi lintas domain untuk memverifikasi identitas pengguna dari realm yang berbeda.
Protokol ini juga harus menjamin keamanan dan privasi pesan yang dikirim antar realm.

2. Thread Komunikasi Antar Realm:
Setiap server chat dalam realm masing-masing dapat memiliki thread terpisah yang khusus digunakan untuk mengirim dan menerima pesan dari server gateway.
Thread ini dapat berjalan secara asyncronous untuk memastikan komunikasi tetap lancar tanpa mengganggu alur kerja utama aplikasi chat.
Thread ini dapat menangani otentikasi, routing pesan, sinkronisasi data, dan manajemen koneksi antar realm.

3. User Interface dengan Flet:
Untuk membangun user interface chat, kita dapat menggunakan Flet yang berbasis pada Flutter.
Flet menyediakan berbagai kontrol dan widget yang dapat digunakan untuk membangun antarmuka chat, seperti kotak pesan, tombol kirim, dan lainnya.
Dengan Flet, kita dapat membuat aplikasi chat yang dapat dijalankan di web, desktop, maupun mobile dengan kode Python yang sama.
Integrasi antara aplikasi chat lokal dan mekanisme komunikasi antar realm dapat dilakukan melalui API atau event handling yang disediakan oleh Flet.

Secara garis besar, arsitektur multi-realm chat menggunakan Flet dapat terdiri atas:
1. Server chat lokal dalam setiap realm
2. Server gateway untuk komunikasi antar realm
3. Thread terpisah di setiap server chat untuk menangani komunikasi antar realm
4. User interface chat menggunakan kontrol dan widget Flet

Dengan arsitektur ini, setiap server chat lokal dapat saling bertukar pesan melalui server gateway, sementara pengguna dapat berinteraksi dengan antarmuka chat yang konsisten di berbagai platform.


## Penutup:

Demikian tugas akhir Kelompok 9 Pemrograman Jaringan C. Kami telah memberikan dokumentasi yang komprehensif mengenai pembagian tugas, repository, definisi protokol chat, pertukaran data antar server, arsitektur implementasi, serta cara menjalankan server dan client. Kami berharap dokumentasi dan kode-kode yang telah kami cantumkan bermanfaat dalam memahami dan mengimplementasikan aplikasi chat yang sesuai dengan kebutuhan.
