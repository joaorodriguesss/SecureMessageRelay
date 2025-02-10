import asyncio
import base64
import os
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography import x509
import datetime
import CRT__Validation as CRT
import sys


conn_port = 8443
max_msg_size = 9999

p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF
g = 2
parameters = dh.DHParameterNumbers(p, g).parameters()

def is_PK(bytes):
    try:
        serialization.load_pem_public_key(bytes)
        return True
    except Exception:
        return False

def get_pseudonym(user_cert: x509.Certificate):
    pseudonym_value = None
    for attribute in user_cert.subject:
        if attribute.oid._name == "pseudonym":
            pseudonym_value = attribute.value
            break
    if pseudonym_value is not None:
        return pseudonym_value
    else:
        return None

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

class Client:
    """ Classe que implementa a funcionalidade de um CLIENTE. """
    def __init__(self, sckt=None):
        """ Construtor da classe. """
        self.sckt = sckt
        self.msg_cnt = 0

        self.private_key = parameters.generate_private_key()
        self.public_key = self.private_key.public_key()
        
        self.rsa_key = None
        self.client_certificate = None
        self.ca_certificate = None

        self.server_public_key = None
        self.server_certificate = None

        self.algorithm = None
        self.derived_key = None
        
        self.file = None
        self.logged = False



    def my_parser(self, command):
        #opções 
        # -user <FNAME> (opcional antes do send, asqueue, getmsg)         
        # send <UID> <SUBJECT>
        # askqueue
        # getmsg <NUM>
        # help
        r = None
        parts = command.split()
        if parts[0] == '-user':
            if len(parts) > 2:
                #tratar do FNAME (ficheiro com userdata)
                if self.file == None:

                    self.file = parts[1]
                    #Verificar comando a seguir
                    if parts[2] == 'send' and len(parts) >= 5:
                        uid = parts[1]
                        subject_parts = parts[2:]  # Pega todas as partes do assunto
                        subject = " ".join(subject_parts)
                        r = 'send' + ' ' + uid + ' ' + subject 
                    elif parts[2] == 'askqueue':
                        r= 'askqueue'
                    elif parts[2] == 'getmsg' and len(parts) == 4:
                        r= 'getmsg' + ' ' + parts[3]
                    else:
                        print('Invalid command')
                else:
                    print('User data already defined')     
            else:
                print('Missing arguments, help to see the options')
                # este send não devia ser implementado assim, devia primeiro esperar 3 args e depois dar outro arg (a mensagem)
        # elif parts[0] == 'send' and len(parts) == 4:
        #     r = 'send' + ' ' + parts[1] + ' ' + parts[2] + ' ' + parts[3]
        elif parts[0] == 'send' and len(parts) >= 3:
            uid = parts[1]
            subject_parts = parts[2:]  # Pega todas as partes do assunto
            subject = " ".join(subject_parts)
            r = 'send'+ ' ' + uid + ' ' + subject
        elif parts[0] == 'exit':
            sys.exit()  # Isso vai encerrar o script Python.
        elif parts[0] == 'askqueue' and len(parts) == 1:
            r = 'askqueue' 
        elif parts[0] == 'getmsg' and len(parts) == 2:
            r = 'getmsg' + ' ' + parts[1]
        elif parts[0] == 'help' and len(parts) == 1:
            print("\n-user <FNAME> - argumento opcional (que deverá surgir sempre em primeiro lugar) que especifica o ficheiro com dados do utilizador. Por omissão, será assumido que esse ficheiro é userdata.p12.\n")
            print("send <UID> <SUBJECT> - envia uma mensagem com assunto <SUBJECT> destinada ao utilizador com identificador <UID>. O conteúdo da mensagem será lido do stdin, e o tamanho deve ser limitado a 1000 bytes.\n")
            print("askqueue - solicita ao servidor que lhe envie a lista de mensagens não lidas da queue do utilizador.Para cada mensagem na queue, é devolvida uma linha contendo: <NUM>:<SENDER>:<TIME>:<SUBJECT>,onde <NUM> é o número de ordem da mensagem na queue e <TIME> um timestamp adicionado pelo servidor que regista a altura em que a mensagem foi recebida.\n")
            print("getmsg <NUM> - solicita ao servidor o envio da mensagem da sua queue com número <NUM>. No caso de sucesso, a mensagem será impressa no stdout. Uma vez enviada, essa mensagem será marcada como lida, pelo que não será listada no próximo comando askqueue (mas pode voltar a ser pedida pelo cliente).\n")
            r = 'help'
        else:
            print('Invalid command')      
            
        return r


    async def preliminary_exchange(self, reader, writer):
        #verificar servidor (trocar public keys, certificados e assinaturas)
        if self.file == None:
            self.file = 'userdata.p12'
        
        self.rsa_key, self.client_certificate,self.ca_certificate  = CRT.get_userdata(self.file)

        # Enviar a chave pública do cliente ao servidor
        pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        if writer is not None:  # <-----------------
            writer.write(pem)
            await writer.drain()
        

        # Receber a chave pública do servidor, assinatura e certificado
        response = await reader.read(max_msg_size)
        if response and writer is not None:  # <------------------
            pemSv, rest = CRT.unpair(response)
            signature, certServer_bytes = CRT.unpair(rest)
            
            #Chave publica do servidor
            self.server_public_key = serialization.load_pem_public_key(pemSv)

            # Verificar certificado do servidor
            certServer = CRT.convert_to_certificate(certServer_bytes)
            CRT.valida_cert(self.ca_certificate, certServer)

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
                Imsg = CRT.mkpair(server_public_key_bytes, public_key_bytes) 
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
            gXgY = CRT.mkpair(public_key_bytes,server_public_key_bytes)
            signature = self.rsa_key.sign(
                gXgY,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            #Enviar assinatura e certificado do cliente ao servidor
            client_certificate_bytes = CRT.convertCert_to_bytes(self.client_certificate)
            data = CRT.mkpair(signature, client_certificate_bytes) 


        if writer is not None:  # <-----------------
            writer.write(data)
            await writer.drain()

        # Aguarde e leia a resposta do servidor novamente
        response = await reader.read(max_msg_size)


        # Apos tudo certo criar algoritmo
        shared_key = self.private_key.exchange(self.server_public_key)
        self.derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data',
        ).derive(shared_key)
        self.algorithm = AESGCM(self.derived_key)

        return None
    
    async def execute(self, reader, writer, command):
       #vez do cliente enviar dados
        command = command.split()
        if command[0] =='send':
            uid = command[1]

            # pedir ao servidor a chave publica do utilizador com uid
            nonce = os.urandom(12)
            message = 'getpubkey ' + uid
            ct = self.algorithm.encrypt(nonce, message.encode(), None)
            writer.write(nonce + ct)
            await writer.drain()

            # Receber a chave pública do utilizador (nao vem encriptada)
            response = await reader.read(max_msg_size)
            if response == b'ERROR: UID not found':
                print("ERROR: UID not found")
                return None

            else:
                # temos a pk (response em bytes), preciso conteudo da mensagem
                r = True
                while r:
                    content = input("Digite o conteúdo da mensagem:\n")
                    if len(content.encode()) > 1000:
                        print("A mensagem excedeu o limite de 1000 bytes. Por favor, insira uma mensagem com menos de 1000 bytes.")
                    else:
                        r = False

                subject = command[2:]
                firstS = 'send' + ' ' + str(uid) + ' ' + ' '.join(subject)
                # enviar apenas send 
                nonce = os.urandom(12)
                ct = self.algorithm.encrypt(nonce, firstS.encode(), None)

                writer.write(nonce + ct)
                await writer.drain()

                # Receber confirmação do servidor (nao vem encriptada)
                confirmation = await reader.read(max_msg_size)
                conf = confirmation.decode()
                if conf == 'processing send request':
                    
                    # criar algoritmo dos 2 clientes
                    pk = serialization.load_pem_public_key(response)
                    shared_key = self.private_key.exchange(pk)
                    derived_key = HKDF(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=None,
                        info=b'handshake data',
                    ).derive(shared_key)
                    algorithm = AESGCM(derived_key)

                    # Assinar conteudo 
                    signature = self.rsa_key.sign(
                        content.encode(),
                        padding.PSS(
                            mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                    )
                    #juntar conteudo com assinatura e certificado
                    signANDcert = CRT.mkpair(signature, CRT.convertCert_to_bytes(self.client_certificate))
                    contenANDsignANDcert = CRT.mkpair(content.encode(), signANDcert)

                    #encrpitar conteudo, assinatura e certificado com algorimto dos clientes
                    nonce = os.urandom(12)
                    ct = algorithm.encrypt(nonce, contenANDsignANDcert, None)

                    # Enviar  nonce e conteudo para os clientes 
                    writer.write(nonce + ct)
                    await writer.drain()

                    # Aguardar e imprimir a resposta do servidor
                    response = await reader.read(max_msg_size)
                    res = self.algorithm.decrypt(response[:12], response[12:], None)
                    print(res.decode())

        elif command[0] == 'askqueue':
            
            # Envia o comando para o servidor
            nonce = os.urandom(12)
            ct = self.algorithm.encrypt(nonce, command[0].encode(), None)
            writer.write(nonce + ct)
            await writer.drain()

            response = await reader.read(max_msg_size)
            nonce = response[:12]
            encrypted_response = response[12:]
            # Decifra a resposta
            decrypted_response = self.algorithm.decrypt(nonce, encrypted_response, None)
            print(decrypted_response.decode())
            
        elif command[0] == 'getmsg':
            # Envia o comando para o servidor
            send = 'getmsg ' + command[1]
            nonce = os.urandom(12)
            ct = self.algorithm.encrypt(nonce, send.encode(), None)
            writer.write(nonce + ct)
            await writer.drain()
           
            # Recebe a mensagem 
            received_bytes = await reader.read(4096)  # Tamanho máximo dos bytes recebidos
            
            if received_bytes.startswith(b'MSG RELAY SERVICE'):
                error_message = received_bytes.decode()
                print("ERROR: ", error_message)
            else:
                # Decodificando os bytes para JSON
                received_json = received_bytes.decode()
                # Convertendo JSON de volta para dicionário
                received_msg = json.loads(received_json)
                # Convertendo o conteúdo de volta para bytes
                received_msg['content'] = base64.b64decode(received_msg['content'])

                # Acessando os campos da mensagem
                num = received_msg['num']
                sender = received_msg['sender']
                subject = received_msg['subject']
                time = received_msg['time']
                content = received_msg['content']

                # criar algoritmo dos 2 clientes
                #pedir chave publica do sender
                nonce = os.urandom(12)
                message = 'getpubkey ' + sender
                ct = self.algorithm.encrypt(nonce, message.encode(), None)
                writer.write(nonce + ct)
                await writer.drain()

                # Receber a chave pública do utilizador (nao vem encriptada)
                response = await reader.read(max_msg_size)
                if response == b'MSG RELAY SERVICE: unknown message!':
                    print("MSG RELAY SERVICE: unknown message!")
                    return None
                
                pk = serialization.load_pem_public_key(response)
                shared_key = self.private_key.exchange(pk)
                derived_key = HKDF(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=None,
                    info=b'handshake data',
                ).derive(shared_key)
                algorithm = AESGCM(derived_key)

                #Decifrar conteudo
                #nonce + ct(content + sign + cert)
                nonce = content[:12]
                encrypted_content = content[12:]
                decrypted_content = algorithm.decrypt(nonce, encrypted_content, None)
                
                #content + sign + cert
                real_content, signANDcert = CRT.unpair(decrypted_content)
                signature, certClient_bytes = CRT.unpair(signANDcert)
                #Passar certificado para objeto
                certClient = CRT.convert_to_certificate(certClient_bytes)
                # Verificar assinatura do cliente
                try:    
                    certClient.public_key().verify(
                        signature,
                        real_content,
                        padding.PSS(
                            mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                    )
                except Exception as e:
                    print("MSG RELAY SERVICE: verification error!" ,e)

                result = real_content.decode()
                #datetime.fromtimestamp(message['time']).strftime('%d/%m/%Y %H:%M')
                print(f"Message number: {num}, From: {sender}, At: {datetime.datetime.fromtimestamp(time)}, With Subject: {subject}\n")
                print(f"Content: {result}\n")
                
            

    async def process(self,reader, writer, msg=b''):
        """ Processa uma mensagem (`bytestring`) enviada pelo SERVIDOR.
            Retorna a mensagem a transmitir como resposta (`None` para
            finalizar ligação) """   

        # servidor só envia mensagens após o cliente escolher o que quer fazer
        if not self.logged:
            #if msg == b"" or msg == None:    
            command = None
            while(command == None or command == 'help' or command == 'exit'):
                new_msg = input("\n\nInsira um comando:\n")
                command = self.my_parser(new_msg)

            # command aqui é sempre válido
            await self.preliminary_exchange(reader, writer)
            self.logged = True
            
            # Vez do client enviar dados
            await self.execute(reader, writer, command)
            
        
        else:
            #ja esta logado, executar comando recebido normalmente                      
       
            while True:
                command = None
                while(command == None or command == 'help'):
                    new_msg = input("\n\nInsira um comando:\n")
                    command = self.my_parser(new_msg)
                await self.execute(reader, writer, command)

                
         

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
    
    try:
        print("Bem vindo ao sistema de mensagens seguro!")
        print("Digite 'help' para listar os comandos ou 'exit' para sair.")

        while True:
            await client.process(reader, writer)

        # writer.write(b'\n')
        # print('Socket closed!')
        # writer.close()
    except KeyboardInterrupt:
        print('Socket closed!')

def run_client():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tcp_echo_client())

run_client()