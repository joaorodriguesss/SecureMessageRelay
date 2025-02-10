#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#define SOCKET_PATH "/tmp/concordia_socket"

int main() {
    int server_fd, client_fd, err;
    struct sockaddr_un server_addr, client_addr;
    socklen_t client_addr_len;

    // Criar socket
    server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return EXIT_FAILURE;
    }

    // Configurar endereço do servidor
    memset(&server_addr, 0, sizeof(struct sockaddr_un));
    server_addr.sun_family = AF_UNIX;
    strncpy(server_addr.sun_path, SOCKET_PATH, sizeof(server_addr.sun_path) - 1);

    // Vincular e escutar
    unlink(SOCKET_PATH);
    if (bind(server_fd, (struct sockaddr *) &server_addr, sizeof(struct sockaddr_un)) < 0) {
        perror("bind");
        return EXIT_FAILURE;
    }

    if (listen(server_fd, 5) < 0) {
        perror("listen");
        return EXIT_FAILURE;
    }

    printf("Server is listening.\n");

    // Aceitar conexões
    client_addr_len = sizeof(struct sockaddr_un);
    client_fd = accept(server_fd, (struct sockaddr *) &client_addr, &client_addr_len);
    if (client_fd < 0) {
        perror("accept");
        return EXIT_FAILURE;
    }

    // Aqui você pode expandir para receber e enviar mensagens...
    
    close(client_fd);
    close(server_fd);
    unlink(SOCKET_PATH);

    return EXIT_SUCCESS;
}