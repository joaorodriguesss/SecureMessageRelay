#define _DEFAULT_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <pwd.h>
#include <grp.h>

#define BASE_PATH "/var/lib/concordia_data/groups"
#define MAX_PATH_LENGTH 2048  // Aumentando o tamanho do buffer

// Função para comparar dois nomes de arquivo baseados em seus números inteiros
int numeric_dirent_comparator(const struct dirent **a, const struct dirent **b) {
    int valA = atoi((*a)->d_name);
    int valB = atoi((*b)->d_name);
    return valA - valB;
}

// Função para verificar se o usuário é membro do grupo
int is_user_member_of_group(const char *username, const char *groupname) {
    struct group *grp = getgrnam(groupname);
    struct stat statbuf;
    char group_dir[1024];
    snprintf(group_dir, sizeof(group_dir), "%s/%s", BASE_PATH, groupname);

    if (stat(group_dir, &statbuf) == -1) {
        perror("stat");
        return 0;
    }

    // Verifica se o usuário é o proprietário do diretório
    struct passwd *pwd = getpwuid(statbuf.st_uid);
    if (pwd && strcmp(pwd->pw_name, username) == 0) {
        return 1;  // O proprietário do diretório é automaticamente considerado membro
    }

    if (!grp) {
        printf("Group '%s' not found.\n", groupname);
        return 0;
    }

    // Iterar pelos membros do grupo
    for (char **members = grp->gr_mem; *members; members++) {
        if (strcmp(*members, username) == 0) {
            return 1;  // Usuário é membro do grupo
        }
    }
    return 0;  // Usuário não é membro do grupo
}

// Função para ler e exibir mensagens de um grupo específico
void read_group_messages(const char *groupname) {
    char path[MAX_PATH_LENGTH];
    snprintf(path, sizeof(path), "%s/%s", BASE_PATH, groupname);

    struct dirent **namelist;
    int n = scandir(path, &namelist, NULL, (int (*)(const struct dirent **, const struct dirent **)) numeric_dirent_comparator);
    if (n < 0) {
        perror("Failed to scan directory");
        return;
    }

    for (int i = 0; i < n; i++) {
        if (namelist[i]->d_type == DT_REG) {
            char file_path[MAX_PATH_LENGTH];
            if (snprintf(file_path, sizeof(file_path), "%s/%s", path, namelist[i]->d_name) >= sizeof(file_path)) {
                fprintf(stderr, "Path buffer is too small for the file path.\n");
                continue;
            }

            FILE *file = fopen(file_path, "r");
            if (!file) {
                perror("Failed to open message file");
                continue;
            }

            char line[1024], sender[256] = "", message[1024] = "";
            while (fgets(line, sizeof(line), file)) {
                if (strncmp(line, "Sender: ", 8) == 0) {
                    strcpy(sender, line + 8);
                    char *newline = strchr(sender, '\n');
                    if (newline) *newline = '\0';  // Remove newline
                } else if (strncmp(line, "Message:\n", 9) == 0) {
                    while (fgets(line, sizeof(line), file)) {
                        strcat(message, line);
                    }
                }
            }
            sender[strcspn(sender, "\n")] = '\0';  // Ensure no newline at end
            message[strcspn(message, "\n")] = '\0';  // Ensure no newline at end
            printf("%s | %s\n", sender, message);
            fclose(file);
        }
        free(namelist[i]);
    }
    free(namelist);
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s groupname\n", argv[0]);
        return EXIT_FAILURE;
    }

    struct passwd *pwd = getpwuid(getuid());
    if (!pwd) {
        fprintf(stderr, "Failed to get user information.\n");
        return EXIT_FAILURE;
    }

    if (!is_user_member_of_group(pwd->pw_name, argv[1])) {
        fprintf(stderr, "Access denied: You are not a member of group '%s'.\n", argv[1]);
        return EXIT_FAILURE;
    }

    read_group_messages(argv[1]);
    return EXIT_SUCCESS;
}
