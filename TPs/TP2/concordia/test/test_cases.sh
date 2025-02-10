#!/bin/bash

# Diretório base dos scripts
SCRIPT_DIR="/path/to/concordia/bin"

# Utilizador de teste
TEST_USER="testuser"

# Nome do grupo de teste
TEST_GROUP="testgroup"

# Mensagem de teste
TEST_MESSAGE="Hello, this is a test message."

# Funções de teste
function test_send_message() {
    echo "Testing message sending..."
    $SCRIPT_DIR/concordia-enviar.sh $TEST_USER "$TEST_MESSAGE"
}

function test_list_messages() {
    echo "Testing message listing..."
    $SCRIPT_DIR/concordia-listar.sh
}

function test_create_group() {
    echo "Testing group creation..."
    $SCRIPT_DIR/concordia-grupo-criar.sh $TEST_GROUP
}

function test_add_group_member() {
    echo "Testing adding a member to the group..."
    $SCRIPT_DIR/concordia-grupo-destinatario-adicionar.sh $TEST_GROUP $TEST_USER
}

function test_list_group_members() {
    echo "Testing listing group members..."
    $SCRIPT_DIR/concordia-grupo-listar.sh $TEST_GROUP
}

function test_remove_group_member() {
    echo "Testing removing a member from the group..."
    $SCRIPT_DIR/concordia-grupo-destinatario-remover.sh $TEST_GROUP $TEST_USER
}

function test_remove_group() {
    echo "Testing group removal..."
    $SCRIPT_DIR/concordia-grupo-remover.sh $TEST_GROUP
}

# Executa os testes
test_send_message
test_list_messages
test_create_group
test_add_group_member
test_list_group_members
test_remove_group_member
test_remove_group

echo "Tests completed."
