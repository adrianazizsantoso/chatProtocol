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