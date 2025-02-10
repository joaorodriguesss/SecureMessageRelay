#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>

int main() {
    printf("User ID: %d\n", getuid());
    printf("Group ID: %d\n", getgid());
    
    FILE *arquivo;
    char linha[100];
    arquivo = fopen("exemplo.txt", "r");

    if (arquivo == NULL) {
        
        printf("Erro ao abrir o arquivo.:%s\n", strerror(errno));
        return 1; 
    }
    while (fgets(linha, sizeof(linha), arquivo) != NULL) {
        printf("%s", linha);
    }

    // Fecha o arquivo
    fclose(arquivo);
    return 0;
}
