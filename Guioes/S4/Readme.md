# Respostas das Questões
## Q2
    Considerando um NONCE fixo, esse mesmo NONCE seria sempre igual para cada mensagem criptografada. Desta maneira caso um atacante descubra informações de dados da mensagem inicial, não tendo acesso à mensagem cifrada, conseguiria recuperar a chave secreta.
    
    Um atacante com o texto cifrado de uma comunicação pode até retransmitir essa mensagem cifrada para alcançar o mesmo efeito, já que o NONCE é fixo

    Em resumo um NONCE fixo é extremamente inseguro e deve ser evitado a todo custo numa medida de garantir segurança e eficácia das cifras de fluxo.

# Relatório do Guião da Semana 4
    Aprofundamento de cifras de fluxo, com utilização do ChaCha20