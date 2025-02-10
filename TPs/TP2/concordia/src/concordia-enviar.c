#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <time.h>

#define SERVER_SOCKET_PATH "/var/run/concordia/concordia_socket"

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s destination message...\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    int sock = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    struct sockaddr_un server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sun_family = AF_UNIX;
    strncpy(server_addr.sun_path, SERVER_SOCKET_PATH, sizeof(server_addr.sun_path) - 1);

    if (connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("connect");
        close(sock);
        exit(EXIT_FAILURE);
    }

    // Prepara a mensagem para enviar ao daemon
    char *message = malloc(4096); // Aloca espaço suficiente
    if (!message) {
        perror("malloc");
        close(sock);
        exit(EXIT_FAILURE);
    }

    int uid = getuid(); // Obtém o UID do usuário atual
    snprintf(message, 4096, "enviar %d %s ", uid, argv[1]);

    // Adiciona cada parte da mensagem real
    for (int i = 2; i < argc; i++) {
        strcat(message, argv[i]);
        if (i < argc - 1) strcat(message, " ");
    }

    // Envia a mensagem para o daemon
    if (write(sock, message, strlen(message) + 1) < 0) { // +1 para incluir o terminador nulo
        perror("write");
        close(sock);
        free(message);
        exit(EXIT_FAILURE);
    }

    printf("Message sent: %s\n", message);
    free(message);
    close(sock);
    return EXIT_SUCCESS;
}
