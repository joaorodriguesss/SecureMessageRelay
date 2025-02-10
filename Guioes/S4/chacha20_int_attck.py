import sys
import os
import struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes



def main(inp):
    """ função que executa a funcionalidade pretendida... """
   
    fileCypher = inp[1]
    pos = int(inp[2])  
    palavraPos = inp[3]  
    novaPalavra =inp[4]  

    with open(fileCypher, 'rb') as file:
        file.seek( 16 + pos )
        b = len(palavraPos)
        ct = file.read(b)

    hack = bytes([a ^ b ^ c for a, b, c in zip(palavraPos.encode(), novaPalavra.encode(), ct)])

    with open(fileCypher, 'rb') as file:
        nonce = file.read(16)
        file.seek(0)
        file.seek(16 + b)
        rest = file.read()
    
    with open(fileCypher + '.attck','wb') as fileOut:
        fileOut.write(nonce)
        fileOut.write(hack)
        fileOut.write(rest)
    

main(sys.argv)