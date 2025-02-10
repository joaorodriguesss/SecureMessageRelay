import asyncio
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from CRT__Validation import cert_load, valida_cert
from cryptography.x509 import Certificate
from cryptography import x509

def mkpair(x, y):
    """produz uma byte-string contendo o tuplo '(x,y)' ('x' e 'y' são byte-strings)"""
    len_x = len(x)
    len_x_bytes = len_x.to_bytes(2, "little")
    return len_x_bytes + x + y


def unpair(xy):
    """extrai componentes de um par codificado com 'mkpair'"""
    len_x = int.from_bytes(xy[:2], "little")
    x = xy[2 : len_x + 2]
    y = xy[len_x + 2 :]
    return x, y

def convert_to_bytes(obj):
    """Converte o objeto para bytes."""
    if isinstance(obj, Certificate):
        return obj.public_bytes(serialization.Encoding.PEM)
    else:
        return obj

def convert_to_certificate(cert_bytes):
    """Converte bytes de certificado em um objeto Certificate."""
    return x509.load_pem_x509_certificate(cert_bytes)



conn_cnt = 0
conn_port = 8443
max_msg_size = 9999

p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF
g = 2
parameters = dh.DHParameterNumbers(p, g).parameters()

class ServerWorker(object):
    """ Classe que implementa a funcionalidade do SERVIDOR. """
    def __init__(self, cnt, addr=None):
        """ Construtor da classe. """
        self.id = cnt
        self.addr = addr
        self.msg_cnt = 0
        self.derived_key = None
        self.private_key = parameters.generate_private_key()
        self.public_key = None

        self.server_certificate = None
        self.client_certificate = None
        self.client_public_key = None


    def process(self, msg):
        """ Processa uma mensagem (`bytestring`) enviada pelo CLIENTE.
            Retorna a mensagem a transmitir como resposta (`None` para
            finalizar ligação) """

        with open('MSG_SERVER.key', 'rb') as key_file:
            self.rsa_key = serialization.load_pem_private_key(
                key_file.read(), password="1234".encode())

        self.server_certificate =cert_load('MSG_SERVER.crt')
        
        if self.derived_key == None:
            #primeira mensagem recebida será a chave publica do cliente
            self.client_public_key = serialization.load_pem_public_key(msg)
            
            shared_key = self.private_key.exchange(self.client_public_key)
            self.derived_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b'Kmaster',
            ).derive(shared_key)

            #criar chave publica do servidor
            self.public_key = self.private_key.public_key()

            #Assinar  SigB(gy, gx)

            # passar para bytes
            public_key_bytes = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            client_public_key_bytes = self.client_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            keys = mkpair(public_key_bytes, client_public_key_bytes)
            signature = self.rsa_key.sign(
                keys,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            server_certificate_bytes = convert_to_bytes(self.server_certificate)
            rest = mkpair(signature, server_certificate_bytes)
            #enviar chave publica do servidor, assinatura e certificado
            print("Pem made! \n")
            #print(public_key_bytes)
            return mkpair(public_key_bytes,rest) 

        
        if self.client_certificate == None:
            # Receber a assinatura e certificado do cliente
            signature, certClient_bytes = unpair(msg)

            # Verificar certificado do cliente
            certClient = convert_to_certificate(certClient_bytes)
            CA_cert = cert_load('MSG_CA.crt')
            print ("Validating certificate")
            valida_cert(CA_cert,certClient)
            print ("Validation Done")
            
            # Verificar assinatura do cliente
            client_public_key_bytes = self.client_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            public_key_bytes = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            try:
                Imsg = mkpair(client_public_key_bytes, public_key_bytes) 
                certClient.public_key().verify(
                    signature,
                    Imsg,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                self.client_certificate = certClient
            except Exception as e:
                print("An error occurred during signature verification:", e)
            
            # Apos tudo certo criar algoritmo
            self.algorithm = algorithms.AES(self.derived_key)


        self.msg_cnt += 1

        nounce = msg[:16]
        msg= msg[16:]
        cipher = Cipher(self.algorithm, modes.CTR(nounce))
        encryptor = cipher.encryptor()
        txt = encryptor.update(msg)
        txt = txt.decode()
        print('%d : %s' % (self.id,txt))
        new_msg = txt.upper().encode()
        print(new_msg)
        if len(new_msg) == 0: return None

        
        decryptor = cipher.decryptor()
        new_msg = decryptor.update(new_msg)
        
        #write a byte string where the first 12 bytes are the nonce and the other ones new_msg
        return nounce + new_msg




#
#
# Funcionalidade Cliente/Servidor
#
# obs: não deverá ser necessário alterar o que se segue
#

async def handle_echo(reader, writer):
    global conn_cnt
    conn_cnt +=1
    addr = writer.get_extra_info('peername')
    srvwrk = ServerWorker(conn_cnt, addr)
    data = await reader.read(max_msg_size)
    while True:
        if not data: continue
        if data[:1]==b'\n': break
        data = srvwrk.process(data)
        if not data: break
        writer.write(data)
        await writer.drain()
        data = await reader.read(max_msg_size)
    print("[%d]" % srvwrk.id)
    writer.close()


def run_server():
    loop = asyncio.new_event_loop()
    coro = asyncio.start_server(handle_echo, '127.0.0.1', conn_port)
    server = loop.run_until_complete(coro)
    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    print('  (type ^C to finish)\n')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
    print('\nFINISHED!')


run_server()