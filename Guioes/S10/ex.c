#include <syslog.h>

int main(int argc, char *argv[]) {
    
    // opcional
    openlog("MY EXE", LOG_PID | LOG_NDELAY, LOG_USER);

    setlogmask(LOG_UPTO(LOG_DEBUG));


    syslog(LOG_DEBUG,"%s %d", "Hello, world!", 20);

    closelog();
    
    
    return 0;    
}

/*

openlog("MY EXE", LOG_PID, LOG_LOCAL2) loga com o nome MY EXE, com o PID e com a facility LOG_LOCAL2;
journalctl --facility=local2


*/