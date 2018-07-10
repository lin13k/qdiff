from cryptography.fernet import Fernet
from django.conf import settings


class FernetCipher:
    def __init__(self, cipher=None):
        if cipher:
            self.cipher = Fernet(cipher)
        else:
            self.cipher = Fernet(settings.FILE_ENCRYPTION_KEY)

    def encode(self, plaintext):
        return self.cipher.encrypt(plaintext.encode('ascii')).decode('ascii')

    def decode(self, ciphertext):
        return self.cipher.decrypt(ciphertext.encode('ascii')).decode('ascii')


def decodedContent(file):
    fc = FernetCipher()
    return fc.decode(file.read())
