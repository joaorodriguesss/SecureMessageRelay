#define _DEFAULT_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <string.h>
#include <sys/stat.h> 
#include <errno.h>
#include <time.h>
#include <pwd.h>
#include <dirent.h> 
#include <fcntl.h>
#include <unistd.h>
#include <grp.h>
#include <ctype.h>
#include <sys/wait.h>

#define SOCKET_DIR "/var/run/concordia"
#define SOCKET_PATH "/var/run/concordia/concordia_socket"
#define BASE_PATH "/var/lib/concordia_data" 

#define MAX_USERS 100
#define MAX_PATH_LENGTH 1024 

// Estrutura para manter a lista de UIDs
typedef struct {
    int uids[MAX_USERS];
    int count;
} ActiveUsers;

ActiveUsers activeUsers = { .count = 0 };

// Função para verificar se um UID está ativo
int is_user_active(int uid) {
    for (int i = 0; i < activeUsers.count; i++) {
        if (activeUsers.uids[i] == uid) {
            return 1;  // UID encontrado na lista
        }
    }
    return 0;  // UID não encontrado
}

// Função para ter username pelo UID
char* get_username_by_uid(int uid) {
    struct passwd *pwd = getpwuid(uid);
    if (pwd == NULL) {
        return NULL;
    }
    return pwd->pw_name;
}

// Função para adicionar um UID à lista
void add_user(int uid) {
    if (is_user_active(uid) == 1) {
        printf("Utilizador já está ativado.\n");
    } else {
        if (activeUsers.count < MAX_USERS) {
            activeUsers.uids[activeUsers.count++] = uid;
            printf("UID %d adicionado.\n", uid);
        } else {
            printf("Máximo de utilizadores atingido.\n");
        }
    }
}

// Função para remover um UID da lista
void remove_user(int uid) {
    int index = -1;
    for (int i = 0; i < activeUsers.count; i++) {
        if (activeUsers.uids[i] == uid) {
            index = i;
            break;
        }
    }
    if (index != -1) {
        activeUsers.uids[index] = activeUsers.uids[activeUsers.count - 1];
        activeUsers.count--;
        printf("UID %d removido.\n", uid);
    } else {
        printf("UID %d não encontrado.\n", uid);
    }
}

// Função para imprimir os UIDs ativos
void print_active_users() {
    printf("Usuários ativos: ");
    for (int i = 0; i < activeUsers.count; i++) {
        printf("%d ", activeUsers.uids[i]);
    }
    printf("\n");
}

// Função para ler um diretório e encontrar o maior número de arquivo
int find_max_in_dir(const char *path) {
    DIR *dir = opendir(path);
    struct dirent *entry;
    int max = 0;
    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type == DT_REG) { // Se for um arquivo regular
            int num = atoi(entry->d_name);
            if (num > max) {
                max = num;
            }
        }
    }
    closedir(dir);
    return max;
}

int find_max_in_dir_group(const char *path) {
    DIR *dir = opendir(path);
    struct dirent *entry;
    int max = 1000;
    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type == DT_REG) { // Se for um arquivo regular
            int num = atoi(entry->d_name);
            if (num > max) {
                max = num;
            }
        }
    }
    closedir(dir);
    return max;
}

int get_next_message_number(const char *base_path, const char *username) {
    char unread_path[1024], read_path[1024];
    snprintf(unread_path, sizeof(unread_path), "%s/%s/messages/unread", base_path, username);
    snprintf(read_path, sizeof(read_path), "%s/%s/messages/read", base_path, username);

    int max_number = 0;
    int max_unread = find_max_in_dir(unread_path);
    int max_read = find_max_in_dir(read_path);

    max_number = (max_unread > max_read) ? max_unread : max_read;
    return max_number + 1; // Retorna o próximo número disponível
}

int get_next_group_message_number(const char *base_path, const char *group_name) {
    char path[1024];
    snprintf(path, sizeof(path), "%s/groups/%s", base_path, group_name);

    return find_max_in_dir_group(path) + 1;  // Retorna o próximo número disponível diretamente do diretório do grupo
}

void save_message_to_user(const char *dest, const char *msg, int sender_uid) {
    int message_number = get_next_message_number(BASE_PATH, dest);
    char filepath[1024];
    int fd;
    char metadata[1024];
    struct tm *tm_now = localtime(&(time_t){time(NULL)});
    char time_str[100];

    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_now);
    int message_length = strlen(msg);

    char *sender_username = get_username_by_uid(sender_uid);
    if (sender_username == NULL) {
        fprintf(stderr, "Failed to find user for UID %d\n", sender_uid);
        return;
    }

    snprintf(filepath, sizeof(filepath), "%s/%s/messages/unread/%d.txt", BASE_PATH, dest, message_number);
    printf("Attempting to save message to: %s\n", filepath);

    fd = open(filepath, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd == -1) {
        fprintf(stderr, "Failed to open file: %s\n", strerror(errno));
        return;
    }

    snprintf(metadata, sizeof(metadata), "Date of Receipt: %s\nSender: %s (UID: %d)\nMessage Size: %d bytes\n\nMessage:\n%s",
             time_str, sender_username, sender_uid, message_length, msg);

    if (write(fd, metadata, strlen(metadata)) == -1) {
        fprintf(stderr, "Failed to write to file: %s\n", strerror(errno));
    }

    printf("Message saved in: %s\n", filepath);

    close(fd);
}

// void save_message_to_group(const char *group_name, const char *msg, int sender_uid) {
//     char group_path[1024];
//     snprintf(group_path, sizeof(group_path), "%s/groups/%s", BASE_PATH, group_name);

//     int message_number = get_next_group_message_number(BASE_PATH, group_name);
//     char filepath[2048];
//     snprintf(filepath, sizeof(filepath), "%s/%d.txt", group_path, message_number);

//     int fd = open(filepath, O_WRONLY | O_CREAT | O_TRUNC, 0644);
//     if (fd == -1) {
//         fprintf(stderr, "Failed to open file: %s\n", strerror(errno));
//         return;
//     }

//     struct tm *tm_now = localtime(&(time_t){time(NULL)});
//     char time_str[100];
//     strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_now);
//     int message_length = strlen(msg);
//     char *sender_username = get_username_by_uid(sender_uid);
//     char metadata[2048];
//     snprintf(metadata, sizeof(metadata), "Date of Receipt: %s\nSender: %s (UID: %d)\nMessage Size: %d bytes\n\nMessage:\n%s",
//              time_str, sender_username, sender_uid, message_length, msg);

//     if (write(fd, metadata, strlen(metadata)) == -1) {
//         fprintf(stderr, "Failed to write to file: %s\n", strerror(errno));
//     }

//     printf("Message saved in: %s\n", filepath);

//     close(fd);
// }



// void save_message_to_group(const char *group_name, const char *msg, int sender_uid) {
//     char group_path[1024];
//     snprintf(group_path, sizeof(group_path), "%s/groups/%s", BASE_PATH, group_name);

//     int message_number = get_next_group_message_number(BASE_PATH, group_name);
//     char filepath[2048];
//     snprintf(filepath, sizeof(filepath), "%s/%d.txt", group_path, message_number);

//     int fd = open(filepath, O_WRONLY | O_CREAT | O_TRUNC, 0666);
//     if (fd == -1) {
//         fprintf(stderr, "Failed to open file: %s\n", strerror(errno));
//         return;
//     }

//     struct tm *tm_now = localtime(&(time_t){time(NULL)});
//     char time_str[100];
//     strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_now);
//     int message_length = strlen(msg);
//     char *sender_username = get_username_by_uid(sender_uid);
//     char metadata[2048];
//     snprintf(metadata, sizeof(metadata), "Date of Receipt: %s\nSender: %s (UID: %d)\nMessage Size: %d bytes\n\nMessage:\n%s",
//              time_str, sender_username, sender_uid, message_length, msg);

//     if (write(fd, metadata, strlen(metadata)) == -1) {
//         fprintf(stderr, "Failed to write to file: %s\n", strerror(errno));
//     }

//     printf("Message saved in: %s\n", filepath);

//     close(fd);
// }


void save_message_to_group(const char *group_name, const char *msg, int sender_uid) {
    char group_path[1024];
    snprintf(group_path, sizeof(group_path), "%s/groups/%s", BASE_PATH, group_name);

    int message_number = get_next_group_message_number(BASE_PATH, group_name);
    char filepath[2048];
    snprintf(filepath, sizeof(filepath), "%s/%d.txt", group_path, message_number);

    mode_t old_umask = umask(0);  // Setar umask para 0 temporariamente
    int fd = open(filepath, O_WRONLY | O_CREAT | O_TRUNC, 0666);  // Permissões para rw-rw-rw-
    umask(old_umask);  // Restaurar o umask anterior

    if (fd == -1) {
        fprintf(stderr, "Failed to open file: %s\n", strerror(errno));
        return;
    }

    struct tm *tm_now = localtime(&(time_t){time(NULL)});
    char time_str[100];
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_now);
    int message_length = strlen(msg);
    char *sender_username = get_username_by_uid(sender_uid);
    char metadata[2048];
    snprintf(metadata, sizeof(metadata), "Date of Receipt: %s\nSender: %s (UID: %d)\nMessage Size: %d bytes\n\nMessage:\n%s",
             time_str, sender_username, sender_uid, message_length, msg);

    if (write(fd, metadata, strlen(metadata)) == -1) {
        fprintf(stderr, "Failed to write to file: %s\n", strerror(errno));
    }

    printf("Message saved in: %s\n", filepath);

    close(fd);
}

// Função para validar o nome do grupo
int is_valid_groupname(const char *groupname) {
    while (*groupname) {
        if (!isalnum(*groupname) && *groupname != '-' && *groupname != '_') {
            return 0; // Retorna falso se encontrar um caractere inválido
        }
        groupname++;
    }
    return 1; // Retorna verdadeiro se todos os caracteres forem válidos
}

// Função para criar um grupo
int create_group(const char *groupname) {
    if (!is_valid_groupname(groupname)) {
        fprintf(stderr, "Invalid group name.\n");
        return -1;
    }

    struct group *grp = getgrnam(groupname);
    if (grp != NULL) {
        fprintf(stderr, "Group '%s' already exists.\n", groupname);
        return 0; // Grupo já existe, não precisa criar novamente
    }

    pid_t pid = fork();
    
    if (pid == -1) {
        perror("Failed to fork");
        return -1;
    } else if (pid > 0) {
        int status;
        waitpid(pid, &status, 0);
        if (WIFEXITED(status)) {
            return WEXITSTATUS(status);
        } else {
            return -1; // Retorna -1 se o processo filho não terminar normalmente
        }
    } else {
        execlp("groupadd", "groupadd", groupname, (char *) NULL);
        perror("execlp failed"); // Exibir erro se execlp falhar
        exit(EXIT_FAILURE);
    }
}

void create_user_specific_directory(const char* username) {
    char path[MAX_PATH_LENGTH];
    char messages_path[MAX_PATH_LENGTH];
    // char groups_path[MAX_PATH_LENGTH];
    char unread_path[MAX_PATH_LENGTH];
    char read_path[MAX_PATH_LENGTH];

    int ret;

    struct passwd *pwd = getpwnam(username);
    if (!pwd) {
        fprintf(stderr, "Failed to find user %s\n", username);
        return;
    }

    printf("USERNAME OF GROUP: %s\n", username);
    // Cria um grupo específico para o usuário
    if (create_group(username) != 0) {
        fprintf(stderr, "Failed to create group for %s\n", username);
        return;
    }

    // Obter GID do grupo criado
    struct group *grp = getgrnam(username);
    printf("GROUP NAME: %s\n", grp->gr_name);
    if (!grp) {
        fprintf(stderr, "Failed to find group %s\n", username);
        return;
    }

    // Configurar umask para zero temporariamente pode garantir que as permissões desejadas sejam aplicadas
    mode_t old_umask = umask(0);

    if (pwd) {
        ret = snprintf(path, sizeof(path), "%s/%s", BASE_PATH, username);
        if (ret < 0 || ret >= sizeof(path)) {
            fprintf(stderr, "Path length error for messages_path\n");
            umask(old_umask); // Restaura a umask original
            return;
        }

        if (mkdir(path, 0750) == -1) { //LEITURA E EXECUÇÃO PARA GRUPO
            fprintf(stderr, "Error creating directory %s: %s\n", path, strerror(errno));
            umask(old_umask); // Restaura a umask original
            return;
        }

        if (chown(path, pwd->pw_uid, grp->gr_gid) == -1) {
            fprintf(stderr, "Error setting ownership for %s: %s\n", path, strerror(errno));
            umask(old_umask); // Restaura a umask original
        }

        ret = snprintf(messages_path, sizeof(messages_path), "%s/messages", path);
        if (ret < 0 || ret >= sizeof(messages_path)) {
            fprintf(stderr, "Path length error for messages_path\n");
            umask(old_umask); // Restaura a umask original
            return;
        }

        mkdir(messages_path, 0750); 

        chown(messages_path, pwd->pw_uid, grp->gr_gid);

        // ret = snprintf(groups_path, sizeof(groups_path), "%s/groups", path);
        // if (ret < 0 || ret >= sizeof(groups_path)) {
        //     fprintf(stderr, "Path length error for groups_path\n");
        //     umask(old_umask); // Restaura a umask original
        //     return;
        // }

        // mkdir(groups_path, 0750);

        // chown(groups_path, pwd->pw_uid, grp->gr_gid);

        ret = snprintf(unread_path, sizeof(unread_path), "%s/unread", messages_path);
        if (ret < 0 || ret >= sizeof(unread_path)) {
            fprintf(stderr, "Path length error for unread_path\n");
            umask(old_umask); // Restaura a umask original
            return;
        }

        mkdir(unread_path, 0750);

        chown(unread_path, pwd->pw_uid, grp->gr_gid);

        ret = snprintf(read_path, sizeof(read_path), "%s/read", messages_path);
        if (ret < 0 || ret >= sizeof(read_path)) {
            fprintf(stderr, "Path length error for read_path\n");
            umask(old_umask); // Restaura a umask original
            return;
        }

        mkdir(read_path, 0750);

        chown(read_path, pwd->pw_uid, grp->gr_gid);

        printf("Directories created for %s with appropriate permissions in: %s\n", username, path);
    } else {
        fprintf(stderr, "Failed to find user %s\n", username);
    }
    umask(old_umask); // Restaura a umask original
}

int remove_directory(const char *path) {
    DIR *dir = opendir(path);
    if (dir == NULL) {
        fprintf(stderr, "Failed to open directory %s: %s\n", path, strerror(errno));
        return -1;
    }

    struct dirent *entry;
    char full_path[1024];
    int status = 0;

    while ((entry = readdir(dir)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0)
            continue;

        snprintf(full_path, sizeof(full_path), "%s/%s", path, entry->d_name);
        struct stat statbuf;
        if (stat(full_path, &statbuf) == 0) {
            if (S_ISDIR(statbuf.st_mode)) {
                status = remove_directory(full_path); // Recursive call
            } else {
                if (unlink(full_path) != 0) {
                    fprintf(stderr, "Failed to remove file %s: %s\n", full_path, strerror(errno));
                    status = -1;
                }
            }
        }
        if (status != 0) break;
    }

    closedir(dir);

    if (status == 0) { // Only attempt to remove the directory if all contents were removed
        if (rmdir(path) != 0) {
            fprintf(stderr, "Failed to remove directory %s: %s\n", path, strerror(errno));
            status = -1;
        }
    }

    return status;
}

int remove_user_directory(const char *username) {
    char path[1024];
    snprintf(path, sizeof(path), "%s/%s", BASE_PATH, username);
    return remove_directory(path);
}

void setup_base_directory() {
    mkdir(BASE_PATH, 0770);
    chown(BASE_PATH, 0, 0);  // root ownership or daemon_user if required
}

void strreplace(char *str, const char *old, const char *new) {
    char *pos, temp[1024];
    int oldlen = strlen(old);
    int newlen = strlen(new);

    while ((pos = strstr(str, old)) != NULL) {
        strcpy(temp, str);
        int len = pos - str;
        str[len] = '\0';
        strcat(str, new);
        strcat(str, temp + len + oldlen);
    }
}

int ensure_base_group_directory_exists() {
    char path[1024];
    snprintf(path, sizeof(path), "/var/lib/concordia_data/groups");

    struct stat st = {0};
    if (stat(path, &st) == -1) {
        mode_t old_umask = umask(0);
        int result = mkdir(path, 0775); // Acesso de leitura/escrita para o grupo e outros com acesso de leitura
        umask(old_umask);
        if (result == -1) {
            fprintf(stderr, "Error creating base group directory %s: %s\n", path, strerror(errno));
            return -1;
        }
    }
    return 0;
}

// Função para criar um grupo de sistema e um diretório para o grupo com um owner específico
int create_group_directory(const char *group_name, int user_uid) {

    // Verifica se o nome do grupo já existe como nome de usuário
    struct passwd *pwd = getpwnam(group_name);
    if (pwd != NULL) {
        fprintf(stderr, "Cannot create group named '%s' because a user with the same name exists.\n", group_name);
        return -1;  // Retorna erro se um usuário com o mesmo nome já existe
    }

    if (!is_valid_groupname(group_name)) {
        fprintf(stderr, "Invalid group name.\n");
        return -1;
    }

    struct group *grp = getgrnam(group_name);
    if (grp != NULL) {
        fprintf(stderr, "Group '%s' already exists.\n", group_name);
        return 0; // Grupo já existe, não precisa criar novamente
    }

    // Cria o grupo no sistema
    char cmd[256];
    snprintf(cmd, sizeof(cmd), "groupadd %s", group_name);
    if (system(cmd) != 0) {
        fprintf(stderr, "Failed to create system group '%s'.\n", group_name);
        return -1;
    }

    // Cria o diretório para o grupo
    char path[1024];
    snprintf(path, sizeof(path), "/var/lib/concordia_data/groups/%s", group_name);
    mode_t old_umask = umask(0);
    if (mkdir(path, 0770) == -1) {
        fprintf(stderr, "Error creating group directory %s: %s\n", path, strerror(errno));
        umask(old_umask);
        return -1;
    }
    umask(old_umask);

    // Configura o proprietário do diretório
    if (chown(path, user_uid, -1) == -1) {
        fprintf(stderr, "Failed to set owner UID %d for directory %s: %s\n", user_uid, path, strerror(errno));
        return -1;
    }

    printf("Group '%s' created successfully with directory owned by UID %d.\n", group_name, user_uid);
    return 0;
}

int remove_directory2(const char *path) {
    DIR *dir = opendir(path);
    if (dir == NULL) {
        fprintf(stderr, "Failed to open directory %s: %s\n", path, strerror(errno));
        return -1;
    }

    struct dirent *entry;
    char full_path[1024];
    int status = 0;

    while ((entry = readdir(dir)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;
        }
        snprintf(full_path, sizeof(full_path), "%s/%s", path, entry->d_name);
        struct stat statbuf;
        if (stat(full_path, &statbuf) == 0) {
            if (S_ISDIR(statbuf.st_mode)) {
                status = remove_directory2(full_path); // Recursive call
            } else {
                if (unlink(full_path) != 0) {
                    fprintf(stderr, "Failed to remove file %s: %s\n", full_path, strerror(errno));
                    status = -1;
                }
            }
        }
        if (status != 0) break;
    }

    closedir(dir);
    if (status == 0) { // Only attempt to remove the directory if all contents were removed
        if (rmdir(path) != 0) {
            fprintf(stderr, "Failed to remove directory %s: %s\n", path, strerror(errno));
            status = -1;
        }
    }

    return status;
}

// Função para verificar se um UID é membro de um grupo específico
int is_member_of_group(const char *group_name, int uid) {
    struct group *grp = getgrnam(group_name);
    if (!grp) {
        fprintf(stderr, "Group '%s' not found.\n", group_name);
        return 0;  // Grupo não encontrado
    }

    char **members;
    for (members = grp->gr_mem; *members != NULL; members++) {
        struct passwd *pwd = getpwnam(*members);
        if (pwd && pwd->pw_uid == uid) {
            return 1;  // UID é membro do grupo
        }
    }
    return 0;  // UID não é membro do grupo
}

int remove_group_directory(const char *group_name, int requester_uid) {
    char path[1024];
    snprintf(path, sizeof(path), "/var/lib/concordia_data/groups/%s", group_name);

    struct stat st;
    if (stat(path, &st) == -1) {
        fprintf(stderr, "Error: Cannot access group directory %s: %s\n", path, strerror(errno));
        return -1;
    }

    if (st.st_uid != requester_uid) {
        fprintf(stderr, "Error: User UID %d is not the owner of the group '%s' and cannot remove it.\n", requester_uid, group_name);
        return -1;
    }

    return remove_directory2(path);
}

// Função para converter UID em nome de usuário
char* uid_to_username(int uid) {
    struct passwd *pwd = getpwuid(uid);
    if (pwd == NULL) {
        fprintf(stderr, "Failed to find user for UID %d: %s\n", uid, strerror(errno));
        return NULL;
    }
    return strdup(pwd->pw_name);  // Retornar uma cópia do nome de usuário
}

// Função para adicionar um UID a um grupo do sistema, verificando o proprietário do grupo
int add_uid_to_system_group(const char *group_name, int uid, int uid_owner) {
    char group_dir_path[1024];
    snprintf(group_dir_path, sizeof(group_dir_path), "/var/lib/concordia_data/groups/%s", group_name);

    // Obter informações do diretório do grupo
    struct stat group_dir_stat;
    if (stat(group_dir_path, &group_dir_stat) != 0) {
        fprintf(stderr, "Error: Cannot access group directory %s: %s\n", group_dir_path, strerror(errno));
        return -1;
    }

    // Verificar se o uid_owner é o proprietário do diretório do grupo
    if (group_dir_stat.st_uid != uid_owner) {
        fprintf(stderr, "Error: User UID %d is not the owner of the group '%s' and cannot add members.\n", uid_owner, group_name);
        return -1;
    }

    char *username = uid_to_username(uid);
    if (username == NULL) {
        return -1;  // Falha ao obter o nome de usuário
    }

    // Comando para adicionar o nome de usuário ao grupo
    char cmd[256];
    snprintf(cmd, sizeof(cmd), "usermod -a -G %s %s", group_name, username);
    int result = system(cmd);
    free(username);  // Liberar memória alocada para o nome de usuário

    if (result != 0) {
        fprintf(stderr, "Failed to add user %s to group %s.\n", username, group_name);
        return -1;
    }

    printf("User %s added to group %s successfully.\n", username, group_name);
    return 0;
}

// Função para listar membros de um grupo
void list_group_members(int client_sock, const char *group_name) {
    struct group *grp = getgrnam(group_name);
    if (grp == NULL) {
        char buffer[1024];
        snprintf(buffer, sizeof(buffer), "Group '%s' not found.\n", group_name);
        char *message = buffer; 
        write(client_sock, message, strlen(message));
        return;
    }

    char buffer[1024];
    char *message = buffer;
    int len = snprintf(buffer, sizeof(buffer), "Members of group '%s':\n", group_name);
    message += len;

    for (char **members = grp->gr_mem; *members; members++) {
        len = snprintf(message, sizeof(buffer) - (message - buffer), "%s\n", *members);
        message += len;
    }

    write(client_sock, buffer, message - buffer);
}

int main(void) {

    setup_base_directory();

    // Verifica se o diretório existe
    struct stat st = {0};
    if (stat(SOCKET_DIR, &st) == -1) {
        perror("Diretório /var/run/concordia não existe");
        return EXIT_FAILURE;
    }

    int server_sock, client_sock;
    struct sockaddr_un server_addr, client_addr;
    socklen_t client_addr_len;

    // Criando o socket do servidor
    server_sock = socket(AF_UNIX, SOCK_STREAM, 0);
    if (server_sock < 0) {
        perror("socket");
        return EXIT_FAILURE;
    }

    // Configurando o endereço do servidor
    memset(&server_addr, 0, sizeof(struct sockaddr_un));
    server_addr.sun_family = AF_UNIX;
    strcpy(server_addr.sun_path, SOCKET_PATH);
    unlink(SOCKET_PATH); // Remove o socket anterior se existir

    // Vinculando o socket a um endereço
    if (bind(server_sock, (struct sockaddr *) &server_addr, sizeof(struct sockaddr_un)) < 0) {
        perror("bind");
        return EXIT_FAILURE;
    }

    // Definindo permissões para o socket
    chmod(SOCKET_PATH, 0777);

    // Ouvindo por conexões
    if (listen(server_sock, 5) < 0) {
        perror("listen");
        return EXIT_FAILURE;
    }

    printf("Concordia daemon running...\n");

    // Aceitando conexões
    while (1) {
        client_addr_len = sizeof(struct sockaddr_un);
        client_sock = accept(server_sock, (struct sockaddr *) &client_addr, &client_addr_len);
        if (client_sock < 0) {
            perror("accept");
            continue;
        }

        // Comandos
        char buffer[1024];
        int len = read(client_sock, buffer, sizeof(buffer) - 1);
        if (len > 0) {
            buffer[len] = '\0';  // Garante terminação da string
            int uid;
            char command[10];
            sscanf(buffer, "%s %d", command, &uid);  // Lê o comando e o UID
            if (strncmp(command, "ativar", 6) == 0) {
                printf("Utilizador com UID %d registado.\n", uid);
                // create_user_directory_by_uid(uid);
                create_user_specific_directory(get_username_by_uid(uid));
                printf("Diretório com UID %d criado.\n", uid);
                add_user(uid);
                printf("Utilizador com UID %d adicionado.\n", uid);
                print_active_users();
            } 
            else{
                if (!is_user_active(uid)) {
                    printf("UID %d não está ativo. Por favor, ative primeiro.\n", uid);
                    return 1;

                } else if (strncmp(command, "desativar", 9) == 0) {
                    printf("Comando para desativar UID %d recebido.\n", uid);
                    if (!is_user_active(uid)) {
                        printf("UID %d não está ativo. Não é possível desativar.\n", uid);
                        continue; // Continua a escuta sem encerrar o servidor
                    } else {
                        char* username = get_username_by_uid(uid);
                        if (username) {
                            printf("Removendo diretório para o usuário %s.\n", username);
                            remove_user_directory(username);
                            remove_user(uid);
                            printf("Utilizador com UID %d e diretórios associados removidos.\n", uid);
                            print_active_users();
                        } else {
                            printf("Não foi possível encontrar o usuário para UID %d.\n", uid);
                        }
                    }
                } else if (strncmp(command, "enviar", 6) == 0) {
                    int sender_uid;
                    char recipient[100], message[2048];
                    sscanf(buffer, "%*s %d %s %[^\t\n]", &sender_uid, recipient, message); // Read UID, recipient, and message
                    struct passwd *pwd = getpwnam(recipient);
                    if (pwd != NULL) {
                        if (is_user_active(pwd->pw_uid)) {
                            save_message_to_user(recipient, message, sender_uid);
                        } else {
                            printf("Recipient '%s' is not active.\n", recipient);
                        }
                    } else {
                        struct group *grp = getgrnam(recipient);
                        if (grp != NULL) {
                            // Verifica se o remetente é membro do grupo ou se é o proprietário do diretório do grupo
                            if (is_member_of_group(recipient, sender_uid) || grp->gr_gid == getuid()) {
                                save_message_to_group(recipient, message, sender_uid);
                            } else {
                                printf("Sender is not authorized to send messages to group '%s'.\n", recipient);
                            }
                        } else {
                            printf("Recipient '%s' not found as user or group.\n", recipient);
                        }
                    }
                } else if (strncmp(command, "read", 4) == 0) {

                    printf("COMMAND RECEIVED READ: %s", buffer);
                    char comm[10], message_path[256], message_path_copy[256];
                    int uid;
                    sscanf(buffer, "%s %d %s", comm, &uid, message_path);

                    strcpy(message_path_copy, message_path);
                    strreplace(message_path_copy, "unread", "read");

                    if (rename(message_path, message_path_copy) != 0) {
                        perror("Failed to move message");
                    } else {
                        printf("Message %s moved to read.\n", message_path_copy);
                    }
                } else if (strncmp(command, "remover-destinatario", 20) == 0) {
                    char group_name[100];
                    int uid;
                    sscanf(buffer, "%*s %s %d", group_name, &uid); // Extraí o nome do grupo e UID
                    
                    // Removendo o usuário do grupo
                    char cmd[256];
                    char *username = uid_to_username(uid);
                    if (!username) {
                        char *error_message = "User not found.\n";
                        write(client_sock, error_message, strlen(error_message));
                        continue;
                    }

                    snprintf(cmd, sizeof(cmd), "gpasswd -d %s %s", username, group_name);
                    if (system(cmd) != 0) {
                        fprintf(stderr, "Failed to remove user %s from group %s.\n", username, group_name);
                        char *error_message = "Failed to remove user from group.\n";
                        write(client_sock, error_message, strlen(error_message));
                    } else {
                        printf("User %s removed from group %s successfully.\n", username, group_name);
                        char *success_message = "User removed from group successfully.\n";
                        write(client_sock, success_message, strlen(success_message));
                    }
                    free(username);
                } else if (strncmp(command, "remover-grupo", 13) == 0) {
                    char group_name[100];
                    int uid;
                    sscanf(buffer, "%*s %s %d", group_name, &uid); 

                    if (remove_group_directory(group_name, uid) != 0) {
                        printf("Failed to remove group '%s'.\n", group_name);
                    } else {
                        printf("Group '%s' removed successfully.\n", group_name);
                    }
                } else if (strncmp(command, "remove", 6) == 0) {
                    int uid;
                    char message_filepath[256];
                    sscanf(buffer, "%*s %d %s", &uid, message_filepath);
                    
                    printf("MESSAGE_FILEPATH: %s.\n", message_filepath);

                    if (unlink(message_filepath) == 0) {
                        printf("Message %s successfully removed.\n", message_filepath);
                    } else {
                        perror("Failed to remove message");
                    }
                } else if (strncmp(command, "criar-grupo", 11) == 0) {
                    char group_name[100];
                    int uid;
                    sscanf(buffer, "%*s %s %d", group_name, &uid);  // Modificado para receber UID

                    if (create_group_directory(group_name, uid) != 0) {
                        printf("Failed to create group '%s'.\n", group_name);
                    } else {
                        printf("Group '%s' created successfully.\n", group_name);
                    }
                } else if (strncmp(command, "adicionar-destinatario", 22) == 0) {
                    char group_name[100];
                    int requester_uid, target_uid;
                    sscanf(buffer, "%*s %s %d %d", group_name, &requester_uid, &target_uid);

                    // Verificar se o solicitante é o dono do diretório do grupo
                    char group_path[1024];
                    snprintf(group_path, sizeof(group_path), "/var/lib/concordia_data/groups/%s", group_name);
                    struct stat st;
                    if (stat(group_path, &st) != 0) {
                        fprintf(stderr, "Group does not exist.\n");
                    } else {
                        add_uid_to_system_group(group_name, target_uid, requester_uid);
                    }
                } else if (strncmp(command, "listar-grupo", 12) == 0) {
                    char group_name[100];
                    char comm[25];
                    sscanf(buffer, "%s %s", comm, group_name);
                    list_group_members(client_sock, group_name);
                }
            }
        }

        close(client_sock);
    }

    close(server_sock);
    unlink(SOCKET_PATH);
    return EXIT_SUCCESS;
}

