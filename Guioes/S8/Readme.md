# Respostas das Questões

## Q1 / Q2 

    touch exemplo.txt
    mkdir myDir

Criado um ficheiro exemplo.txt e uma diretoria

    chmod 750 exemplo.txt 
Alterado para o owner conseguir fazer tudo, o grupo apenas ler e executar e os outros nao fazerem nada

    useradd SuperHerói
Adcionado user SuperHerói

    sudo chown SuperHerói exemplo.txt 
Agora SuperHerói é o owner

    groupadd trolhas
Criado o grupo trolhas

    sudo chgrp trolhas exemplo.txt 

    umask 754
Owner tudo, grupo ler e executar e outros apenas ler


    su SuperHerói

## Q3

Criado um programa em C e o excutável chamado "roda"

- sudo chmod 754 roda
- ls -l
- -rwxr-xr-- 1 fikiling   fikiling 16048 abr 15 10:11 roda
- sudo chmod u+s roda        
- ls -l
- -rwsr-xr-- 1 fikiling   fikiling 16048 abr 15 10:11 roda

-rwsr-s--x 1 SuperHerói fikiling 16320 abr 15 10:46 roda
alteradas as permissoes para quem executar do grupo usar as permissoes do SuperHeroi 

executado o programa como fikiling 

./roda
User ID: 1000
Group ID: 1000
Altos estrondos 

e conseguimos executar


## Q4

getfacl roda 
# file: roda
# owner: SuperHerói
# group: fikiling
# flags: ss-
user::rwx
group::r-x
other::--x


sudo setfacl -m u:fikiling:rw roda

getfacl roda 
# file: roda
# owner: SuperHerói
# group: fikiling
# flags: ss-
user::rwx
user:fikiling:rw-
group::r-x
mask::rwx
other::--x

agora o user fikiling tem permissoes unicas sobre o ficheiro


# Relatório do Guião da Semana 8
    Aprofundimento de conhecimentos sobre comandos sobre permissões de ficheiros e diretórias em linux