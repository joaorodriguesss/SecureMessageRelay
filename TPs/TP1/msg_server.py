import asyncio
import base64
import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography import x509
import CRT__Validation as CRT
from collections import defaultdict
import time
from datetime import datetime

conn_cnt = 0
conn_port = 8443
max_msg_size = 9999

p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF
g = 2
parameters = dh.DHParameterNumbers(p, g).parameters()

def encrypt_message(message, derived_key):
    """
    Cifra uma mensagem utilizando AES-GCM.

    :param message: Mensagem (string) a ser cifrada.
    :param derived_key: Chave derivada para a cifra (bytes).
    :return: Uma tupla contendo o nonce e a mensagem cifrada, ambos em bytes.
    """
    # AES-GCM requer um nonce, aqui utilizamos um de 12 bytes
    nonce = os.urandom(12)

    # Cria uma instância de AESGCM com a chave derivada
    aesgcm = AESGCM(derived_key)

    # Cifra a mensagem, note que a mensagem precisa ser convertida para bytes
    encrypted_message = aesgcm.encrypt(nonce, message.encode(), None)

    # Retorna o nonce e a mensagem cifrada
    return nonce, encrypted_message

def decrypt_message(nonce, encrypted_message, derived_key):
    """
    Decifra uma mensagem utilizando AES-GCM.

    :param nonce: Nonce utilizado para cifrar a mensagem (bytes).
    :param encrypted_message: Mensagem cifrada (bytes).
    :param derived_key: Chave derivada para a decifração (bytes).
    :return: A mensagem decifrada como uma string.
    :raises: Um erro se a decifração falhar.
    """
    # Cria uma instância de AESGCM com a chave derivada
    aesgcm = AESGCM(derived_key)

    # Decifra a mensagem
    decrypted_message = aesgcm.decrypt(nonce, encrypted_message, None)

    # Retorna a mensagem decifrada, convertendo de bytes para string
    return decrypted_message.decode()

class ServerWorker(object):
    """ Classe que implementa a funcionalidade do SERVIDOR. """
    read_messages = defaultdict(list)  # Dicionário clientes -> mensagens lidas
    unread_messages = defaultdict(list)  # Dicionário clientes -> mensagens não lidas
    client_info = {} # Dicionário clientes -> public_key, certificate, derived_key, algorithm

    def __init__(self, cnt, addr=None):
        """ Construtor da classe. """
        
        self.uid_info = {}
        self.id = cnt
        self.addr = addr
        self.msg_cnt = 0

        self.private_key = parameters.generate_private_key()
        self.public_key = self.private_key.public_key()

        rsaKey, svCert, caCert = CRT.get_userdata('MSG_SERVER.p12')
        self.server_certificate = svCert
        self.ca_certificate = caCert
        self.rsa_key = rsaKey

    #Adicionar chave publica, certificado e a chave derivada de um cliente 
    def add_client_elems(self, uid,public_key, certificate, derived_key):
        if uid not in self.client_info:
            self.client_info[uid] = {}
        self.client_info[uid]['public_key'] = public_key
        self.client_info[uid]['certificate'] = certificate
        self.client_info[uid]['derived_key'] = derived_key
        self.client_info[uid]['algorithm'] = AESGCM(derived_key)
   
    def send_message_unreads(self, uid_receiver,num, sender, subject, content):
        # Cria a mensagem como um dicionário
        message = {'num': num,'sender': sender, 'subject': subject, 'time': time.time(),'content': content}
        # Adiciona a mensagem ao dicionário de mensagens não lidas
        # Aqui, utilizamos o método append para adicionar a mensagem à lista de mensagens do usuário
        if uid_receiver not in self.unread_messages:
            self.unread_messages[uid_receiver] = [message]
        else:
            self.unread_messages[uid_receiver].append(message)
        
        print(f"Mensagem adicionada com key: {uid_receiver}. Total de mensagens não lidas: {len(self.unread_messages[uid_receiver])}")
        
    def send_message_reads(self, uid_receiver,num, sender, subject, content):
        # Cria a mensagem como um dicionário
        message = {'num': num,'sender': sender, 'subject': subject, 'time': time.time(),'content': content}
        # Adiciona a mensagem ao dicionário de mensagens não lidas
        # Aqui, utilizamos o método append para adicionar a mensagem à lista de mensagens do usuário
        if uid_receiver not in self.read_messages:
            self.read_messages[uid_receiver] = [message]
        else:
            self.read_messages[uid_receiver].append(message)

    def get_unread_messages(self, uid):
        if uid in self.unread_messages:
            formatted_messages = []
            for idx, message in enumerate(self.unread_messages[uid], start=1):
                # Formata o tempo da mensagem para dia/mês/ano hora:minuto
                message_time = datetime.fromtimestamp(message['time']).strftime('%d/%m/%Y %H:%M')
                # Formata a mensagem para exibir apenas número, remetente, tempo e assunto
                formatted_message = f"{message['num']}: {message['sender']} - {message_time} - {message['subject']}"
                print(formatted_message)
                formatted_messages.append(formatted_message)
            return formatted_messages
        else:
            print(f"[{uid}] Sem mensagens por ler.")
            return []

    def get_read_messages(self, uid):
        return self.read_messages[uid]
    
    def get_message(self, uid, num):
        res = None
        if uid in self.unread_messages:
            for message in self.unread_messages[uid]:
                if message['num'] == num:
                    res = message
                    self.unread_messages[uid].remove(message)
                    self.send_message_reads(uid, message['num'], message['sender'], message['subject'], message['content'])
                    return res
        if uid in self.read_messages:
            for message in self.read_messages[uid]:
                if message['num'] == num:
                    res = message
                    return res
        return None


    async def preliminary_exchange(self, reader, writer):
        #verificar cliente 

        # Receber a chave pública do cliente
        
        response = await reader.read(max_msg_size)
        client_public_key = serialization.load_pem_public_key(response)

        # passar para bytes
        public_key_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        client_public_key_bytes = client_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        #Assinar  SigB(gy, gx)
        keys = CRT.mkpair(public_key_bytes, client_public_key_bytes)
        signature = self.rsa_key.sign(
            keys,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        #Certificado 2 bytes
        server_certificate_bytes = CRT.convertCert_to_bytes(self.server_certificate)
        rest = CRT.mkpair(signature, server_certificate_bytes)

        # Enviar chave publica do servidor, assinatura e certificado
        data = CRT.mkpair(public_key_bytes,rest)
        writer.write(data)
        await writer.drain()

        # Receber a assinatura e certificado do cliente
        response = await reader.read(max_msg_size)
        signature, certClient_bytes = CRT.unpair(response)

        # Verificar certificado do cliente
        certClient = CRT.convert_to_certificate(certClient_bytes)
        CRT.valida_cert(self.ca_certificate,certClient)

        # Verificar assinatura do cliente
        try:
            Imsg = CRT.mkpair(client_public_key_bytes, public_key_bytes) 
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
        shared_key = self.private_key.exchange(client_public_key)
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data',
        ).derive(shared_key)
        
        uid = CRT.get_UID(certClient)
        self.add_client_elems(uid,client_public_key, certClient, derived_key)

        # Enviar simples string a dizer que tudo correu bem
        # Preparar a mensagem incluindo o UID
        uid_str = str(uid)
        message = "Cliente verificado com UID: " + uid_str
        message_bytes = message.encode('utf-8')  # Codifica a mensagem como bytes

        # Enviar a mensagem ao cliente
        writer.write(message_bytes)
        await writer.drain()

        self.uid_info[uid] = True

        return uid
    

    async def process(self,reader, writer, data_encrypted, uid):
        """ Processa uma mensagem (`bytestring`) enviada pelo CLIENTE.
            Retorna a mensagem a transmitir como resposta (`None` para
            finalizar ligação) """
    


        # Aguarde a mensagem do cliente
        # data = await reader.read(max_msg_size)
        

        # Ao receber dados, suponha que os primeiros 12 bytes são o nonce
        nonce = data_encrypted[:12]
        encrypted_msg = data_encrypted[12:]
        # Usa a chave derivada para decifrar a mensagem
        derived_key = self.client_info[uid]['derived_key']
        data = decrypt_message(nonce, encrypted_msg, derived_key)
        # Agora `decrypted_msg` contém o comando em texto plano
        if not data:
            # Se não houver mais dados, encerre o loop
            pass    

        #outros casos
        parts = data.split()
        if parts[0] == 'exit':
        # Se o cliente enviar 'exit', encerre a conexão
            pass
        # Converta a mensagem recebida em uma lista de palavras
        elif parts[0] == 'send':
            uid2send = parts[1]
            sub = parts[2:]
            subject = " ".join(sub)

            confirm = "processing send request"
            writer.write(confirm.encode())
            await writer.drain()


            # Receber a ct
            data = await reader.read(max_msg_size)
            num = self.msg_cnt
            self.msg_cnt += 1
            self.send_message_unreads(uid2send,num, uid, subject, data)
            response = f'Mensagem enviada para {uid2send} com sucesso.'
            #encriptar a mensagem de retorno
            nonce = os.urandom(12)
            encrypted_message = self.client_info[uid]['algorithm'].encrypt(nonce, response.encode(), None)
            writer.write(nonce + encrypted_message)
            await writer.drain()
            
        
        elif parts[0] == 'getpubkey':
            uid2send = parts[1]
            if uid2send in self.client_info:
                public_key = self.client_info[uid2send]['public_key']
                public_key_bytes = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                # Apenas enviar a chave pública ao cliente
                writer.write(public_key_bytes)
                await writer.drain()
            else:
                writer.write(b'ERROR: UID not found')
                await writer.drain()
        elif parts[0] == 'askqueue':
            messages = self.get_unread_messages(uid)
            if len(messages) == 0:
                response = f"[{uid}] Sem messages por ler."
            else:
                response=""
                for elem in messages:
                    response = response + elem + "\n"
                
            # Enviar resposta encripatada para o cliente
            algoritm = self.client_info[uid]['algorithm']
            nonce = os.urandom(12)
            encrypted_response = algoritm.encrypt(nonce, response.encode(), None)
            writer.write(nonce + encrypted_response)
            await writer.drain()
    
            
        elif parts[0] == 'getmsg':
            num = parts[1] 
            print(num)
            msg = self.get_message(uid, int(num))  
            
            if msg is not None:
                msg['content'] = base64.b64encode(msg['content']).decode() 
                msg_json = json.dumps(msg)

                # Convertendo a mensagem JSON de volta para bytes
                msg_bytes = msg_json.encode()

                # Enviando a mensagem
                writer.write(msg_bytes)
                await writer.drain()
            else:
                writer.write(b'MSG RELAY SERVICE: unknown message!')
                await writer.drain()






        
#
#
# Funcionalidade Cliente/Servidor
#
# obs: não deverá ser necessário alterar o que se segue
#

async def handle_echo(reader, writer):
    global conn_cnt
    conn_cnt += 1
    addr = writer.get_extra_info('peername')
    srvwrk = ServerWorker(conn_cnt, addr)
    
    try:
        uid = await srvwrk.preliminary_exchange(reader, writer)
    except Exception as e:
        print("An error occurred during preliminary exchange:", e)
        writer.close()
        return

    while True:
        # Aguardar a mensagem do cliente
        data = await reader.read(max_msg_size)
        #print("DATA: ", data)
        if not data:
            break
        # Processar a mensagem do cliente
        response = await srvwrk.process(reader, writer, data, uid)


    writer.close()

def run_server():
    loop = asyncio.new_event_loop()
    coro = asyncio.start_server(handle_echo, '127.0.0.1', conn_port)
    server = loop.run_until_complete(coro)
    # Servir requisições até Ctrl+C ser pressionado
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    print('  (type ^C to finish)\n')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    # Fechar o servidor
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
    print('\nFINISHED!')


run_server()