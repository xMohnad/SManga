from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import hashlib
import base64


class CryptoAES:

    @staticmethod
    def decrypt(ciphertext, password):
        ct_bytes = base64.b64decode(ciphertext)
        salt = ct_bytes[8:16]
        ciphertext = ct_bytes[16:]

        key, iv = CryptoAES._generate_key_and_iv(password, salt, 32, 16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted.decode("utf-8")

    @staticmethod
    def _generate_key_and_iv(password, salt, key_length, iv_length):
        d = d_i = b""
        while len(d) < key_length + iv_length:
            d_i = hashlib.md5(d_i + password.encode("utf-8") + salt).digest()
            d += d_i
        return d[:key_length], d[key_length : key_length + iv_length]
