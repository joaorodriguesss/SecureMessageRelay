import asyncio
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend


conn_port = 8443
max_msg_size = 9999


p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF
g = 2
parameters = dh.DHParameterNumbers(p, g).parameters()
#parameters = dh.generate_parameters(generator=2, key_size=2048)
print(parameters)

class Client:
    """ Classe que implementa a funcionalidade de um CLIENTE. """
    def __init__(self, sckt=None):
        """ Construtor da classe. """
        self.sckt = sckt
        self.msg_cnt = 0
        self.private_key = parameters.generate_private_key()
        self.derived_key = None
        


    def process(self, msg=b""):
        """ Processa uma mensagem (`bytestring`) enviada pelo SERVIDOR.
            Retorna a mensagem a transmitir como resposta (`None` para
            finalizar ligação) """

        if msg == None or msg == b"" :
            #primeira mensagem a enviar é a chave publica
            pem = self.private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem
        
        if self.derived_key == None:
            #primeira mensagem recebida será a chave publica do servidor
            shared_key = self.private_key.exchange(serialization.load_pem_public_key(msg))
            self.derived_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b'Kmaster',
            ).derive(shared_key)
            self.algorithm = algorithms.AES(self.derived_key)

        else:
            nounce = msg[:16]
            msg= msg[16:]
            self.msg_cnt += 1
            cipher = Cipher(self.algorithm, modes.CTR(nounce))
            decrypted = cipher.decryptor().update(msg)
            print('Received (%d): %r' % (self.msg_cnt , decrypted.decode()))

            # decode the message with the derived ke


        print('Input message to send (empty to finish)')
        new_msg = input().encode()
        #
        if len(new_msg) == 0: return None
        nounce = os.urandom(16)
        cipher = Cipher(self.algorithm, modes.CTR(nounce))
        decryptor = cipher.decryptor()
        new_msg = decryptor.update(new_msg)
        return nounce + new_msg
        
        #write a byte string where the first 12 bytes are the nonce and the other ones new_msg




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
    print(msg)
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
