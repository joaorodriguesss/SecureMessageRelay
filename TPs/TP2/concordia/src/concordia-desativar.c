#include <stdio.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <stdlib.h>

#define SOCKET_PATH "/var/run/concordia/concordia_socket"

int main() {
    int sock = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("socket creation failed");
        return 1;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strcpy(addr.sun_path, SOCKET_PATH);

    if (connect(sock, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
        perror("connect failed");
        close(sock);
        return 1;
    }

    int uid = getuid();  // Pega o UID do usuário atual
    char message[256];
    sprintf(message, "desativar %d", uid);
    if (write(sock, message, strlen(message) + 1) < 0) {  // +1 para incluir o terminador nulo
        perror("write to socket failed");
        close(sock);
        return 1;
    }

    printf("Deactivation request sent for UID %d\n", uid);

    close(sock);
    return 0;
}
