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