#define _DEFAULT_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>
#include <pwd.h>
#include <limits.h>
#include <sys/socket.h>
#include <sys/un.h>

#define BASE_PATH "/var/lib/concordia_data"
#define SOCKET_PATH "/var/run/concordia/concordia_socket"

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s message_number\n", argv[0]);
        return EXIT_FAILURE;
    }

    struct passwd *pwd = getpwuid(getuid());
    if (!pwd) {
        fprintf(stderr, "Failed to get user information.\n");
        return EXIT_FAILURE;
    }

    char unread_path[PATH_MAX], read_path[PATH_MAX];
    snprintf(unread_path, sizeof(unread_path), "%s/%s/messages/unread", BASE_PATH, pwd->pw_name);
    snprintf(read_path, sizeof(read_path), "%s/%s/messages/read", BASE_PATH, pwd->pw_name);

    char filepath[PATH_MAX], new_path[PATH_MAX];
    FILE *file = NULL;

    // Construct file path for unread messages
    if (snprintf(filepath, sizeof(filepath), "%s/%s.txt", unread_path, argv[1]) >= sizeof(filepath)) {
        fprintf(stderr, "File path is too long.\n");
        return EXIT_FAILURE;
    }
    
    file = fopen(filepath, "r");

    // If not found in unread, try read
    if (!file) {
        if (snprintf(filepath, sizeof(filepath), "%s/%s.txt", read_path, argv[1]) >= sizeof(filepath)) {
            fprintf(stderr, "File path is too long.\n");
            return EXIT_FAILURE;
        }
        file = fopen(filepath, "r");
    }

    if (!file) {
        fprintf(stderr, "Message %s not found in either unread or read folders.\n", argv[1]);
        return EXIT_FAILURE;
    }

    // Display the content of the message
    char line[1024];
    while (fgets(line, sizeof(line), file)) {
        printf("%s", line);
    }
    printf("\n");
    fclose(file);

    // Move the file to read if it was in unread
    if (strstr(filepath, "unread")) {
        if (snprintf(new_path, sizeof(new_path), "%s/%s.txt", read_path, argv[1]) >= sizeof(new_path)) {
            fprintf(stderr, "New file path is too long.\n");
            return EXIT_FAILURE;
        }
        rename(filepath, new_path);
        printf("\n");
    }

    return EXIT_SUCCESS;
}