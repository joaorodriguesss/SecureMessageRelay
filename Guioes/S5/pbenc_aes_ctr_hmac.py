import sys
import os
import struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, hmac

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


        NONCE = os.urandom(8)
        counter = 0
        full_nonce = struct.pack("<Q", counter) + NONCE
        cipher = Cipher(algorithms.AES(key), modes.CTR(full_nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        
        with open(fileCypher, 'rb') as cypher_file:
            message = cypher_file.read()
        
        ct = encryptor.update(message)

        h = hmac.HMAC(key, hashes.SHA256())
        h.update(ct)
        signature = h.finalize()

        #escrever para o fileCypher.enc
        with open(fileCypher + '.enc','wb') as fileOut:
            fileOut.write(signature)
            fileOut.write(salt)
            fileOut.write(full_nonce)
            fileOut.write(ct)

    else:
        fileCypher = inp[2]
        
        password = input("Enter passphrase: ").encode('utf-8')

        with open(fileCypher, 'rb') as file:
            signature = file.read(32)
            salt = file.read(16)
            full_nonce = file.read(16)
            ct = file.read()

        kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
        ) 
        key = kdf.derive(password)        

        cipher = Cipher(algorithms.AES(key), modes.CTR(full_nonce), backend=default_backend())
        decryptor = cipher.decryptor()
        
        message = decryptor.update(ct)

        h = hmac.HMAC(key, hashes.SHA256())
        h.update(ct)
        h.verify(signature)


        #escrever para o fileCypher.dec
        with open(fileCypher + '.dec','wb') as fileOut:
            fileOut.write(message)


main(sys.argv)