import sys
import os
import struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes



def main(inp):
    """ função que executa a funcionalidade pretendida... """
    type = inp[1] 

    if type == 'setup':
        fileW = inp[2]
        iv = os.urandom(32)
        with open(fileW,'wb') as file:
            file.write(iv)

    elif type == 'enc':
        fileCypher = inp[2]
        fileKey = inp[3]
        with open(fileKey, 'rb') as key_file:
            key = key_file.read()

        NONCE = os.urandom(8)
        counter = 0
        full_nonce = struct.pack("<Q", counter) + NONCE
        algorithm = algorithms.ChaCha20(key, full_nonce)
        cipher = Cipher(algorithm, mode=None)
        encryptor = cipher.encryptor()
        with open(fileCypher, 'rb') as cypher_file:
            message = cypher_file.read()
        
        ct = encryptor.update(message)


        #escrever para o fileCypher.enc
        with open(fileCypher + '.enc','wb') as fileOut:
            fileOut.write(full_nonce)
            fileOut.write(ct)

    else:
        fileCypher = inp[2]
        fileKey = inp[3]
        with open(fileKey, 'rb') as key_file:
            key = key_file.read()

        with open(fileCypher, 'rb') as file:
            full_nonce = file.read(16)
            ct = file.read()

        algorithm = algorithms.ChaCha20(key, full_nonce)
        cipher = Cipher(algorithm, mode=None)
        decryptor = cipher.decryptor()
        
        message = decryptor.update(ct)

        #escrever para o fileCypher.dec
        with open(fileCypher + '.dec','wb') as fileOut:
            fileOut.write(message)


    

main(sys.argv)