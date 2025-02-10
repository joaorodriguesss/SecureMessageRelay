# Serviço de Message Relay com Garantia de Autenticidade

## Constituição do Grupo de Trabalho (G29)

- **A100696** Filipe Gonçalves
- **A100711** João Rodrigues 
- **A100754** Rafael Peixoto

## Descrição do Projeto

Pretende-se construir um serviço de Message Relay que permita aos membros de uma organização trocarem mensagens com garantias de autenticidade. O serviço será suportado por um servidor responsável por manter o estado da aplicação e interagir com os utilizadores do sistema. Todo os intervenientes do sistema (servidor e utilizadores) serão identificados por um identificador único UID.


## Funcionalidades

### Cliente

O cliente interage com o sistema através dos seguintes comandos:
- Enviar mensagem para um UID específico.
- Solicitar ao servidor a lista de mensagens não lidas.
- Receber uma mensagem específica da fila.
- Assistência sobre o uso do programa.

### Servidor

O servidor mantém o estado da aplicação, gerencia as solicitações dos usuários e garante a entrega de mensagens com autenticidade verificável.

### Segurança
Todas as comunicações são protegidas contra acesso e manipulação não autorizados.
Utilização de certificados X509 para identificação e credenciais dos utilizadores.
Verificação da autenticidade das mensagens recebidas

## Implementação

### Estrutura e Design

- **msg_server.py:** Implementa a lógica do servidor, mantendo o estado da aplicação e respondendo às solicitações dos clientes.
- **msg_client.py:** Fornece a interface para o usuário interagir com o sistema, enviar mensagens e consultar a fila de mensagens não lidas e consultar uma mensagem em específico.
- **CRT__Validation.py:** Disponibiliza funções de validação dos certificados utilizados pelos clientes e pelo servidor, garantindo a autenticidade das partes.

### Segurança

Para cada mensagem enviada entre o cliente e o servidor com destino a outro cliente, o conteudo da mensagem é encriptado com a chave derivada entre os dois clientes, e adicionado a assinatura do conteudo e o certificado do cliente que a envia para o cliente que a recebe conseguir confirmar que de facto foi enviada para ele e porque quem diz enviar, e desta maneira o sercvidor não tem acesso ao conteúdo enviado pelo cliente, uma vez encriptado com a chaave derivada dos dois clientes
Quando o cliente faz o comando getmsg, é lhe enviado o conteudo encriptado com o algoritmo das chaves derivadas dos dois clientes, o cliente processa então à decriptação do conteudo, verifica a assinatura com o certificado e após estas validações, confirma que foi enviado para ele por quem diz enviar e lê o conteúdo da mensagem 
Implementado seguindo as melhores práticas de segurança, incluindo o uso de bibliotecas criptográficas para a gestão de certificados e chaves privadas.

## Melhorias e Valorizações

- **Recibos que atestem que uma mensagem foi submetida ao sistema:** Quando um cliente envia uma mensagem recebe sempre uma mensagem proveniente do servidor que diz se o processo de envio occoreu ou não com sucesso. 
- **Log do Sistema:** Introdução de um sistema de log no servidor para registrar transações e facilitar a auditoria.

## Guia de Utilização

Do lado do cliente podem ser inseridos comandos, sendo eles:

- **help** - imprime instruções de ajuda.
- **send {UID} {SUBJECT}** - sendo que **{UID}** é constituído apenas por uma palavra (por exemplo: "MSG_CLI2") e **{SUBJECT}** pode ter várias palavras. Depois do msg_client dar parse a um send com 3 ou mais argumentos, imprime "Digite o corpo da mensagem:" e o usuário deve escrever o corpo da sua mensagem em seguida.
- **askqueue** - solicita ao servidor que lhe envie a lista de mensagens não lidas da queue do utilizador. Para cada mensagem na queue, é devolvida uma linha contendo: {NUM}:{SENDER}:{TIME}:{SUBJECT}, onde {NUM} é o número de ordem da mensagem na queue e {TIME} um timestamp adicionado pelo servidor que regista a altura em que a mensagem foi recebida.
-**user {FNAME}** – argumento opcional (que deverá surgir sempre em primeiro lugar) que especifica o ficheiro com dados do utilizador. Por omissão, será assumido que esse ficheiro é userdata.p12. Exemplo de caso de uso "-user MSG_CLI2.p12 askqueue", que devolve a lista de mensagens não lidas de MSG_CLI2 e o terminal passa a ser do usuário com {UID} MSG_CLI2, o segundo comando que for inserido nunca pode ser antecedido por "-user {FNAME}" visto que aquele terminal já foi designado a um {UID}.

## Conclusão

Este projeto implementa um sistema de Message Relay robusto e seguro, fornecendo uma plataforma confiável para comunicação dentro de uma organização. Através da aplicação de componentes criptográficos, garantimos a autenticidade e a segurança das mensagens trocadas entre os usuários.