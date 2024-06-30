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