#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#define SOCKET_PATH "/var/run/concordia/concordia_socket"

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <group_name>\n", argv[0]);
        return 1;
    }

    int sock = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sock == -1) {
        perror("socket");
        return 1;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(struct sockaddr_un));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, SOCKET_PATH, sizeof(addr.sun_path) - 1);

    if (connect(sock, (struct sockaddr *)&addr, sizeof(struct sockaddr_un)) == -1) {
        perror("connect");
        close(sock);
        return 1;
    }

    char buffer[1024];
    snprintf(buffer, sizeof(buffer), "listar-grupo %s", argv[1]);
    if (write(sock, buffer, strlen(buffer)) == -1) {
        perror("write");
        close(sock);
        return 1;
    }

    // Agora lê a resposta
    ssize_t numRead = read(sock, buffer, sizeof(buffer) - 1);
    if (numRead > 0) {
        buffer[numRead] = '\0';  // Garante que é uma string terminada em NULL
        printf("%s", buffer);
    } else {
        fprintf(stderr, "Failed to receive response from daemon.\n");
    }

    close(sock);
    return 0;
}
