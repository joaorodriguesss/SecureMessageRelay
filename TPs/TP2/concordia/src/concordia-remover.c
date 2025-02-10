#define _DEFAULT_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <pwd.h>
#include <limits.h>
#include <sys/stat.h>

#define BASE_PATH "/var/lib/concordia_data"
#define SOCKET_PATH "/var/run/concordia/concordia_socket"

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s message_index\n", argv[0]);
        return EXIT_FAILURE;
    }

    struct passwd *pwd = getpwuid(getuid());
    if (!pwd) {
        fprintf(stderr, "Failed to get user information.\n");
        return EXIT_FAILURE;
    }

    // Formata o nome do arquivo esperado com a extensão .txt
    char filename[256];
    snprintf(filename, sizeof(filename), "%s.txt", argv[1]);

    char unread_path[PATH_MAX], read_path[PATH_MAX];
    snprintf(unread_path, sizeof(unread_path), "%s/%s/messages/unread/%s", BASE_PATH, pwd->pw_name, filename);
    snprintf(read_path, sizeof(read_path), "%s/%s/messages/read/%s", BASE_PATH, pwd->pw_name, filename);

    // Verifica se o arquivo existe em 'unread'
    struct stat statbuf;
    int exist_unread = stat(unread_path, &statbuf);
    int exist_read = -1;
    if (exist_unread != 0) {
        exist_read = stat(read_path, &statbuf);
    }

    int sock = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("socket creation failed");
        return EXIT_FAILURE;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strcpy(addr.sun_path, SOCKET_PATH);

    if (connect(sock, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
        perror("connect failed");
        close(sock);
        return EXIT_FAILURE;
    }

    char command[5120];
    if (exist_unread == 0) {
        snprintf(command, sizeof(command), "remove %d %s", getuid(), unread_path);
    } else if (exist_read == 0) {
        snprintf(command, sizeof(command), "remove %d %s", getuid(), read_path);
    } else {
        fprintf(stderr, "No such message to remove.\n");
        close(sock);
        return EXIT_FAILURE;
    }

    if (write(sock, command, strlen(command) + 1) < 0) {
        perror("write to socket failed");
        close(sock);
        return EXIT_FAILURE;
    }

    printf("Requested to remove message %s.\n", filename);
    close(sock);
    return EXIT_SUCCESS;
}
