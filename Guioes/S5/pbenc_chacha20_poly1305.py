import sys
import os
import struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

# dec ou enc || fileCypher 


def main(inp):
    """ função que executa a funcionalidade pretendida... """
    type = inp[1] 

    if  type == 'enc':
        fileCypher = inp[2]
        
        password = input("Enter passphrase: ").encode('utf-8')
        salt = os.urandom(16)

        kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
        )       
        key = kdf.derive(password) 


        NONCE = os.urandom(12)
        chacha = ChaCha20Poly1305(key)
        
        with open(fileCypher, 'rb') as cypher_file:
            message = cypher_file.read()
        
        ct = chacha.encrypt(NONCE, message, None)

        #escrever para o fileCypher.enc
        with open(fileCypher + '.enc','wb') as fileOut:
            fileOut.write(salt)
            fileOut.write(NONCE)
            fileOut.write(ct)

    else:
        fileCypher = inp[2]
        
        password = input("Enter passphrase: ").encode('utf-8')

        with open(fileCypher, 'rb') as file:
            salt = file.read(16)
            full_nonce = file.read(12)
            ct = file.read()

        kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
        ) 
        key = kdf.derive(password)        

        chacha = ChaCha20Poly1305(key)
        message = chacha.decrypt(full_nonce, ct, None)

        #escrever para o fileCypher.dec
        with open(fileCypher + '.dec','wb') as fileOut:
            fileOut.write(message)


main(sys.argv)