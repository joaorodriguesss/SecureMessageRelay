#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#define SOCKET_PATH "/var/run/concordia/concordia_socket"

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Usage: %s <group_name> <uid>\n", argv[0]);
        return EXIT_FAILURE;
    }

    const char *group_name = argv[1];
    int uid = atoi(argv[2]);

    int sock = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("socket");
        return EXIT_FAILURE;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(struct sockaddr_un));
    addr.sun_family = AF_UNIX;
    strcpy(addr.sun_path, SOCKET_PATH);

    if (connect(sock, (struct sockaddr *)&addr, sizeof(struct sockaddr_un)) == -1) {
        perror("connect");
        return EXIT_FAILURE;
    }

    char buffer[1024];
    sprintf(buffer, "remover-destinatario %s %d", group_name, uid);
    write(sock, buffer, strlen(buffer) + 1);

    // Receive feedback
    int len = read(sock, buffer, sizeof(buffer) - 1);
    if (len > 0) {
        buffer[len] = '\0';
        printf("%s", buffer);
    }

    close(sock);
    return EXIT_SUCCESS;
}
