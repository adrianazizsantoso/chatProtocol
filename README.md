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

## Implementasi Chat (secara umum):

**1. Implementasi Chat untuk Client (secara umum):**

```
# chat.py

import base64
import os
from os.path import join, dirname, realpath
import json
import uuid
import logging
from queue import Queue
import threading
import socket
import shutil
from datetime import datetime


class RealmThreadCommunication(threading.Thread):
    def __init__(self, chats, realm_dest_address, realm_dest_port):
        self.chats = chats
        self.chat = {}
        self.realm_dest_address = realm_dest_address
        self.realm_dest_port = realm_dest_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.realm_dest_address, self.realm_dest_port))
        threading.Thread.__init__(self)

    def sendstring(self, string):
        try:
            self.sock.sendall(string.encode())
            receivedmsg = ""
            while True:
                data = self.sock.recv(1024)
                print("diterima dari server", data)
                if data:
                    receivedmsg = "{}{}".format(
                        receivedmsg, data.decode()
                    )  # data harus didecode agar dapat di operasikan dalam bentuk string
                    if receivedmsg[-4:] == "\r\n\r\n":
                        print("end of string")
                        return json.loads(receivedmsg)
        except:
            self.sock.close()
            return {"status": "ERROR", "message": "Gagal"}

    def put(self, message):
        dest = message["msg_to"]
        try:
            self.chat[dest].put(message)
        except KeyError:
            self.chat[dest] = Queue()
            self.chat[dest].put(message)


class Chat:
    def __init__(self):
        self.sessions = {}
        self.users = {}
        self.users["messi"] = {
            "nama": "Lionel Messi",
            "negara": "Argentina",
            "password": "surabaya",
            "incoming": {},
            "outgoing": {},
        }
        self.users["henderson"] = {
            "nama": "Jordan Henderson",
            "negara": "Inggris",
            "password": "surabaya",
            "incoming": {},
            "outgoing": {},
        }
        self.users["lineker"] = {
            "nama": "Gary Lineker",
            "negara": "Inggris",
            "password": "surabaya",
            "incoming": {},
            "outgoing": {},
        }
        self.realms = {}

    def proses(self, data):
        j = data.split(" ")
        try:
            command = j[0].strip()
            if command == "auth":
                username = j[1].strip()
                password = j[2].strip()
                logging.warning("AUTH: auth {} {}".format(username, password))
                return self.autentikasi_user(username, password)

            if command == "register":
                username = j[1].strip()
                password = j[2].strip()
                nama = j[3].strip()
                negara = j[4].strip()
                logging.warning("REGISTER: register {} {}".format(username, password))
                return self.register_user(username, password, nama, negara)

            #   ===================== Komunikasi dalam satu server =====================
            elif command == "send":
                sessionid = j[1].strip()
                usernameto = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}".format(message, w)
                usernamefrom = self.sessions[sessionid]["username"]
                logging.warning(
                    "SEND: session {} send message from {} to {}".format(
                        sessionid, usernamefrom, usernameto
                    )
                )
                return self.send_message(sessionid, usernamefrom, usernameto, message)
            elif command == "sendgroup":
                sessionid = j[1].strip()
                usernamesto = j[2].strip().split(",")
                message = ""
                for w in j[3:]:
                    message = "{} {}".format(message, w)
                usernamefrom = self.sessions[sessionid]["username"]
                logging.warning(
                    "SEND: session {} send message from {} to {}".format(
                        sessionid, usernamefrom, usernamesto
                    )
                )
                return self.send_group_message(
                    sessionid, usernamefrom, usernamesto, message
                )
            elif command == "inbox":
                sessionid = j[1].strip()
                username = self.sessions[sessionid]["username"]
                logging.warning("INBOX: {}".format(sessionid))
                return self.get_inbox(username)
            elif command == "sendfile":
                sessionid = j[1].strip()
                usernameto = j[2].strip()
                filepath = j[3].strip()
                encoded_file = j[4].strip()
                usernamefrom = self.sessions[sessionid]["username"]
                logging.warning(
                    "SENDFILE: session {} send file from {} to {}".format(
                        sessionid, usernamefrom, usernameto
                    )
                )
                return self.send_file(
                    sessionid, usernamefrom, usernameto, filepath, encoded_file
                )
            elif command == "sendgroupfile":
                sessionid = j[1].strip()
                usernamesto = j[2].strip().split(",")
                filepath = j[3].strip()
                encoded_file = j[4].strip()
                usernamefrom = self.sessions[sessionid]["username"]
                logging.warning(
                    "SENDGROUPFILE: session {} send file from {} to {}".format(
                        sessionid, usernamefrom, usernamesto
                    )
                )
                return self.send_group_file(
                    sessionid, usernamefrom, usernamesto, filepath, encoded_file
                )

            #   ===================== Komunikasi dengan server lain =====================
            elif command == "addrealm":
                realm_id = j[1].strip()
                realm_dest_address = j[2].strip()
                realm_dest_port = int(j[3].strip())
                return self.add_realm(
                    realm_id, realm_dest_address, realm_dest_port, data
                )
            elif command == "recvrealm":
                realm_id = j[1].strip()
                realm_dest_address = j[2].strip()
                realm_dest_port = int(j[3].strip())
                return self.recv_realm(
                    realm_id, realm_dest_address, realm_dest_port, data
                )
            elif command == "sendprivaterealm":
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                print(message)
                usernamefrom = self.sessions[sessionid]["username"]
                logging.warning(
                    "SENDPRIVATEREALM: session {} send message from {} to {} in realm {}".format(
                        sessionid, usernamefrom, usernameto, realm_id
                    )
                )
                return self.send_realm_message(
                    sessionid, realm_id, usernamefrom, usernameto, message, data
                )
            elif command == "sendfilerealm":
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                filepath = j[4].strip()
                encoded_file = j[5].strip()
                usernamefrom = self.sessions[sessionid]["username"]
                logging.warning(
                    "SENDFILEREALM: session {} send file from {} to {} in realm {}".format(
                        sessionid, usernamefrom, usernameto, realm_id
                    )
                )
                return self.send_file_realm(
                    sessionid,
                    realm_id,
                    usernamefrom,
                    usernameto,
                    filepath,
                    encoded_file,
                    data,
                )
            elif command == "recvfilerealm":
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                filepath = j[4].strip()
                encoded_file = j[5].strip()
                usernamefrom = self.sessions[sessionid]["username"]
                logging.warning(
                    "RECVFILEREALM: session {} send file from {} to {} in realm {}".format(
                        sessionid, usernamefrom, usernameto, realm_id
                    )
                )
                return self.recv_file_realm(
                    sessionid,
                    realm_id,
                    usernamefrom,
                    usernameto,
                    filepath,
                    encoded_file,
                    data,
                )
            elif command == "recvrealmprivatemsg":
                usernamefrom = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                print(message)
                logging.warning(
                    "RECVREALMPRIVATEMSG: recieve message from {} to {} in realm {}".format(
                        usernamefrom, usernameto, realm_id
                    )
                )
                return self.recv_realm_message(
                    realm_id, usernamefrom, usernameto, message, data
                )
            elif command == "sendgrouprealm":
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(",")
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                usernamefrom = self.sessions[sessionid]["username"]
                logging.warning(
                    "SENDGROUPREALM: session {} send message from {} to {} in realm {}".format(
                        sessionid, usernamefrom, usernamesto, realm_id
                    )
                )
                return self.send_group_realm_message(
                    sessionid, realm_id, usernamefrom, usernamesto, message, data
                )
            elif command == "sendgroupfilerealm":
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(",")
                filepath = j[4].strip()
                encoded_file = j[5].strip()
                usernamefrom = self.sessions[sessionid]["username"]
                logging.warning(
                    "SENDGROUPFILEREALM: session {} send file from {} to {} in realm {}".format(
                        sessionid, usernamefrom, usernamesto, realm_id
                    )
                )
                return self.send_group_file_realm(
                    sessionid,
                    realm_id,
                    usernamefrom,
                    usernamesto,
                    filepath,
                    encoded_file,
                    data,
                )
            elif command == "recvgroupfilerealm":
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(",")
                filepath = j[4].strip()
                encoded_file = j[5].strip()
                usernamefrom = self.sessions[sessionid]["username"]
                logging.warning(
                    "SENDGROUPFILEREALM: session {} send file from {} to {} in realm {}".format(
                        sessionid, usernamefrom, usernamesto, realm_id
                    )
                )
                return self.recv_group_file_realm(
                    sessionid,
                    realm_id,
                    usernamefrom,
                    usernamesto,
                    filepath,
                    encoded_file,
                    data,
                )
            elif command == "recvrealmgroupmsg":
                usernamefrom = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(",")
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                logging.warning(
                    "RECVGROUPREALM: send message from {} to {} in realm {}".format(
                        usernamefrom, usernamesto, realm_id
                    )
                )
                return self.recv_group_realm_message(
                    realm_id, usernamefrom, usernamesto, message, data
                )
            elif command == "getrealminbox":
                sessionid = j[1].strip()
                realmid = j[2].strip()
                username = self.sessions[sessionid]["username"]
                logging.warning(
                    "GETREALMINBOX: {} from realm {}".format(sessionid, realmid)
                )
                return self.get_realm_inbox(username, realmid)
            elif command == "getrealmchat":
                realmid = j[1].strip()
                username = j[2].strip()
                logging.warning("GETREALMCHAT: from realm {}".format(realmid))
                return self.get_realm_chat(realmid, username)
            elif command == "logout":
                return self.logout()
            elif command == "info":
                return self.info()
            else:
                print(command)
                return {"status": "ERROR", "message": "**Protocol Tidak Benar"}
        except KeyError:
            return {"status": "ERROR", "message": "Informasi tidak ditemukan"}
        except IndexError:
            return {"status": "ERROR", "message": "--Protocol Tidak Benar"}

    def autentikasi_user(self, username, password):
        if username not in self.users:
            return {"status": "ERROR", "message": "User Tidak Ada"}
        if self.users[username]["password"] != password:
            return {"status": "ERROR", "message": "Password Salah"}
        tokenid = str(uuid.uuid4())
        self.sessions[tokenid] = {
            "username": username,
            "userdetail": self.users[username],
        }
        return {"status": "OK", "tokenid": tokenid}

    def register_user(self, username, password, nama, negara):
        if username in self.users:
            return {"status": "ERROR", "message": "User Sudah Ada"}
        nama = nama.replace("_", " ")
        self.users[username] = {
            "nama": nama,
            "negara": negara,
            "password": password,
            "incoming": {},
            "outgoing": {},
        }
        tokenid = str(uuid.uuid4())
        self.sessions[tokenid] = {
            "username": username,
            "userdetail": self.users[username],
        }
        return {"status": "OK", "tokenid": tokenid}

    def get_user(self, username):
        if username not in self.users:
            return False
        return self.users[username]

    #   ===================== Komunikasi dalam satu server =====================
    def send_message(self, sessionid, username_from, username_dest, message):
        if sessionid not in self.sessions:
            return {"status": "ERROR", "message": "Session Tidak Ditemukan"}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)

        if s_fr == False or s_to == False:
            return {"status": "ERROR", "message": "User Tidak Ditemukan"}

        message = {"msg_from": s_fr["nama"], "msg_to": s_to["nama"], "msg": message}
        outqueue_sender = s_fr["outgoing"]
        inqueue_receiver = s_to["incoming"]
        try:
            outqueue_sender[username_from].put(message)
        except KeyError:
            outqueue_sender[username_from] = Queue()
            outqueue_sender[username_from].put(message)
        try:
            inqueue_receiver[username_from].put(message)
        except KeyError:
            inqueue_receiver[username_from] = Queue()
            inqueue_receiver[username_from].put(message)
        return {"status": "OK", "message": "Message Sent"}

    def send_group_message(self, sessionid, username_from, usernames_dest, message):
        if sessionid not in self.sessions:
            return {"status": "ERROR", "message": "Session Tidak Ditemukan"}
        s_fr = self.get_user(username_from)
        if s_fr is False:
            return {"status": "ERROR", "message": "User Tidak Ditemukan"}
        for username_dest in usernames_dest:
            s_to = self.get_user(username_dest)
            if s_to is False:
                continue
            message = {"msg_from": s_fr["nama"], "msg_to": s_to["nama"], "msg": message}
            outqueue_sender = s_fr["outgoing"]
            inqueue_receiver = s_to["incoming"]
            try:
                outqueue_sender[username_from].put(message)
            except KeyError:
                outqueue_sender[username_from] = Queue()
                outqueue_sender[username_from].put(message)
            try:
                inqueue_receiver[username_from].put(message)
            except KeyError:
                inqueue_receiver[username_from] = Queue()
                inqueue_receiver[username_from].put(message)
        return {"status": "OK", "message": "Message Sent"}

    def get_inbox(self, username):
        s_fr = self.get_user(username)
        incoming = s_fr["incoming"]
        msgs = {}
        for users in incoming:
            msgs[users] = []
            while not incoming[users].empty():
                msgs[users].append(s_fr["incoming"][users].get_nowait())
        return {"status": "OK", "messages": msgs}

    def send_file(
        self, sessionid, username_from, username_dest, filepath, encoded_file
    ):
        if sessionid not in self.sessions:
            return {"status": "ERROR", "message": "Session Tidak Ditemukan"}

        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)

        if s_fr is False or s_to is False:
            return {"status": "ERROR", "message": "User Tidak Ditemukan"}

        filename = os.path.basename(filepath)
        message = {
            "msg_from": s_fr["nama"],
            "msg_to": s_to["nama"],
            "file_name": filename,
            "file_content": encoded_file,
        }

        outqueue_sender = s_fr["outgoing"]
        inqueue_receiver = s_to["incoming"]
        try:
            outqueue_sender[username_from].put(json.dumps(message))
        except KeyError:
            outqueue_sender[username_from] = Queue()
            outqueue_sender[username_from].put(json.dumps(message))
        try:
            inqueue_receiver[username_from].put(json.dumps(message))
        except KeyError:
            inqueue_receiver[username_from] = Queue()
            inqueue_receiver[username_from].put(json.dumps(message))

        # Simpan file ke folder dengan nama yang mencerminkan waktu pengiriman dan nama asli file
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{now}_{username_from}_{username_dest}_{filename}"
        folder_path = join(dirname(realpath(__file__)), "files/")
        os.makedirs(folder_path, exist_ok=True)
        folder_path = join(folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        file_destination = os.path.join(folder_path, filename)
        if "b" in encoded_file[0]:
            msg = encoded_file[2:-1]

            with open(file_destination, "wb") as fh:
                fh.write(base64.b64decode(msg))
        else:
            tail = encoded_file.split()

        return {"status": "OK", "message": "File Sent"}

    def send_group_file(
        self, sessionid, username_from, usernames_dest, filepath, encoded_file
    ):
        if sessionid not in self.sessions:
            return {"status": "ERROR", "message": "Session Tidak Ditemukan"}
        s_fr = self.get_user(username_from)
        if s_fr is False:
            return {"status": "ERROR", "message": "User Tidak Ditemukan"}

        filename = os.path.basename(filepath)
        for username_dest in usernames_dest:
            s_to = self.get_user(username_dest)
            if s_to is False:
                continue
            message = {
                "msg_from": s_fr["nama"],
                "msg_to": s_to["nama"],
                "file_name": filename,
                "file_content": encoded_file,
            }

            outqueue_sender = s_fr["outgoing"]
            inqueue_receiver = s_to["incoming"]
            try:
                outqueue_sender[username_from].put(json.dumps(message))
            except KeyError:
                outqueue_sender[username_from] = Queue()
                outqueue_sender[username_from].put(json.dumps(message))
            try:
                inqueue_receiver[username_from].put(json.dumps(message))
            except KeyError:
                inqueue_receiver[username_from] = Queue()
                inqueue_receiver[username_from].put(json.dumps(message))

            # Simpan file ke folder dengan nama yang mencerminkan waktu pengiriman dan nama asli file
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            folder_name = f"{now}_{username_from}_{username_dest}_{filename}"
            folder_path = join(dirname(realpath(__file__)), "files/")
            os.makedirs(folder_path, exist_ok=True)
            folder_path = join(folder_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            file_destination = os.path.join(folder_path, filename)
            if "b" in encoded_file[0]:
                msg = encoded_file[2:-1]

                with open(file_destination, "wb") as fh:
                    fh.write(base64.b64decode(msg))
            else:
                tail = encoded_file.split()

        return {"status": "OK", "message": "File Sent"}

    #   ===================== Komunikasi dengan server lain =====================
    def add_realm(self, realm_id, realm_dest_address, realm_dest_port, data):
        j = data.split()
        j[0] = "recvrealm"
        data = " ".join(j)
        data += "\r\n"
        if realm_id in self.realms:
            return {"status": "ERROR", "message": "Realm sudah ada"}

        self.realms[realm_id] = RealmThreadCommunication(
            self, realm_dest_address, realm_dest_port
        )
        result = self.realms[realm_id].sendstring(data)
        return result

    def recv_realm(self, realm_id, realm_dest_address, realm_dest_port, data):
        self.realms[realm_id] = RealmThreadCommunication(
            self, realm_dest_address, realm_dest_port
        )
        return {"status": "OK"}

    def send_realm_message(
        self, sessionid, realm_id, username_from, username_dest, message, data
    ):
        if sessionid not in self.sessions:
            return {"status": "ERROR", "message": "Session Tidak Ditemukan"}
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Tidak Ditemukan"}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if s_fr == False or s_to == False:
            return {"status": "ERROR", "message": "User Tidak Ditemukan"}
        message = {"msg_from": s_fr["nama"], "msg_to": s_to["nama"], "msg": message}
        self.realms[realm_id].put(message)

        j = data.split()
        j[0] = "recvrealmprivatemsg"
        j[1] = username_from
        data = " ".join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {"status": "OK", "message": "Message Sent to Realm"}

    def send_file_realm(
        self,
        sessionid,
        realm_id,
        username_from,
        username_dest,
        filepath,
        encoded_file,
        data,
    ):
        if sessionid not in self.sessions:
            return {"status": "ERROR", "message": "Session Tidak Ditemukan"}
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Tidak Ditemukan"}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if s_fr == False or s_to == False:
            return {"status": "ERROR", "message": "User Tidak Ditemukan"}

        filename = os.path.basename(filepath)
        message = {
            "msg_from": s_fr["nama"],
            "msg_to": s_to["nama"],
            "file_name": filename,
            "file_content": encoded_file,
        }
        self.realms[realm_id].put(message)

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{now}_{username_from}_{username_dest}_{filename}"
        folder_path = join(dirname(realpath(__file__)), "files/")
        os.makedirs(folder_path, exist_ok=True)
        folder_path = join(folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        file_destination = os.path.join(folder_path, filename)
        if "b" in encoded_file[0]:
            msg = encoded_file[2:-1]

            with open(file_destination, "wb") as fh:
                fh.write(base64.b64decode(msg))
        else:
            tail = encoded_file.split()

        j = data.split()
        j[0] = "recvfilerealm"
        j[1] = username_from
        data = " ".join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {"status": "OK", "message": "File Sent to Realm"}

    def recv_file_realm(
        self,
        sessionid,
        realm_id,
        username_from,
        username_dest,
        filepath,
        encoded_file,
        data,
    ):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Tidak Ditemukan"}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if s_fr == False or s_to == False:
            return {"status": "ERROR", "message": "User Tidak Ditemukan"}

        filename = os.path.basename(filepath)
        message = {
            "msg_from": s_fr["nama"],
            "msg_to": s_to["nama"],
            "file_name": filename,
            "file_content": encoded_file,
        }
        self.realms[realm_id].put(message)

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{now}_{username_from}_{username_dest}_{filename}"
        folder_path = join(dirname(realpath(__file__)), "files/")
        os.makedirs(folder_path, exist_ok=True)
        folder_path = join(folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        file_destination = os.path.join(folder_path, filename)
        if "b" in encoded_file[0]:
            msg = encoded_file[2:-1]

            with open(file_destination, "wb") as fh:
                fh.write(base64.b64decode(msg))
        else:
            tail = encoded_file.split()

        return {"status": "OK", "message": "File Received to Realm"}

    def recv_realm_message(self, realm_id, username_from, username_dest, message, data):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Tidak Ditemukan"}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if s_fr == False or s_to == False:
            return {"status": "ERROR", "message": "User Tidak Ditemukan"}
        message = {"msg_from": s_fr["nama"], "msg_to": s_to["nama"], "msg": message}
        self.realms[realm_id].put(message)
        return {"status": "OK", "message": "Message Sent to Realm"}

    def send_group_realm_message(
        self, sessionid, realm_id, username_from, usernames_to, message, data
    ):
        if sessionid not in self.sessions:
            return {"status": "ERROR", "message": "Session Tidak Ditemukan"}
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Tidak Ditemukan"}
        s_fr = self.get_user(username_from)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {"msg_from": s_fr["nama"], "msg_to": s_to["nama"], "msg": message}
            self.realms[realm_id].put(message)

        j = data.split()
        j[0] = "recvrealmgroupmsg"
        j[1] = username_from
        data = " ".join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {"status": "OK", "message": "Message Sent to Group in Realm"}

    def send_group_file_realm(
        self,
        sessionid,
        realm_id,
        username_from,
        usernames_to,
        filepath,
        encoded_file,
        data,
    ):
        if sessionid not in self.sessions:
            return {"status": "ERROR", "message": "Session Tidak Ditemukan"}
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Tidak Ditemukan"}
        s_fr = self.get_user(username_from)

        if s_fr == False:
            return {"status": "ERROR", "message": "User Tidak Ditemukan"}

        filename = os.path.basename(filepath)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {
                "msg_from": s_fr["nama"],
                "msg_to": s_to["nama"],
                "file_name": filename,
                "file_content": encoded_file,
            }
            self.realms[realm_id].put(message)

            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            folder_name = f"{now}_{username_from}_{username_to}_{filename}"
            folder_path = join(dirname(realpath(__file__)), "files/")
            os.makedirs(folder_path, exist_ok=True)
            folder_path = join(folder_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            file_destination = os.path.join(folder_path, filename)
            if "b" in encoded_file[0]:
                msg = encoded_file[2:-1]

                with open(file_destination, "wb") as fh:
                    fh.write(base64.b64decode(msg))
            else:
                tail = encoded_file.split()

        j = data.split()
        j[0] = "recvgroupfilerealm"
        j[1] = username_from
        data = " ".join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {"status": "OK", "message": "Message Sent to Group in Realm"}

    def recv_group_file_realm(
        self,
        sessionid,
        realm_id,
        username_from,
        usernames_to,
        filepath,
        encoded_file,
        data,
    ):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Tidak Ditemukan"}
        s_fr = self.get_user(username_from)

        if s_fr == False:
            return {"status": "ERROR", "message": "User Tidak Ditemukan"}

        filename = os.path.basename(filepath)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {
                "msg_from": s_fr["nama"],
                "msg_to": s_to["nama"],
                "file_name": filename,
                "file_content": encoded_file,
            }
            self.realms[realm_id].put(message)

            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            folder_name = f"{now}_{username_from}_{username_to}_{filename}"
            folder_path = join(dirname(realpath(__file__)), "files/")
            os.makedirs(folder_path, exist_ok=True)
            folder_path = join(folder_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            file_destination = os.path.join(folder_path, filename)
            if "b" in encoded_file[0]:
                msg = encoded_file[2:-1]

                with open(file_destination, "wb") as fh:
                    fh.write(base64.b64decode(msg))
            else:
                tail = encoded_file.split()

        return {"status": "OK", "message": "Message Sent to Group in Realm"}

    def recv_group_realm_message(
        self, realm_id, username_from, usernames_to, message, data
    ):
        if realm_id not in self.realms:
            return {"status": "ERROR", "message": "Realm Tidak Ditemukan"}
        s_fr = self.get_user(username_from)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {"msg_from": s_fr["nama"], "msg_to": s_to["nama"], "msg": message}
            self.realms[realm_id].put(message)
        return {"status": "OK", "message": "Message Sent to Group in Realm"}

    def get_realm_inbox(self, username, realmid):
        if realmid not in self.realms:
            return {"status": "ERROR", "message": "Realm Tidak Ditemukan"}
        s_fr = self.get_user(username)
        result = self.realms[realmid].sendstring(
            "getrealmchat {} {}\r\n".format(realmid, username)
        )
        return result

    def get_realm_chat(self, realmid, username):
        s_fr = self.get_user(username)
        msgs = []
        while not self.realms[realmid].chat[s_fr["nama"]].empty():
            msgs.append(self.realms[realmid].chat[s_fr["nama"]].get_nowait())
        return {"status": "OK", "messages": msgs}

    def logout(self):
        if bool(self.sessions) == True:
            self.sessions.clear()
            return {"status": "OK"}
        else:
            return {"status": "ERROR", "message": "Belum Login"}

    def info(self):
        return {"status": "OK", "message": self.sessions}


if __name__ == "__main__":
    j = Chat()
    sesi = j.proses("auth messi surabaya")
    print(sesi)
    sesi2 = j.proses("auth henderson surabaya")
    tokenid = sesi["tokenid"]
    # tokenid2 = sesi2['tokenid']
    print(j.proses("send {} henderson hello gimana kabarnya son ".format(tokenid)))
    # print(j.proses("send {} messi hello gimana kabarnya mess " . format(tokenid)))

    # print j.send_message(tokenid,'messi','henderson','hello son')
    # print j.send_message(tokenid,'henderson','messi','hello si')
    # print j.send_message(tokenid,'lineker','messi','hello si dari lineker')

    # print("isi mailbox dari messi")
    # print(j.get_inbox('messi'))
    print("isi mailbox dari henderson")
    print(j.get_inbox("henderson"))
```

**2. Implementasi Chat untuk Server:**

```
# chat.py

import base64
import os
from os.path import join, dirname, realpath
import json
import uuid
import logging
from queue import  Queue
import threading 
import socket
import shutil
from datetime import datetime

class RealmThreadCommunication(threading.Thread):
    def __init__(self, chats, realm_dest_address, realm_dest_port):
        self.chats = chats
        self.chat = {}
        self.realm_dest_address = realm_dest_address
        self.realm_dest_port = realm_dest_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.realm_dest_address, self.realm_dest_port))
        threading.Thread.__init__(self)

    def sendstring(self, string):
        try:
            self.sock.sendall(string.encode())
            receivedmsg = ""
            while True:
                data = self.sock.recv(1024)
                print("diterima dari server", data)
                if (data):
                    receivedmsg = "{}{}" . format(receivedmsg, data.decode())  #data harus didecode agar dapat di operasikan dalam bentuk string
                    if receivedmsg[-4:]=='\r\n\r\n':
                        print("end of string")
                        return json.loads(receivedmsg)
        except:
            self.sock.close()
            return { 'status' : 'ERROR', 'message' : 'Gagal'}
    
    def put(self, message):
        dest = message['msg_to']
        try:
            self.chat[dest].put(message)
        except KeyError:
            self.chat[dest]=Queue()
            self.chat[dest].put(message)

class Chat:
    def __init__(self):
        self.sessions={}
        self.users = {}
        self.group = {}
        self.users['messi']={ 'nama': 'Lionel Messi', 'negara': 'Argentina', 'password': 'surabaya', 'incoming' : {}, 'outgoing': {}}
        self.users['henderson']={ 'nama': 'Jordan Henderson', 'negara': 'Inggris', 'password': 'surabaya', 'incoming': {}, 'outgoing': {}}
        self.users['lineker']={ 'nama': 'Gary Lineker', 'negara': 'Inggris', 'password': 'surabaya','incoming': {}, 'outgoing':{}}
        self.realms = {}
    def proses(self,data):
        j=data.split(" ")
        try:
            command=j[0].strip()
            if (command=='auth'):
                username=j[1].strip()
                password=j[2].strip()
                logging.warning("AUTH: auth {} {}" . format(username,password))
                return self.autentikasi_user(username,password)
            
            elif (command=='register'):
                username=j[1].strip()
                password=j[2].strip()
                nama=j[3].strip()
                negara=j[4].strip()
                logging.warning("REGISTER: register {} {}" . format(username,password))
                return self.register_user(username,password, nama, negara)
            
#   ===================== Komunikasi dalam satu server =====================            
            elif (command=='addgroup'):
                sessionid = j[1].strip()
                groupname = j[2].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("ADDGROUP: session {} added group {}" . format(sessionid, groupname))
                return self.addgroup(sessionid,usernamefrom,groupname)
            elif (command == 'joingroup'):
                sessionid = j[1].strip()
                groupname = j[2].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("JOINGROUP: session {} added group {}" . format(sessionid, groupname))
                return self.joingroup(sessionid, usernamefrom, groupname)
            elif (command=='send'):
                sessionid = j[1].strip()
                usernameto = j[2].strip()
                message=""
                for w in j[3:]:
                    message="{} {}" . format(message,w)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SEND: session {} send message from {} to {}" . format(sessionid, usernamefrom,usernameto))
                return self.send_message(sessionid,usernamefrom,usernameto,message)
            elif (command=='sendgroup'):
                sessionid = j[1].strip()
                groupname = j[2].strip()
                message=""
                for w in j[3:]:
                    message="{} {}" . format(message,w)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SEND: session {} send message from {} to {}" . format(sessionid, groupname, usernamefrom,groupname))
                return self.send_group_message(sessionid,groupname, usernamefrom,message)
            elif (command=='inbox'):
                sessionid = j[1].strip()
                username = self.sessions[sessionid]['username']
                logging.warning("INBOX: {}" . format(sessionid))
                return self.get_inbox(username)
            elif (command=='sendfile'):
                sessionid = j[1].strip()
                usernameto = j[2].strip()
                filepath = j[3].strip()
                encoded_file = j[4].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDFILE: session {} send file from {} to {}" . format(sessionid, usernamefrom, usernameto))
                return self.send_file(sessionid, usernamefrom, usernameto, filepath, encoded_file)
            elif (command=='sendgroupfile'):
                sessionid = j[1].strip()
                groupname = j[2].strip()
                filepath = j[3].strip()
                encoded_file = j[4].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDGROUPFILE: session {} send file from {} to {}" . format(sessionid, usernamefrom, groupname))
                return self.send_group_file(sessionid, usernamefrom, groupname, filepath, encoded_file)


  #   ===================== Komunikasi dengan server lain =====================           
            elif (command=='addrealm'):
                realm_id = j[1].strip()
                realm_dest_address = j[2].strip()
                realm_dest_port = int(j[3].strip())
                return self.add_realm(realm_id, realm_dest_address, realm_dest_port, data)
            elif (command=='recvrealm'):
                realm_id = j[1].strip()
                realm_dest_address = j[2].strip()
                realm_dest_port = int(j[3].strip())
                return self.recv_realm(realm_id, realm_dest_address, realm_dest_port, data)
            elif (command == 'sendprivaterealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                print(message)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDPRIVATEREALM: session {} send message from {} to {} in realm {}".format(sessionid, usernamefrom, usernameto, realm_id))
                return self.send_realm_message(sessionid, realm_id, usernamefrom, usernameto, message, data)
            elif (command == 'sendfilerealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                filepath = j[4].strip()
                encoded_file = j[5].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDFILEREALM: session {} send file from {} to {} in realm {}".format(sessionid, usernamefrom, usernameto, realm_id))
                return self.send_file_realm(sessionid, realm_id, usernamefrom, usernameto, filepath, encoded_file, data)
            elif (command == 'recvfilerealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                filepath = j[4].strip()
                encoded_file = j[5].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("RECVFILEREALM: session {} send file from {} to {} in realm {}".format(sessionid, usernamefrom, usernameto, realm_id))
                return self.recv_file_realm(sessionid, realm_id, usernamefrom, usernameto, filepath, encoded_file, data)
            elif (command == 'recvrealmprivatemsg'):
                usernamefrom = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                print(message)
                logging.warning("RECVREALMPRIVATEMSG: recieve message from {} to {} in realm {}".format( usernamefrom, usernameto, realm_id))
                return self.recv_realm_message(realm_id, usernamefrom, usernameto, message, data)
            elif (command == 'sendgrouprealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(',')
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDGROUPREALM: session {} send message from {} to {} in realm {}".format(sessionid, usernamefrom, usernamesto, realm_id))
                return self.send_group_realm_message(sessionid, realm_id, usernamefrom,usernamesto, message,data)
            elif (command == 'sendgroupfilerealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(',')
                filepath = j[4].strip()
                encoded_file = j[5].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDGROUPFILEREALM: session {} send file from {} to {} in realm {}".format(sessionid, usernamefrom, usernamesto, realm_id))
                return self.send_group_file_realm(sessionid, realm_id, usernamefrom, usernamesto, filepath, encoded_file, data)
            elif (command == 'recvgroupfilerealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(',')
                filepath = j[4].strip()
                encoded_file = j[5].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDGROUPFILEREALM: session {} send file from {} to {} in realm {}".format(sessionid, usernamefrom, usernamesto, realm_id))
                return self.recv_group_file_realm(sessionid, realm_id, usernamefrom, usernamesto, filepath, encoded_file, data)
            elif (command == 'recvrealmgroupmsg'):
                usernamefrom = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(',')
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w) 
                logging.warning("RECVGROUPREALM: send message from {} to {} in realm {}".format(usernamefrom, usernamesto, realm_id))
                return self.recv_group_realm_message(realm_id, usernamefrom,usernamesto, message,data)
            elif (command == 'getrealminbox'):
                sessionid = j[1].strip()
                realmid = j[2].strip()
                username = self.sessions[sessionid]['username']
                logging.warning("GETREALMINBOX: {} from realm {}".format(sessionid, realmid))
                return self.get_realm_inbox(username, realmid)
            elif (command == 'getrealmchat'):
                realmid = j[1].strip()
                username = j[2].strip()
                logging.warning("GETREALMCHAT: from realm {}".format(realmid))
                return self.get_realm_chat(realmid, username)
            elif (command=='logout'):
                sessionid = j[1].strip()
                return  self.logout(sessionid)
            elif (command=='info'):
                return self.info()
            else:
                print(command)
                return {'status': 'ERROR', 'message': '**Protocol Tidak Benar'}
        except KeyError:
            return { 'status': 'ERROR', 'message' : 'Informasi tidak ditemukan'}
        except IndexError:
            return {'status': 'ERROR', 'message': '--Protocol Tidak Benar'}

    def autentikasi_user(self,username,password):
        if (username not in self.users):
            return { 'status': 'ERROR', 'message': 'User Tidak Ada' }
        if (self.users[username]['password']!= password):
            return { 'status': 'ERROR', 'message': 'Password Salah' }
        tokenid = str(uuid.uuid4()) 
        self.sessions[tokenid]={ 'username': username, 'userdetail':self.users[username]}
        return { 'status': 'OK', 'tokenid': tokenid }
    
    def register_user(self,username, password, nama, negara):
        if (username in self.users):
            return { 'status': 'ERROR', 'message': 'User Sudah Ada' }
        nama = nama.replace("_", " ")
        self.users[username]={ 
            'nama': nama,
            'negara': negara,
            'password': password,
            'incoming': {},
            'outgoing': {}
            }
        tokenid = str(uuid.uuid4()) 
        self.sessions[tokenid]={ 'username': username, 'userdetail':self.users[username]}
        return { 'status': 'OK', 'tokenid': tokenid }

    def get_user(self,username):
        if (username not in self.users):
            return False
        return self.users[username]

#   ===================== Komunikasi dalam satu server =====================
    def addgroup(self, sessionid, usernamefrom, groupname):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        self.group[groupname]={
            'admin': usernamefrom,
            'members': [usernamefrom],
            'message':{}
        }
        return {'status': 'OK', 'message': 'Add group successful'}
    
    def joingroup(self, sessionid, usernamefrom, groupname):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if usernamefrom in self.group[groupname]['members']:
            return {'status': 'ERROR', 'message': 'User sudah dalam group'}
        self.group[groupname]['members'].append(usernamefrom)
        return {'status': 'OK', 'message': 'Add group successful'}
    
    def send_message(self,sessionid,username_from,username_dest,message):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)

        if (s_fr==False or s_to==False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        message = { 'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
        outqueue_sender = s_fr['outgoing']
        inqueue_receiver = s_to['incoming']
        try:	
            outqueue_sender[username_from].put(message)
        except KeyError:
            outqueue_sender[username_from]=Queue()
            outqueue_sender[username_from].put(message)
        try:
            inqueue_receiver[username_from].put(message)
        except KeyError:
            inqueue_receiver[username_from]=Queue()
            inqueue_receiver[username_from].put(message)
        return {'status': 'OK', 'message': 'Message Sent'}
    
    def send_group_message(self, sessionid, groupname, username_from, message):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        if s_fr is False:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        for username_dest in self.group[groupname]['members']:
            s_to = self.get_user(username_dest)
            if s_to is False:
                continue
            message = {'group': groupname,'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message}
            try:    
                self.group[groupname]['message'][username_from].put(message)
            except KeyError:
                self.group[groupname]['message'][username_from]=Queue()
                self.group[groupname]['message'][username_from].put(message)
            
            outqueue_sender = s_fr['outgoing']
            inqueue_receiver = s_to['incoming']
            try:    
                outqueue_sender[username_from].put(message)
            except KeyError:
                outqueue_sender[username_from]=Queue()
                outqueue_sender[username_from].put(message)
            try:
                inqueue_receiver[username_from].put(message)
            except KeyError:
                inqueue_receiver[username_from]=Queue()
                inqueue_receiver[username_from].put(message)
        return {'status': 'OK', 'message': 'Message Sent'}
    
    def get_inbox(self,username):
        s_fr = self.get_user(username)
        incoming = s_fr['incoming']
        msgs={}
        for users in incoming:
            msgs[users]=[]
            while not incoming[users].empty():
                msgs[users].append(s_fr['incoming'][users].get_nowait())
        return {'status': 'OK', 'messages': msgs}

    def send_file(self, sessionid, username_from, username_dest, filepath ,encoded_file):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)

        if s_fr is False or s_to is False:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        filename = os.path.basename(filepath)
        message = {
            'msg_from': s_fr['nama'],
            'msg_to': s_to['nama'],
            'file_name': filename,
            'file_content': encoded_file
        }

        outqueue_sender = s_fr['outgoing']
        inqueue_receiver = s_to['incoming']
        try:
            outqueue_sender[username_from].put(json.dumps(message))
        except KeyError:
            outqueue_sender[username_from] = Queue()
            outqueue_sender[username_from].put(json.dumps(message))
        try:
            inqueue_receiver[username_from].put(json.dumps(message))
        except KeyError:
            inqueue_receiver[username_from] = Queue()
            inqueue_receiver[username_from].put(json.dumps(message))
        
        # Simpan file ke folder dengan nama yang mencerminkan waktu pengiriman dan nama asli file
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        folder_name = f"{now}_{username_from}_{username_dest}_{filename}"
        folder_path = join(dirname(realpath(__file__)), 'files/')
        os.makedirs(folder_path, exist_ok=True)
        folder_path = join(folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        file_destination = os.path.join(folder_path, filename)
        if 'b' in encoded_file[0]:
            msg = encoded_file[2:-1]

            with open(file_destination, "wb") as fh:
                fh.write(base64.b64decode(msg))
        else:
            tail = encoded_file.split()
        
        return {'status': 'OK', 'message': 'File Sent'}

    def send_group_file(self, sessionid, username_from, groupname, filepath, encoded_file):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        if s_fr is False:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        filename = os.path.basename(filepath)
        for username_dest in self.group[groupname]['members']:
            s_to = self.get_user(username_dest)
            if s_to is False:
                continue
            message = {
                'group': groupname,
                'msg_from': s_fr['nama'],
                'msg_to': s_to['nama'],
                'file_name': filename,
                'file_content': encoded_file
            }

            try:    
                self.group[groupname]['message'][username_from].put(message)
            except KeyError:
                self.group[groupname]['message'][username_from]=Queue()
                self.group[groupname]['message'][username_from].put(message)
            
            outqueue_sender = s_fr['outgoing']
            inqueue_receiver = s_to['incoming']
            try:
                outqueue_sender[username_from].put(json.dumps(message))
            except KeyError:
                outqueue_sender[username_from] = Queue()
                outqueue_sender[username_from].put(json.dumps(message))
            try:
                inqueue_receiver[username_from].put(json.dumps(message))
            except KeyError:
                inqueue_receiver[username_from] = Queue()
                inqueue_receiver[username_from].put(json.dumps(message))
        
            # Simpan file ke folder dengan nama yang mencerminkan waktu pengiriman dan nama asli file
            now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            folder_name = f"{now}_{username_from}_{username_dest}_{filename}"
            folder_path = join(dirname(realpath(__file__)), 'files/')
            os.makedirs(folder_path, exist_ok=True)
            folder_path = join(folder_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            file_destination = os.path.join(folder_path, filename)
            if 'b' in encoded_file[0]:
                msg = encoded_file[2:-1]

                with open(file_destination, "wb") as fh:
                    fh.write(base64.b64decode(msg))
            else:
                tail = encoded_file.split()
        
        return {'status': 'OK', 'message': 'File Sent'}


#   ===================== Komunikasi dengan server lain =====================
    def add_realm(self, realm_id, realm_dest_address, realm_dest_port, data):
        j = data.split()
        j[0] = "recvrealm"
        data = ' '.join(j)
        data += "\r\n"
        if realm_id in self.realms:
            return {'status': 'ERROR', 'message': 'Realm sudah ada'}

        self.realms[realm_id] = RealmThreadCommunication(self, realm_dest_address, realm_dest_port)
        result = self.realms[realm_id].sendstring(data)
        return result

    def recv_realm(self, realm_id, realm_dest_address, realm_dest_port, data):
        self.realms[realm_id] = RealmThreadCommunication(self, realm_dest_address, realm_dest_port)
        return {'status':'OK'}

    def send_realm_message(self, sessionid, realm_id, username_from, username_dest, message, data):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if (s_fr==False or s_to==False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        message = { 'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
        self.realms[realm_id].put(message)
        
        j = data.split()
        j[0] = "recvrealmprivatemsg"
        j[1] = username_from
        data = ' '.join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {'status': 'OK', 'message': 'Message Sent to Realm'}
    
    def send_file_realm(self, sessionid, realm_id, username_from, username_dest, filepath, encoded_file, data):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if (s_fr==False or s_to==False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        
        filename = os.path.basename(filepath)
        message = {
            'msg_from': s_fr['nama'],
            'msg_to': s_to['nama'],
            'file_name': filename,
            'file_content': encoded_file
        }
        self.realms[realm_id].put(message)
        
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        folder_name = f"{now}_{username_from}_{username_dest}_{filename}"
        folder_path = join(dirname(realpath(__file__)), 'files/')
        os.makedirs(folder_path, exist_ok=True)
        folder_path = join(folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        file_destination = os.path.join(folder_path, filename)
        if 'b' in encoded_file[0]:
            msg = encoded_file[2:-1]

            with open(file_destination, "wb") as fh:
                fh.write(base64.b64decode(msg))
        else:
            tail = encoded_file.split()
        
        j = data.split()
        j[0] = "recvfilerealm"
        j[1] = username_from
        data = ' '.join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {'status': 'OK', 'message': 'File Sent to Realm'}
    
    def recv_file_realm(self, sessionid, realm_id, username_from, username_dest, filepath, encoded_file, data):
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if (s_fr==False or s_to==False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        
        filename = os.path.basename(filepath)
        message = {
            'msg_from': s_fr['nama'],
            'msg_to': s_to['nama'],
            'file_name': filename,
            'file_content': encoded_file
        }
        self.realms[realm_id].put(message)
        
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        folder_name = f"{now}_{username_from}_{username_dest}_{filename}"
        folder_path = join(dirname(realpath(__file__)), 'files/')
        os.makedirs(folder_path, exist_ok=True)
        folder_path = join(folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        file_destination = os.path.join(folder_path, filename)
        if 'b' in encoded_file[0]:
            msg = encoded_file[2:-1]

            with open(file_destination, "wb") as fh:
                fh.write(base64.b64decode(msg))
        else:
            tail = encoded_file.split()
        
        return {'status': 'OK', 'message': 'File Received to Realm'}

    def recv_realm_message(self, realm_id, username_from, username_dest, message, data):
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if (s_fr==False or s_to==False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        message = { 'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
        self.realms[realm_id].put(message)
        return {'status': 'OK', 'message': 'Message Sent to Realm'}

    def send_group_realm_message(self, sessionid, realm_id, username_from, usernames_to, message, data):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if realm_id not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
            self.realms[realm_id].put(message)
        
        j = data.split()
        j[0] = "recvrealmgroupmsg"
        j[1] = username_from
        data = ' '.join(j)
        data +="\r\n"
        self.realms[realm_id].sendstring(data)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}
    
    def send_group_file_realm(self, sessionid, realm_id, username_from, usernames_to, filepath, encoded_file, data):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)

        if (s_fr==False):
                return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
            
        filename = os.path.basename(filepath)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {
                'msg_from': s_fr['nama'],
                'msg_to': s_to['nama'],
                'file_name': filename,
                'file_content': encoded_file
            }
            self.realms[realm_id].put(message)
        
            now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            folder_name = f"{now}_{username_from}_{username_to}_{filename}"
            folder_path = join(dirname(realpath(__file__)), 'files/')
            os.makedirs(folder_path, exist_ok=True)
            folder_path = join(folder_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            file_destination = os.path.join(folder_path, filename)
            if 'b' in encoded_file[0]:
                msg = encoded_file[2:-1]

                with open(file_destination, "wb") as fh:
                    fh.write(base64.b64decode(msg))
            else:
                tail = encoded_file.split()
        
        j = data.split()
        j[0] = "recvgroupfilerealm"
        j[1] = username_from
        data = ' '.join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}

    def recv_group_file_realm(self, sessionid, realm_id, username_from, usernames_to, filepath, encoded_file, data):
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)

        if (s_fr==False):
                return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
            
        filename = os.path.basename(filepath)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {
                'msg_from': s_fr['nama'],
                'msg_to': s_to['nama'],
                'file_name': filename,
                'file_content': encoded_file
            }
            self.realms[realm_id].put(message)
        
            now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            folder_name = f"{now}_{username_from}_{username_to}_{filename}"
            folder_path = join(dirname(realpath(__file__)), 'files/')
            os.makedirs(folder_path, exist_ok=True)
            folder_path = join(folder_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            file_destination = os.path.join(folder_path, filename)
            if 'b' in encoded_file[0]:
                msg = encoded_file[2:-1]

                with open(file_destination, "wb") as fh:
                    fh.write(base64.b64decode(msg))
            else:
                tail = encoded_file.split()
        
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}

    def recv_group_realm_message(self, realm_id, username_from, usernames_to, message, data):
        if realm_id not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
            self.realms[realm_id].put(message)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}

    def get_realm_inbox(self, username,realmid):
        if (realmid not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username)
        result = self.realms[realmid].sendstring("getrealmchat {} {}\r\n".format(realmid, username))
        return result
    def get_realm_chat(self, realmid, username):
        s_fr = self.get_user(username)
        msgs = []
        while not self.realms[realmid].chat[s_fr['nama']].empty():
            msgs.append(self.realms[realmid].chat[s_fr['nama']].get_nowait())
        return {'status': 'OK', 'messages': msgs}
    def logout(self, sessionid):
        if (bool(self.sessions) == True):
            del self.sessions[sessionid]
            return {'status': 'OK'}
        else:
            return {'status': 'ERROR', 'message': 'Belum Login'}
    def info(self):
        return {'status': 'OK', 'message': self.sessions}

if __name__=="__main__":
    j = Chat()
    sesi = j.proses("auth messi surabaya")
    print(sesi)
    sesi2 = j.proses("auth henderson surabaya")
    tokenid = sesi['tokenid']
    # tokenid2 = sesi2['tokenid']
    print(j.proses("send {} henderson hello gimana kabarnya son " . format(tokenid)))
    # print(j.proses("send {} messi hello gimana kabarnya mess " . format(tokenid)))

    #print j.send_message(tokenid,'messi','henderson','hello son')
    #print j.send_message(tokenid,'henderson','messi','hello si')
    #print j.send_message(tokenid,'lineker','messi','hello si dari lineker')


    # print("isi mailbox dari messi")
    # print(j.get_inbox('messi'))
    print("isi mailbox dari henderson")
    print(j.get_inbox('henderson'))
```

## Implementasi Chat Flet (khusus Client dan Client Desktop):

**1. Implementasi Chat Flet untuk Client (secara umum):**

```
# chat-flet_sesudah_revisi.py


import flet as ft
import json
import os

# Placeholder for ChatClient class
class ChatClient:
    def __init__(self):
        pass
    
    def proses(self, command):
        # Implement the proses method
        pass
    
    def inbox(self):
        # Implement the inbox method
        pass
    
    def info(self):
        # Implement the info method
        pass

TARGET_IP = os.getenv("SERVER_IP") or "127.0.0.1"
TARGET_PORT = os.getenv("SERVER_PORT") or "8889"
ON_WEB = os.getenv("ONWEB") or "1"


class ChatList(ft.Container):
    def __init__(self, page, users, from_user):
        super().__init__()
        for value in users.values():
            print(value["username"])
        self.content = ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.icons.PERSON),
                    title=ft.Text(f"{value['username']}"),
                    on_click=lambda _: page.go(f"/private/{value['username']}"),
                )
                for value in users.values()
            ],
        )

        self.padding = ft.padding.symmetric(vertical=10)


class ChatRoom:
    def __init__(self, page, cc, from_user, to_user):
        self.chat = ft.TextField(
            label="Write a message...",
            autofocus=True,
            expand=True,
            on_submit=self.send_click,
        )
        self.lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
        self.send = ft.IconButton(
            icon=ft.icons.SEND_ROUNDED,
            tooltip="Send message",
            on_click=self.send_click,
        )
        self.file_picker = ft.FilePicker(on_result=self.upload_files, on_upload=self.upload_server)
        self.file_pick = ft.IconButton(
            icon=ft.icons.UPLOAD_FILE_ROUNDED,
            tooltip="Send file",
            on_click=self.on_pick_file,
        )
        self.page = page
        self.cc = cc
        self.from_user = from_user
        self.to_user = to_user
        self.page.pubsub.subscribe(self.on_chat)

    def on_pick_file(self, __e__):
        self.page.overlay.append(self.file_picker)
        self.page.update()
        self.file_picker.pick_files(allow_multiple=True)

    def send_click(self, __e__):
        if not self.chat.value:
            self.chat.error_text = "Please enter message"
            self.page.update()
        else:
            command = f"send {self.to_user} {self.chat.value}"
            server_call = self.cc.proses(command)
            self.lv.controls.append(ft.Text("To {}: {}".format(self.to_user, self.chat.value)))

            if "sent" in server_call:
                self.page.pubsub.send_all(self.chat.value)

            self.chat.value = ""
            self.chat.focus()
            self.page.update()

    def on_chat(self, message):
        check_inbox = json.loads(self.cc.inbox())
        self.lv.controls.append(ft.Text("From {}: {}".format(check_inbox[self.to_user][0]['msg_from'], check_inbox[self.to_user][0]['msg'])))
        self.page.update()

    # file picker and uploads
    def upload_files(self, e:ft.FilePickerResultEvent):
        upload_list = []
        if self.file_picker.result != None and self.file_picker.result.files != None:
            for f in self.file_picker.result.files:
                # print(self.page.get_upload_url(f.name, 600),)
                upload_list.append(
                    ft.FilePickerUploadFile(
                        f.name,
                        upload_url=self.page.get_upload_url(f.name, 600),
                    )
                )
            self.file_picker.upload(upload_list)
    
    def upload_server(self, e:ft.FilePickerUploadEvent):
        if(e.progress == 1):
            command = f"sendfile {self.to_user} app\\client\\upload\\{e.file_name}"
            print(command)
            server_call = self.cc.proses(command)
            print(server_call)
            self.lv.controls.append(ft.Text("To {}: Berhasil mengirim file {}".format(self.to_user, e.file_name)))

            if "sent" in server_call:
                self.page.pubsub.send_all(self.chat.value)

            self.chat.value = ""
            self.chat.focus()
            self.page.update()



def main(page):
    cc = ChatClient()
    page.title = "Chat App"
    is_login = False

    global login_dialog
    def login_dialog():
        nonlocal is_login
        global changeto_login
        global logouttologin
        global changeto_logout

        def changeto_register(e):
            page.dialog.title=ft.Text(
                "Welcome! Please Fill Bellow to register", style=ft.TextThemeStyle.TITLE_MEDIUM
            )
            if not username.value:
                page.dialog.actions=[
                    ft.ElevatedButton("Already have an account", on_click=changeto_login),
                    ft.ElevatedButton("Register", on_click=register_click)
                ]
            elif not password.value:
                page.dialog.actions=[
                    ft.ElevatedButton("Already have an account", on_click=changeto_login),
                    ft.ElevatedButton("Register", on_click=register_click)
                ]
            elif not name.value:
                page.dialog.actions=[
                    ft.ElevatedButton("Already have an account", on_click=changeto_login),
                    ft.ElevatedButton("Register", on_click=register_click)
                ]
            elif not country.value:
                page.dialog.actions=[
                    ft.ElevatedButton("Already have an account", on_click=changeto_login),
                    ft.ElevatedButton("Register", on_click=register_click)
                ]
            else:
                page.dialog.actions=[
                    ft.ElevatedButton("Already have an account", on_click=changeto_login),
                    ft.ElevatedButton("Register", on_click=changeto_login) # <---
                ]
            page.dialog.content=ft.Column([username, password,name,country], tight=True)
            page.update()
        
        def changeto_login(e):
            page.dialog.title=ft.Text(
                "Welcome! Please login", style=ft.TextThemeStyle.TITLE_MEDIUM
            )
            page.dialog.actions=[
                ft.ElevatedButton("Register Account", on_click=changeto_register),
                ft.ElevatedButton("Login", on_click=login_click)
            ]
            page.dialog.content=ft.Column([username, password], tight=True)

            page.update()


        page.dialog = ft.AlertDialog(
            open=not is_login,
            modal=True,
            title=ft.Text(
                "Welcome! Please login", style=ft.TextThemeStyle.TITLE_MEDIUM
            ),
            content=ft.Column([username, password], tight=True),
            actions=[
                ft.ElevatedButton("Register Account", on_click=changeto_register),
                ft.ElevatedButton("Login", on_click=login_click)
            ],
            actions_alignment="end",
        )
        
    def close_login_dialog():
        login_dialog.close()
        
    login_dialog()

    def register_click(__e__):
        if not username.value:
            username.error_text = "Please enter username"
            username.update()
        else :
            username.error_text = ""
            username.update()


        if not password.value:
            password.error_text = "Please enter password"
            password.update()
        else :
            password.error_text = ""
            password.update()
        
        if not name.value:
            name.error_text = "Please enter name"
            name.update()
        else :
            name.error_text = ""
            name.update()

        if not country.value:
            country.error_text = "Please enter country"
            country.update()
        else :
            country.error_text = ""
            country.update()

        if username.value != "" and password.value != "" and name.value != "" and country.value != "":
            login = cc.register(username.value, password.value, name.value, country.value)

            if "Error" in login:
                country.error_text = "Error When Register"
                country.update()

            else:
                username.value = ""
                password.value = ""
                name.value = ""
                country.value = ""
                username.error_text = ""
                password.error_text = ""
                name.error_text = ""
                country.error_text = ""
                page.update()
                changeto_login(None)
            page.update()

    def login_click(__e__):
        if not username.value:
            username.error_text = "Please enter username"
            username.update()
        else :
            username.error_text = ""
            username.update()


        if not password.value:
            password.error_text = "Please enter password"
            password.update()
        else :
            password.error_text = ""
            password.update()

        if username.value != "" and password.value != "":
            login = cc.login(username.value, password.value)

            if "Error" in login:
                username.error_text = "Username or Password does not match"
                password.error_text = "Username or Password does not match"
                username.update()

            else:
                close_login_dialog()
                menu_item_username.text = "welcome, " + username.value
                username.value = ""
                password.value = ""
                username.error_text = ""
                password.error_text = ""
                is_login = True
                page.dialog.open = False

            page.update()
    
    def logout_click(e):
        is_login = False
        cc.logout()
        login_dialog()
        page.update()

    username = ft.TextField(label="Username", autofocus=True)
    password = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        autofocus=True,
        on_submit=login_click,
    )
    name = ft.TextField(label="name", autofocus=True)
    country = ft.TextField(label="country", autofocus=True)

    global menu_item_username
    menu_item_username = ft.PopupMenuItem(text="")
    menu = ft.PopupMenuButton(
        items=[
            menu_item_username,
            ft.PopupMenuItem(
                icon=ft.icons.LOGOUT, text="Logout", on_click=logout_click
            ),
        ]
    )

    def route_change(__route__):
        troute = ft.TemplateRoute(page.route)
        page.views.clear()

        page.views.append(
            ft.View(
                "/",
                [
                    menu,
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.ListTile(
                                        leading=ft.Icon(ft.icons.PERSON),
                                        title=ft.Text("Private Chat"),
                                        on_click=lambda _: page.go("/private"),
                                    ),
                                    ft.ListTile(
                                        leading=ft.Icon(ft.icons.GROUP),
                                        title=ft.Text("Group Chat"),
                                        on_click=lambda _: page.go("/group"),
                                    ),
                                ],
                            ),
                            padding=ft.padding.symmetric(vertical=10),
                        )
                    ),
                ],
            )
        )

        if troute.match("/private"):
            page.views.append(
                ft.View(
                    "/private",
                    [
                        ft.AppBar(title=ft.Text("Private Chat"), actions=[menu]),
                        ft.Card(
                            content=ChatList(page, cc.info(), cc.username),
                        ),
                    ],
                )
            )

        elif troute.match("/private/:username"):
            cr = ChatRoom(page, cc, cc.username, troute.username)
            
            file_picker = ft.FilePicker()
            page.overlay.append(file_picker)
            page.update()

            page.views.append(
                ft.View(
                    f"/private/{troute.username}",
                    [
                        ft.AppBar(
                            title=ft.Text(f"Private Chat with {troute.username}"),
                            actions=[menu],
                        ),
                        cr.lv,
                        ft.Row([cr.chat, cr.send, cr.file_pick]),
                    ],
                )
            )

        elif troute.match("/group"):
            page.views.append(
                ft.View(
                    "/group",
                    [
                        ft.AppBar(title=ft.Text("Group Chat"), actions=[menu]),
                        # lv,
                        # ft.Row([chat, send]),
                    ],
                )
            )
        page.update()

    def view_pop(__view__):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)



if __name__=='__main__':
    if (ON_WEB=="1"):
        ft.app(target=main,view=ft.WEB_BROWSER,port=8550)
    else:
        ft.app(target=main)
```

**2. Implementasi Chat Flet untuk Client Desktop:**

```
# chat-flet_sesudah_revisi.py

import flet as ft
import os

# Placeholder for ChatClient class
class ChatClient:
    def __init__(self):
        pass
    
    def proses(self, command):
        # Implement the proses method
        pass
    
    def inbox(self):
        # Implement the inbox method
        pass
    
    def info(self):
        # Implement the info method
        pass

TARGET_IP = os.getenv("SERVER_IP") or "127.0.0.1"
TARGET_PORT = os.getenv("SERVER_PORT") or "8889"
ON_WEB = os.getenv("ONWEB") or "0"


def main(page):
    def btn_click(e):
        if not cmd.value:
            cmd.error_text = "masukkan command"
            page.update()
        else:
            txt = cmd.value
            lv.controls.append(ft.Text(f"command: {txt}"))
            txt = cc.proses(txt)
            lv.controls.append(ft.Text(f"result {cc.tokenid}: {txt}"))
            cmd.value=""
            page.update()

    cc = ChatClient()


    lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
    cmd = ft.TextField(label="Your command")

    page.add(lv)
    page.add(cmd, ft.ElevatedButton("Send", on_click=btn_click))


if __name__=='__main__':
    if (ON_WEB=="1"):
        ft.app(target=main,view=ft.WEB_BROWSER,port=8550)
    else:
        ft.app(target=main)
```

## Implementasi Chat CLI:

**1. Implementasi Chat CLI untuk Client:**

```
# chat-cli.py

import socket
import json
import base64
import json
import os
from chat import Chat

TARGET_IP = "127.0.0.1"
TARGET_PORT = 8889


class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (TARGET_IP, TARGET_PORT)
        self.sock.connect(self.server_address)
        self.tokenid = ""
        self.username = ""

    def proses(self, cmdline):
        j = cmdline.split(" ")
        try:
            command = j[0].strip()
            if command == "auth":
                username = j[1].strip()
                password = j[2].strip()
                return self.login(username, password)
            if command == "register":
                username = j[1].strip()
                password = j[2].strip()
                nama = j[3].strip()
                negara = j[4].strip()
                return self.register(username, password, nama, negara)
            elif command == "addrealm":
                realmid = j[1].strip()
                realm_address = j[2].strip()
                realm_port = j[3].strip()
                return self.add_realm(realmid, realm_address, realm_port)
            elif command == "send":
                usernameto = j[1].strip()
                message = ""
                for w in j[2:]:
                    message = "{} {}".format(message, w)
                return self.send_message(usernameto, message)
            elif command == "sendfile":
                usernameto = j[1].strip()
                filepath = j[2].strip()
                return self.send_file(usernameto, filepath)
            elif command == "sendgroup":
                usernamesto = j[1].strip()
                message = ""
                for w in j[2:]:
                    message = "{} {}".format(message, w)
                return self.send_group_message(usernamesto, message)
            elif command == "sendgroupfile":
                usernamesto = j[1].strip()
                filepath = j[2].strip()
                return self.send_group_file(usernamesto, filepath)
            elif command == "sendprivaterealm":
                realmid = j[1].strip()
                username_to = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}".format(message, w)
                return self.send_realm_message(realmid, username_to, message)
            elif command == "sendfilerealm":
                realmid = j[1].strip()
                usernameto = j[2].strip()
                filepath = j[3].strip()
                return self.send_file_realm(realmid, usernameto, filepath)
            elif command == "sendgrouprealm":
                realmid = j[1].strip()
                usernamesto = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}".format(message, w)
                return self.send_group_realm_message(realmid, usernamesto, message)
            elif command == "sendgroupfilerealm":
                realmid = j[1].strip()
                usernamesto = j[2].strip()
                filepath = j[3].strip()
                return self.send_group_file_realm(realmid, usernamesto, filepath)
            elif command == "inbox":
                return self.inbox()
            elif command == "getrealminbox":
                realmid = j[1].strip()
                return self.realm_inbox(realmid)
            elif command == "logout":
                return self.logout()
            elif command == "info":
                return self.info()
            else:
                return "*Maaf, command tidak benar"
        except IndexError:
            return "-Maaf, command tidak benar"

    def sendstring(self, string):
        try:
            self.sock.sendall(string.encode())
            receivemsg = ""
            while True:
                data = self.sock.recv(1024)
                print("diterima dari server", data)
                if data:
                    receivemsg = "{}{}".format(
                        receivemsg, data.decode()
                    )  # data harus didecode agar dapat di operasikan dalam bentuk string
                    if receivemsg[-4:] == "\r\n\r\n":
                        print("end of string")
                        return json.loads(receivemsg)
        except:
            self.sock.close()
            return {"status": "ERROR", "message": "Gagal"}

    def login(self, username, password):
        string = "auth {} {} \r\n".format(username, password)
        result = self.sendstring(string)
        if result["status"] == "OK":
            self.tokenid = result["tokenid"]
            self.username = username
            return "username {} logged in, token {} ".format(username, self.tokenid)
        else:
            return "Error, {}".format(result["message"])

    def register(self, username, password, nama, negara):
        string = "register {} {} {} {}\r\n".format(username, password, nama, negara)
        result = self.sendstring(string)
        if result["status"] == "OK":
            self.tokenid = result["tokenid"]
            return "username {} register in, token {} ".format(username, self.tokenid)
        else:
            return "Error, {}".format(result["message"])

    def add_realm(self, realmid, realm_address, realm_port):
        if self.tokenid == "":
            return "Error, not authorized"
        string = "addrealm {} {} {} \r\n".format(realmid, realm_address, realm_port)
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "Realm {} added".format(realmid)
        else:
            return "Error, {}".format(result["message"])

    def send_message(self, usernameto="xxx", message="xxx"):
        if self.tokenid == "":
            return "Error, not authorized"
        string = "send {} {} {} \r\n".format(self.tokenid, usernameto, message)
        print(string)
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "message sent to {}".format(usernameto)
        else:
            return "Error, {}".format(result["message"])

    def send_file(self, usernameto="xxx", filepath="xxx"):
        if self.tokenid == "":
            return "Error, not authorized"

        if not os.path.exists(filepath):
            return {"status": "ERROR", "message": "File not found"}

        with open(filepath, "rb") as file:
            file_content = file.read()
            encoded_content = base64.b64encode(
                file_content
            )  # Decode byte-string to UTF-8 string
        string = "sendfile {} {} {} {}\r\n".format(
            self.tokenid, usernameto, filepath, encoded_content
        )

        result = self.sendstring(string)
        if result["status"] == "OK":
            return "file sent to {}".format(usernameto)
        else:
            return "Error, {}".format(result["message"])

    def send_realm_message(self, realmid, username_to, message):
        if self.tokenid == "":
            return "Error, not authorized"
        string = "sendprivaterealm {} {} {} {}\r\n".format(
            self.tokenid, realmid, username_to, message
        )
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "Message sent to realm {}".format(realmid)
        else:
            return "Error, {}".format(result["message"])

    def send_file_realm(self, realmid, usernameto, filepath):
        if self.tokenid == "":
            return "Error, not authorized"
        if not os.path.exists(filepath):
            return {"status": "ERROR", "message": "File not found"}

        with open(filepath, "rb") as file:
            file_content = file.read()
            encoded_content = base64.b64encode(
                file_content
            )  # Decode byte-string to UTF-8 string
        string = "sendfilerealm {} {} {} {} {}\r\n".format(
            self.tokenid, realmid, usernameto, filepath, encoded_content
        )
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "File sent to realm {}".format(realmid)
        else:
            return "Error, {}".format(result["message"])

    def send_group_message(self, usernames_to="xxx", message="xxx"):
        if self.tokenid == "":
            return "Error, not authorized"
        string = "sendgroup {} {} {} \r\n".format(self.tokenid, usernames_to, message)
        print(string)
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "message sent to {}".format(usernames_to)
        else:
            return "Error, {}".format(result["message"])

    def send_group_file(self, usernames_to="xxx", filepath="xxx"):
        if self.tokenid == "":
            return "Error, not authorized"

        if not os.path.exists(filepath):
            return {"status": "ERROR", "message": "File not found"}

        with open(filepath, "rb") as file:
            file_content = file.read()
            encoded_content = base64.b64encode(
                file_content
            )  # Decode byte-string to UTF-8 string

        string = "sendgroupfile {} {} {} {}\r\n".format(
            self.tokenid, usernames_to, filepath, encoded_content
        )

        result = self.sendstring(string)
        if result["status"] == "OK":
            return "file sent to {}".format(usernames_to)
        else:
            return "Error, {}".format(result["message"])

    def send_group_realm_message(self, realmid, usernames_to, message):
        if self.tokenid == "":
            return "Error, not authorized"
        string = "sendgrouprealm {} {} {} {} \r\n".format(
            self.tokenid, realmid, usernames_to, message
        )

        result = self.sendstring(string)
        if result["status"] == "OK":
            return "message sent to group {} in realm {}".format(usernames_to, realmid)
        else:
            return "Error {}".format(result["message"])

    def send_group_file_realm(self, realmid, usernames_to, filepath):
        if self.tokenid == "":
            return "Error, not authorized"

        if not os.path.exists(filepath):
            return {"status": "ERROR", "message": "File not found"}

        with open(filepath, "rb") as file:
            file_content = file.read()
            encoded_content = base64.b64encode(
                file_content
            )  # Decode byte-string to UTF-8 string
        string = "sendgroupfilerealm {} {} {} {} {}\r\n".format(
            self.tokenid, realmid, usernames_to, filepath, encoded_content
        )

        result = self.sendstring(string)
        if result["status"] == "OK":
            return "file sent to group {} in realm {}".format(usernames_to, realmid)
        else:
            return "Error {}".format(result["message"])

    def inbox(self):
        if self.tokenid == "":
            return "Error, not authorized"
        string = "inbox {} \r\n".format(self.tokenid)
        result = self.sendstring(string)
        if result["status"] == "OK":
            return "{}".format(json.dumps(result["messages"]))
        else:
            return "Error, {}".format(result["message"])

    def realm_inbox(self, realmid):
        if self.tokenid == "":
            return "Error, not authorized"
        string = "getrealminbox {} {} \r\n".format(self.tokenid, realmid)
        print("Sending: " + string)
        result = self.sendstring(string)
        print("Received: " + str(result))
        if result["status"] == "OK":
            return "Message received from realm {}: {}".format(
                realmid, result["messages"]
            )
        else:
            return "Error, {}".format(result["message"])

    def logout(self):
        string = "logout \r\n"
        result = self.sendstring(string)
        if result["status"] == "OK":
            self.tokenid = ""
            return "Logout Berhasil"
        else:
            return "Error, {}".format(result["message"])

    def info(self):
        string = "info {} \r\n"
        result = self.sendstring(string)
        if result["status"] == "OK":
            return result["message"]


if __name__ == "__main__":
    cc = ChatClient()
    c = Chat()
    while True:
        print("\n")
        print(
            "List User: "
            + str(c.users.keys())
            + " dan Passwordnya: "
            + str(c.users["messi"]["password"])
            + ", "
            + str(c.users["henderson"]["password"])
            + ", "
            + str(c.users["lineker"]["password"])
        )
        print(
            """Command:\n
        1. Login: auth [username] [password]\n
        2. Register: register [username] [password] [nama (gunakan "_" untuk seperator) ] [negara]\n
        3. Menambah realm: addrealm [nama_realm] [address] [port]\n
        4. Mengirim pesan: send [username to] [message]\n
        5. Mengirim file: sendfile [username to] [filename]\n
        6. Mengirim pesan ke realm: sendrealm [name_realm] [username to] [message]\n
        7. Mengirim file ke realm: sendfilerealm [name_realm] [username to] [filename]\n
        8. Mengirim pesan ke group: sendgroup [usernames to] [message]\n
        9. Mengirim file ke group: sendgroupfile [usernames to] [filename]\n
        10. Mengirim pesan ke group realm: sendgrouprealm [name_realm] [usernames to] [message]\n
        11. Mengirim file ke group realm: sendgroupfilerealm [name_realm] [usernames to] [filename]\n
        12. Melihat pesan: inbox\n
        13. Melihat pesan realm: realminbox [nama_realm]\n
        14. Logout: logout\n
        15. Melihat user yang aktif: info\n"""
        )
        cmdline = input("Command {}:".format(cc.tokenid))
        print(cc.proses(cmdline))
```

**2. Implementasi Chat CLI untuk Client Desktop:**

```
# chat-cli.py

import socket
import os
import json

TARGET_IP = os.getenv("SERVER_IP") or "127.0.0.1"
TARGET_PORT = os.getenv("SERVER_PORT") or "8889"


class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(TARGET_IP)
        print(TARGET_PORT)
        self.server_address = (TARGET_IP,int(TARGET_PORT))
        self.sock.connect(self.server_address)
        self.tokenid=""
    def proses(self,cmdline):
        j=cmdline.split(" ")
        try:
            command=j[0].strip()
            if (command=='auth'):
                username=j[1].strip()
                password=j[2].strip()
                return self.login(username,password)
            elif (command=='send'):
                usernameto = j[1].strip()
                message=""
                for w in j[2:]:
                   message="{} {}" . format(message,w)
                return self.sendmessage(usernameto,message)
            elif (command=='inbox'):
                return self.inbox()
            else:
                return "*Maaf, command tidak benar"
        except IndexError:
                return "-Maaf, command tidak benar"
    def sendstring(self,string):
        try:
            self.sock.sendall(string.encode())
            receivemsg = ""
            while True:
                data = self.sock.recv(64)
                print("diterima dari server",data)
                if (data):
                    receivemsg = "{}{}" . format(receivemsg,data.decode())  #data harus didecode agar dapat di operasikan dalam bentuk string
                    if receivemsg[-4:]=='\r\n\r\n':
                        print("end of string")
                        return json.loads(receivemsg)
        except:
            self.sock.close()
            return { 'status' : 'ERROR', 'message' : 'Gagal'}
    def login(self,username,password):
        string="auth {} {} \r\n" . format(username,password)
        result = self.sendstring(string)
        if result['status']=='OK':
            self.tokenid=result['tokenid']
            return "username {} logged in, token {} " .format(username,self.tokenid)
        else:
            return "Error, {}" . format(result['message'])
    def sendmessage(self,usernameto="xxx",message="xxx"):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="send {} {} {} \r\n" . format(self.tokenid,usernameto,message)
        print(string)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "message sent to {}" . format(usernameto)
        else:
            return "Error, {}" . format(result['message'])
    def inbox(self):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="inbox {} \r\n" . format(self.tokenid)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "{}" . format(json.dumps(result['messages']))
        else:
            return "Error, {}" . format(result['message'])



if __name__=="__main__":
    cc = ChatClient()
    while True:
        cmdline = input("Command {}:" . format(cc.tokenid))
        print(cc.proses(cmdline))
```

**3. Implementasi Chat CLI untuk Server:**

```
# chat-cli.py

import socket
import json
import base64
import json
import os
from chat import Chat
TARGET_IP = "127.0.0.1"
TARGET_PORT = 8889

class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (TARGET_IP,TARGET_PORT)
        self.sock.connect(self.server_address)
        self.tokenid=""
    def proses(self,cmdline):
        j=cmdline.split(" ")
        try:
            command=j[0].strip()
            if (command=='auth'):
                username=j[1].strip()
                password=j[2].strip()
                return self.login(username,password)
            if (command=='register'):
                username=j[1].strip()
                password=j[2].strip()
                nama=j[3].strip()
                negara=j[4].strip()
                return self.register(username, password, nama, negara)
            elif (command=='addrealm'):
                realmid = j[1].strip()
                realm_address = j[2].strip()
                realm_port = j[3].strip()
                return self.add_realm(realmid, realm_address, realm_port)
            elif (command=='addgroup'):
                groupname = j[1].strip()
                return self.add_group(groupname)
            elif (command=='joingroup'):
                groupname = j[1].strip()
                return self.join_group(groupname)
            elif (command=='send'):
                usernameto = j[1].strip()
                message=""
                for w in j[2:]:
                    message="{} {}" . format(message,w)
                return self.send_message(usernameto,message)
            elif (command=='sendfile'):
                usernameto = j[1].strip()
                filepath = j[2].strip()
                return self.send_file(usernameto,filepath)
            elif (command=='sendgroup'):
                groupname = j[1].strip()
                message=""
                for w in j[2:]:
                    message="{} {}" . format(message,w)
                return self.send_group_message(groupname,message)
            elif (command=='sendgroupfile'):
                groupname = j[1].strip()
                filepath = j[2].strip()
                return self.send_group_file(groupname,filepath)
            elif (command == 'sendprivaterealm'):
                realmid = j[1].strip()
                username_to = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}".format(message, w)
                return self.send_realm_message(realmid, username_to, message)
            elif (command=='sendfilerealm'):
                realmid = j[1].strip()
                usernameto = j[2].strip()
                filepath = j[3].strip()
                return self.send_file_realm(realmid, usernameto,filepath)
            elif (command=='sendgrouprealm'):
                realmid = j[1].strip()
                usernamesto = j[2].strip()
                message=""
                for w in j[3:]:
                    message="{} {}" . format(message,w)
                return self.send_group_realm_message(realmid, usernamesto,message)
            elif (command=='sendgroupfilerealm'):
                realmid = j[1].strip()
                usernamesto = j[2].strip()
                filepath = j[3].strip()
                return self.send_group_file_realm(realmid, usernamesto,filepath)
            elif (command=='inbox'):
                return self.inbox()
            elif (command == 'getrealminbox'):
                realmid = j[1].strip()
                return self.realm_inbox(realmid)
            elif (command=='logout'):
                return self.logout()
            elif (command=='info'):
                return self.info()
            else:
                return "*Maaf, command tidak benar"
        except IndexError:
            return "-Maaf, command tidak benar"

    def sendstring(self,string):
        try:
            self.sock.sendall(string.encode())
            receivemsg = ""
            while True:
                data = self.sock.recv(1024)
                print("diterima dari server",data)
                if (data):
                    receivemsg = "{}{}" . format(receivemsg,data.decode())  #data harus didecode agar dapat di operasikan dalam bentuk string
                    if receivemsg[-4:]=='\r\n\r\n':
                        print("end of string")
                        return json.loads(receivemsg)
        except:
            self.sock.close()
            return { 'status' : 'ERROR', 'message' : 'Gagal'}

    def login(self,username,password):
        string="auth {} {} \r\n" . format(username,password)
        result = self.sendstring(string)
        if result['status']=='OK':
            self.tokenid=result['tokenid']
            return "username {} logged in, token {} " .format(username,self.tokenid)
        else:
            return "Error, {}" . format(result['message'])
    
    def register(self,username,password, nama, negara):
        string="register {} {} {} {}\r\n" . format(username,password, nama, negara)
        result = self.sendstring(string)
        if result['status']=='OK':
            self.tokenid=result['tokenid']
            return "username {} register in, token {} " .format(username,self.tokenid)
        else:
            return "Error, {}" . format(result['message'])

    def add_realm(self, realmid, realm_address, realm_port):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="addrealm {} {} {} \r\n" . format(realmid, realm_address, realm_port)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "Realm {} added" . format(realmid)
        else:
            return "Error, {}" . format(result['message'])

    def add_group(self, groupname):
        string="addgroup {} {} \r\n".format(self.tokenid, groupname)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "Group {} added".format(groupname)
    
    def join_group(self, groupname):
        string="joingroup {} {} \r\n".format(self.tokenid, groupname)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "Group {} added".format(groupname)

    def send_message(self,usernameto="xxx",message="xxx"):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="send {} {} {} \r\n" . format(self.tokenid,usernameto,message)
        print(string)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "message sent to {}" . format(usernameto)
        else:
            return "Error, {}" . format(result['message'])
        
    def send_file(self, usernameto="xxx", filepath="xxx"):
        if (self.tokenid==""):
            return "Error, not authorized"

        if not os.path.exists(filepath):
            return {'status': 'ERROR', 'message': 'File not found'}
        
        with open(filepath, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)  # Decode byte-string to UTF-8 string
        string="sendfile {} {} {} {}\r\n" . format(self.tokenid,usernameto,filepath,encoded_content)

        result = self.sendstring(string)
        if result['status']=='OK':
            return "file sent to {}" . format(usernameto)
        else:
            return "Error, {}" . format(result['message'])

    def send_realm_message(self, realmid, username_to, message):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="sendprivaterealm {} {} {} {}\r\n" . format(self.tokenid, realmid, username_to, message)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "Message sent to realm {}".format(realmid)
        else:
            return "Error, {}".format(result['message'])
        
    def send_file_realm(self, realmid, usernameto, filepath):
        if (self.tokenid==""):
            return "Error, not authorized"
        if not os.path.exists(filepath):
            return {'status': 'ERROR', 'message': 'File not found'}
        
        with open(filepath, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)  # Decode byte-string to UTF-8 string
        string="sendfilerealm {} {} {} {} {}\r\n" . format(self.tokenid, realmid, usernameto, filepath, encoded_content)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "File sent to realm {}".format(realmid)
        else:
            return "Error, {}".format(result['message'])

    def send_group_message(self,groupname="xxx",message="xxx"):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="sendgroup {} {} {} \r\n" . format(self.tokenid,groupname,message)
        print(string)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "message sent to {}" . format(groupname)
        else:
            return "Error, {}" . format(result['message'])
        
    def send_group_file(self, groupname="xxx", filepath="xxx"):
        if (self.tokenid==""):
            return "Error, not authorized"
        
        if not os.path.exists(filepath):
            return {'status': 'ERROR', 'message': 'File not found'}
        
        with open(filepath, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)  # Decode byte-string to UTF-8 string

        string="sendgroupfile {} {} {} {}\r\n" . format(self.tokenid,groupname,filepath, encoded_content)

        result = self.sendstring(string)
        if result['status']=='OK':
            return "file sent to {}" . format(groupname)
        else:
            return "Error, {}" . format(result['message'])

    def send_group_realm_message(self, realmid, usernames_to, message):
        if self.tokenid=="":
            return "Error, not authorized"
        string="sendgrouprealm {} {} {} {} \r\n" . format(self.tokenid, realmid, usernames_to, message)

        result = self.sendstring(string)
        if result['status']=='OK':
            return "message sent to group {} in realm {}" .format(usernames_to, realmid)
        else:
            return "Error {}".format(result['message'])
        
    def send_group_file_realm(self, realmid, usernames_to, filepath):
        if self.tokenid=="":
            return "Error, not authorized"

        if not os.path.exists(filepath):
            return {'status': 'ERROR', 'message': 'File not found'}
        
        with open(filepath, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)  # Decode byte-string to UTF-8 string
        string="sendgroupfilerealm {} {} {} {} {}\r\n" . format(self.tokenid, realmid, usernames_to, filepath, encoded_content)

        result = self.sendstring(string)
        if result['status']=='OK':
            return "file sent to group {} in realm {}" .format(usernames_to, realmid)
        else:
            return "Error {}".format(result['message'])

    def inbox(self):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="inbox {} \r\n" . format(self.tokenid)
        result = self.sendstring(string)
        if result['status']=='OK':
            return "{}" . format(json.dumps(result['messages']))
        else:
            return "Error, {}" . format(result['message'])

    def realm_inbox(self, realmid):
        if (self.tokenid==""):
            return "Error, not authorized"
        string="getrealminbox {} {} \r\n" . format(self.tokenid, realmid)
        print("Sending: " + string)
        result = self.sendstring(string)
        print("Received: " + str(result))
        if result['status']=='OK':
            return "Message received from realm {}: {}".format(realmid, result['messages'])
        else:
            return "Error, {}".format(result['message'])
    
    def logout(self):
        string="logout {}\r\n".format(self.tokenid)
        result = self.sendstring(string)
        if result['status']=='OK':
            self.tokenid=""
            return "Logout Berhasil"
        else:
            return "Error, {}" . format(result['message'])

    def info(self):
        string="info \r\n"
        result = self.sendstring(string)
        list_user_aktif="User yang Aktif:\n"
        if result['status']=='OK':
            list_user_aktif += f"{result['message']}"
        return list_user_aktif

if __name__=="__main__":
    cc = ChatClient()
    c = Chat()
    while True:
        print("\n")
        print("List User: " + str(c.users.keys()) + " dan Passwordnya: " + str(c.users['messi']['password']) + ", " + str(c.users['henderson']['password']) + ", " + str(c.users['lineker']['password']))
        print("""Command:\n
        1. Login: auth [username] [password]\n
        2. Register: register [username] [password] [nama (gunakan "_" untuk seperator) ] [negara]\n
        3. Menambah realm: addrealm [nama_realm] [address] [port]\n
        4. Mengirim pesan: send [username to] [message]\n
        5. Mengirim file: senfile [username to] [filename]\n
        6. Mengirim pesan ke realm: sendprivaterealm [name_realm] [username to] [message]\n
        7. Mengirim file ke realm: sendfilerealm [name_realm] [username to] [filename]\n
        8. Mengirim pesan ke group: sendgroup [usernames to] [message]\n
        9. Mengirim file ke group: sendgroupfile [usernames to] [filename]\n
        10. Mengirim pesan ke group realm: sendgrouprealm [name_realm] [usernames to] [message]\n
        11. Mengirim file ke group realm: sendgroupfilerealm [name_realm] [usernames to] [filename]\n
        12. Melihat pesan: inbox\n
        13. Melihat pesan realm: realminbox [nama_realm]\n
        14. Logout: logout\n
        15. Melihat user yang aktif: info\n""")
        cmdline = input("Command {}:" . format(cc.tokenid))
        print(cc.proses(cmdline))
```

## Implementasi lainnya:

**1. Implementasi `run.sh` (khusus Client Desktop):**

```
SERVER_IP=127.0.0.1
SERVER_PORT=8889
export SERVER_IP SERVER_PORT
virtualenv venv
source venv/Scripts/activate
pip3 install -r requirements.txt
python3 chat-flet.py
deactivate
```

**2. Implementasi Thread Chat (khusus Server):**

```
# server_thread_chat.py

from socket import *
import socket
import threading
import json
import logging
from chat import Chat

chatserver = Chat()

class ProcessTheClient(threading.Thread):
	def __init__(self, connection, address):
		self.connection = connection
		self.address = address
		threading.Thread.__init__(self)

	def run(self):
		rcv=""
		while True:
			data = self.connection.recv(2048)
			if data:
				d = data.decode()
				rcv=rcv+d
				if rcv[-2:]=='\r\n':
					#end of command, proses string
					logging.warning("data dari client: {}" . format(rcv))
					hasil = json.dumps(chatserver.proses(rcv))
					hasil=hasil+"\r\n\r\n"
					logging.warning("balas ke  client: {}" . format(hasil))
					self.connection.sendall(hasil.encode())
					rcv=""
			else:
				break
		self.connection.close()

class Server(threading.Thread):
	def __init__(self):
		self.the_clients = []
		self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		threading.Thread.__init__(self)

	def run(self):
		self.my_socket.bind(('0.0.0.0',8889))
		self.my_socket.listen(1)
		while True:
			self.connection, self.client_address = self.my_socket.accept()
			logging.warning("connection from {}" . format(self.client_address))
			
			clt = ProcessTheClient(self.connection, self.client_address)
			clt.start()
			self.the_clients.append(clt)
	

def main():
    print("Server is running...")
    svr = Server()
    svr.start()

if __name__=="__main__":
	main()
```

**3. Implementasi `requirements.txt` (khusus Client dan Client Desktop):**

```
requests
uuid
flet
```

**4. Implementasi `.gitignore` (secara umum):**

```
__pycache__
```

**5. Implementasi `docker-compose.yml` (secara umum):**

```
version: '3.9'
services:
  chatserver:
    image: python:3.11.3-alpine3.17 
    restart: unless-stopped
    volumes:
    - ./app/server:/app
    environment: 
    - SERVER_IP=0.0.0.0
    - SERVER_PORT=8889
    working_dir: /app
    ports:
    - 8889:8889
    command:
    - /bin/sh
    - -c
    - 'cd /app && pip3 install -r requirements.txt && python3 server_thread_chat.py'
    networks:
      - progjarnet
  chatclient:
    image: python:3.11.3-alpine3.17 
    restart: unless-stopped
    environment:
      - SERVER_IP=chatserver
      - SERVER_PORT=8889
      - ONWEB=1
    working_dir: /app
    ports:
    - 8550:8550
    volumes:
    - ./app/client:/app
    command:
    - /bin/sh
    - -c
    - 'cd /app && pip3 install -r requirements.txt && python3 chat-flet.py'
    depends_on:
    - chatserver
#    deploy:
#      mode: replicated
#      replicas: 1
    networks:
      - progjarnet
networks:
  progjarnet:
    ipam:
      config:
        - subnet: 172.222.221.0/24
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

Tampilan saat mendaftar:

<img width="414" alt="image" src="https://github.com/adrianazizsantoso/chatProtocol/assets/115202624/0e7f868f-dd30-4966-8864-62332b627f32">

Tampilan saat login:

<img width="414" alt="image" src="https://github.com/adrianazizsantoso/chatProtocol/assets/115202624/4bab73c9-1e66-428d-8d26-0c62e16fff79">

Tampilan saat chatting:

<img width="414" alt="image" src="https://github.com/adrianazizsantoso/chatProtocol/assets/115202624/f4d4b963-06f1-455e-ae9f-1e62359b982c">

## IP Address dan Port Server:
- IP Address Server: 127.0.0.1
- Port Server: 8889

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

Dengan arsitektur ini, setiap server chat lokal dapat saling bertukar pesan melalui server gateway, sementara pengguna dapat berinteraksi dengan antarmuka chat yang konsisten di berbagai platform. Inilah kodingan Flet yang digunakan pada tugas akhir “Chat Protocol” ini:

```
import flet as ft

ACCOUNTS = {
    'test': '12345678',
    'user': 'password'
}

class Message():
    def __init__(self, user: str, text: str, message_type: str):
        self.user = user
        self.text = text
        self.message_type = message_type

class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        self.vertical_alignment = ft.CrossAxisAlignment.START
        self.controls=[
                ft.CircleAvatar(
                    content=ft.Text(self.get_initials(message.user)),
                    color=ft.colors.WHITE,
                    bgcolor=self.get_avatar_color(message.user),
                ),
                ft.Column(
                    [
                        ft.Text(message.user, weight="bold"),
                        ft.Text(message.text, selectable=True),
                    ],
                    tight=True,
                    spacing=5,
                ),
            ]

    def get_initials(self, user_name: str):
        return user_name[:1].capitalize()

    def get_avatar_color(self, user_name: str):
        colors_lookup = [
            ft.colors.AMBER,
            ft.colors.BLUE,
            ft.colors.BROWN,
            ft.colors.CYAN,
            ft.colors.GREEN,
            ft.colors.INDIGO,
            ft.colors.LIME,
            ft.colors.ORANGE,
            ft.colors.PINK,
            ft.colors.PURPLE,
            ft.colors.RED,
            ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]

def main(page: ft.Page):
    content = None

    def send_message_click(e):
        page.pubsub.send_all(Message(user=page.session.get('username'), text=new_message.value, message_type="chat_message"))
        new_message.value = ""
        page.update()

    def join_click(e):
        if not username.value:
            username.error_text = "Username cannot be blank!"
            username.update()
        elif username.value not in ACCOUNTS.keys():
            username.error_text = 'User does not exist!'
            username.update()
        elif password.value != ACCOUNTS[username.value]:
            password.error_text = 'Incorrect password'
            password.update()
        else:
            page.session.set("username", username.value)
            name_dialog.open = False
            page.pubsub.send_all(Message(user=username.value, text=f"{username.value} has joined the chat.", message_type="login_message"))
            content.visible = True
            page.update()
            
    username = ft.TextField(label="Enter your user name")
    password = ft.TextField(label="Enter your password")

    name_dialog = ft.AlertDialog(
        open=True,
        modal=True,
        title=ft.Text("Welcome!"),
        content=ft.Column([username, password], tight=True),
        actions=[ft.ElevatedButton(text="Join chat", on_click=join_click)],
        actions_alignment="end",
    )

    page.overlay.append(name_dialog)

    # Chat messages
    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    # A new message entry form
    new_message = ft.TextField(
        hint_text="Write a message...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        filled=True,
        expand=True,
        on_submit=send_message_click,
    )

    tab = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(icon=ft.icons.PERSON),
            ft.Tab(icon=ft.icons.GROUP),
        ],
        expand=True
    )

    content = ft.Row(
        expand=True,
        visible=False,
        controls=[
            ft.Column(
                controls=[
                    ft.Container(
                        tab,
                    ),
                ],
                expand=1
            ),
            ft.Column(
                expand=3,
                controls=[
                    chat,
                    ft.Row(
                        controls=[
                            new_message,
                            ft.IconButton(
                                icon=ft.icons.SEND_ROUNDED,
                                tooltip="Send message",
                                on_click=send_message_click,
                            ),
                        ]
                    )
                ]
            )
        ]
    )

    page.add(content)

    def on_message(message: Message):
        if message.message_type == "chat_message":
            m = ChatMessage(message)
        elif message.message_type == "login_message":
            m = ft.Text(message.text, italic=True, color=ft.colors.BLACK45, size=12)
        chat.controls.append(m)
        page.update()

    page.pubsub.subscribe(on_message)

ft.app(target=main)
```


## Penutup:

Demikian tugas akhir Kelompok 9 Pemrograman Jaringan C. Kami telah memberikan dokumentasi yang komprehensif mengenai pembagian tugas, repository, definisi protokol chat, pertukaran data antar server, arsitektur implementasi, serta cara menjalankan server dan client. Kami berharap dokumentasi dan kode-kode yang telah kami cantumkan bermanfaat dalam memahami dan mengimplementasikan aplikasi chat yang sesuai dengan kebutuhan.
