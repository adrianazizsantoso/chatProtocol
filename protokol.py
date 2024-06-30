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