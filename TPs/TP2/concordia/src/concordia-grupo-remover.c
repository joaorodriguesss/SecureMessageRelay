#include <stdio.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <sys/types.h>
#include <unistd.h>

#define SOCKET_PATH "/var/run/concordia/concordia_socket"

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <group_name>\n", argv[0]);
        return 1;
    }

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
    char command[256];
    sprintf(command, "remover-grupo %s %d", argv[1], uid);
    if (write(sock, command, strlen(command) + 1) < 0) {
        perror("write to socket failed");
        close(sock);
        return 1;
    }

    printf("Request to remove group '%s' sent successfully.\n", argv[1]);

    close(sock);
    return 0;
}
