# Código baseado em https://docs.python.org/3.6/library/asyncio-stream.html#tcp-echo-client-using-streams
import asyncio
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

conn_cnt = 0
conn_port = 8443
max_msg_size = 9999
password = "gghlioucfcghjoi"

def pad_string_to_32_bytes(s):
    if len(s) >= 32:
        return s[:32]
    else:
        return s.ljust(32, b'\0')

class ServerWorker(object):
    """ Classe que implementa a funcionalidade do SERVIDOR. """
    def __init__(self, cnt, addr=None):
        """ Construtor da classe. """
        self.id = cnt
        self.addr = addr
        self.msg_cnt = 0
    def process(self, msg):
        """ Processa uma mensagem (`bytestring`) enviada pelo CLIENTE.
            Retorna a mensagem a transmitir como resposta (`None` para
            finalizar ligação) """
        self.msg_cnt += 1
        #
        # ALTERAR AQUI COMPORTAMENTO DO SERVIDOR
        #        
        if not msg:
            # Se a mensagem estiver vazia, envie uma resposta para manter a conexão ativa
            return b'Keep alive'
        
        nonce_r = msg[:12]
        ciphertext = msg[12:]
        passW = pad_string_to_32_bytes(password.encode())
        aesgcm = AESGCM(passW)
        decrypt_msg = aesgcm.decrypt(nonce_r, ciphertext, None).decode()
        print("%r" % decrypt_msg)

        print('%d : %r' % (self.id, decrypt_msg))

        # Encrypt messagem de volta
        message2Ret = decrypt_msg.upper().encode()

        nonce = os.urandom(12)
        aesgcm = AESGCM(passW)
        ciphertext = aesgcm.encrypt(nonce, message2Ret, None)
        allM = nonce + ciphertext
        #
        return allM if len(allM)>0 else None


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