# NÃO ESTÁ ATUALIZADO
# Projeto Concordia

Projeto Concordia é um sistema de mensagens local para utilizadores de um sistema Linux, desenvolvido como parte da disciplina de Segurança de Sistemas Informáticos da Universidade do Minho.

## Funcionalidades

- Envio de mensagens entre utilizadores locais.
- Criação e gestão de grupos privados de conversa.
- Suporte para comunicação assíncrona semelhante ao email.
- Mensagens com limite de 512 caracteres.
- Gerenciamento de utilizadores e grupos através de comandos de linha.

## Requisitos

- Sistema operacional Linux.
- OpenSSL para criptografia de mensagens.

## Instalação

1. Clone o repositório: https://github.com/uminho-lei-ssi/2324-G29.git

2. Navegue até o diretório do projeto: cd TPs/TP2/concordia

3. Dê permissão de execução para os scripts: chmod +x /home/joaorodrigues61/GitHub\ Repositorys/2324-G29/TPs/TP2/concordia/bin/*.sh

## Configuração

Para configurar o sistema e iniciar o serviço:

1. Copie o arquivo de serviço systemd para o diretório apropriado: sudo cp systemd/concordia.service /etc/systemd/system/

2. Recarregue os daemons do systemd para registar o serviço: sudo systemctl daemon-reload

3. Habilite o serviço: sudo systemctl enable concordia.service 

4. Inicie o serviço: sudo systemctl start concordia.service

5. Verifique o Status do Serviço: sudo systemctl status concordia.service

## Uso

### Enviar uma Mensagem

bin/concordia-enviar.sh nome_do_utulizador "Mensagem"

### Listar Mensagens

bin/concordia-listar.sh

### Criar um Grupo

bin/concordia-grupo-criar.sh nome_do_grupo
