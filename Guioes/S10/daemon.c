#include <stdio.h>
#include <syslog.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    
    int i = 0;
    while (1){
        syslog(LOG_INFO,"%s: %d", "My Daemon", i++);
        sleep(1);
    
    }
    
    return 0;
}




/* ps -xau | grep <PROGRAMA>
kill -9 <PID>

cp my_daemon.service ~/.config/systemd/user
systemctl --user daemon-reload
systemctl --user start my_daemon
systemctl --user status my_daemon

systemctl --user stop my_daemon

journalctl --user-unit my_daemon
*/