import asyncio
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
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
    return x509.load_pem_x509_certificate(cert_bytes, default_backend())


conn_port = 8443
max_msg_size = 9999

p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF
g = 2
parameters = dh.DHParameterNumbers(p, g).parameters()

class Client:
    """ Classe que implementa a funcionalidade de um CLIENTE. """
    def __init__(self, sckt=None):
        """ Construtor da classe. """
        self.sckt = sckt
        self.msg_cnt = 0
        self.private_key = parameters.generate_private_key()
        self.public_key = None
        self.derived_key = None
        
        self.client_certificate = None
        self.server_certificate = None
        self.server_public_key = None

        self.content = None


    def process(self, msg=b""):
        """ Processa uma mensagem (`bytestring`) enviada pelo SERVIDOR.
            Retorna a mensagem a transmitir como resposta (`None` para
            finalizar ligação) """
        
        with open('MSG_CLI1.key', 'rb') as key_file:
            self.rsa_key = serialization.load_pem_private_key(
                key_file.read(), password=b"1234", backend=default_backend())
        
        self.client_certificate = cert_load('MSG_CLI1.crt')
        
            
        if msg == None or msg == b"":
            # Enviar a chave pública do cliente ao servidor
            self.public_key = self.private_key.public_key()
            pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            print('Sending public key to server')
            return pem



        # Receber a chave pública do servidor, assinatura e certificado
        if self.derived_key == None:

            pem, rest = unpair(msg)
            signature, certServer = unpair(rest)
            print('Received server public key:')
            print(pem)

            print('Received signature:')
            #print(signature)

            print('Received server certificate:')
            #print(certServer)
            
            #Chave publica do servidor
            self.server_public_key = serialization.load_pem_public_key(pem)
             
            print('Received server public key after:')
            print(self.server_public_key)
            shared_key = self.private_key.exchange(self.server_public_key)
            self.derived_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b'Kmaster',
            ).derive(shared_key)

            #Sig e Cert do servidor
            signature, certServer_bytes = unpair(rest)

            # Verificar certificado do servidor
            certServer = convert_to_certificate(certServer_bytes)
            print('Received server certificate:')
            print(certServer)
            CA_cert = cert_load('MSG_CA.crt')
            valida_cert(CA_cert, certServer)
                
            # 2Bytes
            public_key_bytes = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            server_public_key_bytes = self.server_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Verificar assinatura do servidor
            try:    
                Imsg = mkpair(server_public_key_bytes, public_key_bytes) 
                certServer.public_key().verify(
                    signature,
                    Imsg,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            except Exception as e:
                print("Error verifying signature: " ,e)
            #Assinar  SigA(gx, gy)

            gXgY = mkpair(public_key_bytes,server_public_key_bytes)
            signature = self.rsa_key.sign(
                gXgY,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            # Apos tudo certo criar algoritmo
            self.algorithm = algorithms.AES(self.derived_key)

            #enviar assinatura e certificado do cliente
            client_certificate_bytes = convert_to_bytes(self.client_certificate)
            return mkpair(signature, client_certificate_bytes) 

        if self.content == None:
            print('Input message to send (empty to finish)')
            new_msg = input().encode()

            if len(new_msg) == 0: return None
            nounce = os.urandom(16)
            cipher = Cipher(self.algorithm, modes.CTR(nounce))
            decryptor = cipher.decryptor()
            new_msg = decryptor.update(new_msg)
            self.content = True
            return nounce + new_msg

        else: 
            nounce = msg[:16]
            msg = msg[16:]
            self.msg_cnt += 1
            cipher = Cipher(self.algorithm, modes.CTR(nounce))
            decrypted = cipher.decryptor().update(msg)
            print('Received (%d): %r' % (self.msg_cnt, decrypted.decode()))
            
            print('Input message to send (empty to finish)')
            new_msg = input().encode()

            if len(new_msg) == 0: return None
            nounce = os.urandom(16)
            cipher = Cipher(self.algorithm, modes.CTR(nounce))
            decryptor = cipher.decryptor()
            new_msg = decryptor.update(new_msg)
            return nounce + new_msg


async def tcp_echo_client():
    reader, writer = await asyncio.open_connection('127.0.0.1', conn_port)
    addr = writer.get_extra_info('peername')
    client = Client(addr)
    msg = client.process()
    print(msg)
    while msg:
        writer.write(msg)
        msg = await reader.read(max_msg_size)
        if msg:
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
