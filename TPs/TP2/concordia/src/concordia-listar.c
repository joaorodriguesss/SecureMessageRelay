#define _DEFAULT_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <pwd.h>
#include <grp.h>

#define BASE_PATH "/var/lib/concordia_data"

void list_directory_contents(const char *path) {
    struct dirent **namelist;
    int n = scandir(path, &namelist, NULL, alphasort);
    if (n < 0) {
        perror("scandir");
        return;
    }

    char full_path[2048];
    FILE *file;
    int message_id;
    char sender[256], date[256];

    for (int index = 0; index < n; index++) {
        if (namelist[index]->d_name[0] == '.') {
            free(namelist[index]);
            continue;
        }

        sscanf(namelist[index]->d_name, "%d.txt", &message_id);

        snprintf(full_path, sizeof(full_path), "%s/%s", path, namelist[index]->d_name);
        file = fopen(full_path, "r");
        if (!file) {
            perror("Failed to open message file");
            free(namelist[index]);
            continue;
        }

        // Read and parse the necessary information from the file
        if (fgets(date, sizeof(date), file) && fgets(sender, sizeof(sender), file)) {
            // Assuming the first line is the date and the second line is the sender
            char *newline = strchr(date, '\n');
            if (newline) *newline = '\0';  // Remove newline character
            newline = strchr(sender, '\n');
            if (newline) *newline = '\0';  // Remove newline character

            printf("%d | %s | %s\n", message_id, sender + 8, date + 17);  // Skip the prefix part of the metadata
        }

        fclose(file);
        free(namelist[index]);
    }
    free(namelist);
}

// // Função auxiliar para verificar se o usuário é membro do grupo
// int is_user_member_of_group(const char *username, const char *groupname) {
//     struct group *grp = getgrnam(groupname);
//     if (grp == NULL) {
//         return 0;  // Grupo não encontrado
//     }
//     for (char **members = grp->gr_mem; *members; members++) {
//         if (strcmp(*members, username) == 0) {
//             return 1;
//         }
//     }
//     return 0;
// }

// // Função para listar mensagens de grupos
// void list_group_messages(const char *username) {
//     DIR *dir = opendir("/var/lib/concordia_data/groups");
//     if (dir == NULL) {
//         perror("Failed to open groups directory");
//         return;
//     }
//     struct dirent *entry;
//     while ((entry = readdir(dir)) != NULL) {
//         if (entry->d_type == DT_DIR && entry->d_name[0] != '.') {
//             if (is_user_member_of_group(username, entry->d_name)) {
//                 char group_messages_path[1024];
//                 snprintf(group_messages_path, sizeof(group_messages_path), "/var/lib/concordia_data/groups/%s", entry->d_name);
//                 struct stat st;
//                 if (stat(group_messages_path, &st) == 0) {
//                     printf("Permissions for group '%s': %o\n", entry->d_name, st.st_mode & (S_IRWXU | S_IRWXG | S_IRWXO));
//                 }
//                 printf("Messages from group '%s':\n", entry->d_name);
//                 list_directory_contents(group_messages_path);
//             }
//         }
//     }
//     closedir(dir);
// }


void list_messages(const char *username, int all) {
    char path[1024];
    printf("Listing all messages for %s:\n", username);

    printf("Personal unread messages:\n");
    snprintf(path, sizeof(path), "%s/%s/messages/unread", BASE_PATH, username);
    list_directory_contents(path);

    printf("Personal read messages:\n");
    snprintf(path, sizeof(path), "%s/%s/messages/read", BASE_PATH, username);
    list_directory_contents(path);

    // // Listar mensagens de grupos
    // list_group_messages(username);
}

int main(int argc, char *argv[]) {
    struct passwd *pwd = getpwuid(getuid());
    if (!pwd) {
        fprintf(stderr, "Failed to get user information.\n");
        return EXIT_FAILURE;
    }

    int all = 0; // Default to show only unread messages
    if (argc > 1 && strcmp(argv[1], "-a") == 0) {
        all = 1;
    }

    list_messages(pwd->pw_name, all);
    return EXIT_SUCCESS;
}

