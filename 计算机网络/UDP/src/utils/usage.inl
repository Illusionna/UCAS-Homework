#include <stdio.h>


void usage_help(char *app, int port) {
    printf("--------------------------------------------------------------------------\n");
    printf("| Usage:\n");
    printf("|  %s run\t\t- Start a host server (default port: %d)\n", app, port);
    printf("|  %s [file_path]\t- Client sends a file to server\n", app);
    printf("|-----------------------------------------------------------------\n");
    printf("| Example:\n");
    printf("|  %s /Users/illusionna/Desktop/main.pdf\n", app);
    printf("|  %s /Users/illusionna/Desktop/README\n", app);
    printf("--------------------------------------------------------------------------\n");
}


void usage_start(int pid, int port) {
    printf("\x1b[32mINFO:\x1b[0m Started server process ID [\x1b[36m%d\x1b[0m]\n", pid);
    printf("\x1b[32mINFO:\x1b[0m Waiting for application startup.\n");
    printf("\x1b[32mINFO:\x1b[0m Application startup complete.\n");
    printf("\x1b[32mINFO:\x1b[0m C socket UDP service running on \x1b[36mlocalhost:%d\x1b[0m (Press \x1b[33mCTRL+C\x1b[0m to quit)\n", port);
}


void usage_end(int pid) {
    printf("\x1b[32mINFO:\x1b[0m Shutting down.\n");
    printf("\x1b[32mINFO:\x1b[0m Waiting for application shutdown.\n");
    printf("\x1b[32mINFO:\x1b[0m Application shutdown complete.\n");
    printf("\x1b[32mINFO:\x1b[0m Finished server process ID [\x1b[36m%d\x1b[0m]\n", pid);
}