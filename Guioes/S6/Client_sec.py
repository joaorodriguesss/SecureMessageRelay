# Código baseado em https://docs.python.org/3.6/library/asyncio-stream.html#tcp-echo-client-using-streams
import asyncio
import socket
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

password = "gghlioucfcghjoi"
conn_port = 8443
max_msg_size = 9999

def pad_string_to_32_bytes(s):
    if len(s) >= 32:
        return s[:32]
    else:
        return s.ljust(32, b'\0')
    

class Client:
    """ Classe que implementa a funcionalidade de um CLIENTE. """
    def __init__(self, sckt=None):
        """ Construtor da classe. """
        self.sckt = sckt
        self.msg_cnt = 0
    def process(self, msg=b""):
        """ Processa uma mensagem (`bytestring`) enviada pelo SERVIDOR.
            Retorna a mensagem a transmitir como resposta (`None` para
            finalizar ligação) """
        self.msg_cnt +=1
        allM = None
        # 
        #
        if msg == b"":
            print('Received (%d): %r' % (self.msg_cnt , msg))

            print('Input message to send (empty to finish)')
            new_msg = input().encode()
            passW = pad_string_to_32_bytes(password.encode())
            nonce = os.urandom(12)
            aesgcm = AESGCM(passW)
            ciphertext = aesgcm.encrypt(nonce, new_msg, None)
            allM = nonce + ciphertext


        else:    
            nonce_R = msg[:12]
            ciphertext = msg[12:]
            passW = pad_string_to_32_bytes(password.encode())
            aesgcm = AESGCM(passW)
            decrypt_msg = aesgcm.decrypt(nonce_R, ciphertext, None).decode()
            
            print('Received (%d): %r' % (self.msg_cnt , decrypt_msg))
            
            print('Input message to send (empty to finish)')
            new_msg = input().encode()
            
            nonce = os.urandom(12)
            ciphertext = aesgcm.encrypt(nonce, new_msg, None)
            allM = nonce + ciphertext

        
        return allM 



#
#
# Funcionalidade Cliente/Servidor
#
# obs: não deverá ser necessário alterar o que se segue
#


async def tcp_echo_client():
    reader, writer = await asyncio.open_connection('127.0.0.1', conn_port)
    addr = writer.get_extra_info('peername')
    client = Client(addr)
    msg = client.process()
    while msg:
        writer.write(msg)
        msg = await reader.read(max_msg_size)
        if msg :
            msg = client.process(msg)
        else:
            break
    writer.write(b'\n')
    print('Socket closed!')
    writer.close()

def run_client():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tcp_echo_client())


run_client()