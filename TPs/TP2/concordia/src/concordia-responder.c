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

#define SERVER_SOCKET_PATH "/var/run/concordia/concordia_socket"
#define BASE_PATH "/var/lib/concordia_data"

char* get_username_by_uid(int uid) {
    struct passwd *pwd = getpwuid(uid);
    if (pwd == NULL) {
        return NULL;
    }
    return strdup(pwd->pw_name);  // Aloca e retorna uma cópia do nome
}

int get_sender_from_message(const char* message_filename, int *sender_uid, char **sender_username) {
    struct passwd *pwd = getpwuid(getuid());
    if (!pwd) {
        fprintf(stderr, "Failed to get user information.\n");
        return -1;
    }

    char unread_path[PATH_MAX], read_path[PATH_MAX];
    snprintf(unread_path, sizeof(unread_path), "%s/%s/messages/unread/%s.txt", BASE_PATH, pwd->pw_name, message_filename);
    snprintf(read_path, sizeof(read_path), "%s/%s/messages/read/%s.txt", BASE_PATH, pwd->pw_name, message_filename);

    char *path_to_use = NULL;
    struct stat statbuf;
    if (stat(unread_path, &statbuf) == 0) {
        path_to_use = unread_path;
    } else if (stat(read_path, &statbuf) == 0) {
        path_to_use = read_path;
    } else {
        fprintf(stderr, "Message file not found.\n");
        return -1;
    }

    FILE *file = fopen(path_to_use, "r");
    if (file == NULL) {
        perror("Error opening message file");
        return -1;
    }

    char line[1024];
    while (fgets(line, sizeof(line), file)) {
        if (sscanf(line, "Sender: %*s (UID: %d)", sender_uid) == 1) {
            *sender_username = get_username_by_uid(*sender_uid);
            fclose(file);
            return 0;
        }
    }

    fclose(file);
    return -1;
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s message_filename message_response...\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    char *message_filename = argv[1];  // Assume filename is passed as the first argument

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

    int sender_uid;
    char *sender_username = NULL;
    if (get_sender_from_message(message_filename, &sender_uid, &sender_username) != 0) {
        fprintf(stderr, "Failed to get sender info\n");
        close(sock);
        return EXIT_FAILURE;
    }

    char *response_message = malloc(4096);  // Allocate memory for the response message
    if (!response_message) {
        perror("malloc");
        close(sock);
        free(sender_username);
        exit(EXIT_FAILURE);
    }

    snprintf(response_message, 4096, "enviar %d %s ", sender_uid, sender_username);  // Format the command to send response
    for (int i = 2; i < argc; i++) {
        strcat(response_message, argv[i]);
        if (i < argc - 1) strcat(response_message, " ");
    }

    if (write(sock, response_message, strlen(response_message) + 1) < 0) {
        perror("write");
        close(sock);
        free(response_message);
        free(sender_username);
        return EXIT_FAILURE;
    }

    printf("Response sent: %s\n", response_message);
    free(response_message);
    free(sender_username);
    close(sock);
    return EXIT_SUCCESS;
}
