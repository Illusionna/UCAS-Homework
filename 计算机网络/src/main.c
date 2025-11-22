#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <stdint.h>

#include "./utils/log.h"
#include "./utils/hashmap.h"
#include "./utils/socket.h"
#include "./utils/thread.h"
#include "./utils/os.h"

#define PORT 8080


long N = 0;
static Mutex mutex;
static volatile int RUNNING = 1;
static Socket S = SOCKET_INVALID;
static HashMap *dict = NULL;


void interrupt_handle(int semaphore) {
    printf("\n\x1b[1;32m* Interrupt: Disconnect Socket and Free Memory.\x1b[0m\n");

    hashmap_view(dict);
    hashmap_destroy(dict);
    mutex_destroy(&mutex);

    RUNNING = 0;
    if (S != SOCKET_INVALID) socket_close(S);
    socket_destroy();
}


void log_mutex_func(int lock, void *ctx) {
    Mutex *mutex = (Mutex *)ctx;
    if (lock) mutex_lock(mutex);
    else mutex_unlock(mutex);
}


void log_callback_csv(LogEvent *event) {
    char buffer[32];
    buffer[strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", event->time)] = '\0';
    fprintf(event->ctx, "%s, %s, %s, %d, ", buffer, TIPS[event->level], event->file, event->line);
    vfprintf(event->ctx, event->fmt, event->argument_pointer);
    fprintf(event->ctx, "\n");
    fflush(event->ctx);
}


void log_callback_statistics(LogEvent *event) {
    N++;
    fprintf(event->ctx, "%ld ", N);
    fflush(event->ctx);
}


int http_header(char *header, int header_size, unsigned long content_length, int status_code) {
    int header_length;
    if (status_code == 200) {
        header_length = snprintf(
            header, header_size,
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            "Content-Length: %lu\r\n"
            "Connection: close\r\n"
            "\r\n", content_length
        );
    } else if (status_code == 404) {
        header_length = snprintf(
            header, header_size,
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/html\r\n"
            "Content-Length: %lu\r\n"
            "Connection: close\r\n"
            "\r\n", content_length
        );
    } else {
        header_length = snprintf(
            header, 256,
            "HTTP/1.1 500 Internal Server Error\r\n"
            "Content-Type: text/html\r\n"
            "Content-Length: %lu\r\n"
            "Connection: close\r\n"
            "\r\n", content_length
        );
    }
    return header_length;
}


int route_coroutine(void *args) {
    Socket c = (Socket)(uintptr_t)args;

    char buffer[1024];
    int n = socket_recv(c, buffer, sizeof(buffer) - 1, 0);
    if (n <= 0) {
        printf("\x1b[1;37;45mWarning:\x1b[0m Receive socket.\n");
        socket_close(c);
        return 1;
    }
    buffer[n] = '\0';

    char method[16];
    char url[256];
    sscanf(buffer, "%s %s", method, url);
    char *body = NULL;
    char header[256];
    int header_length;
    int range_start = 0;
    int range_end = -1;
    char *range = strstr(buffer, "Range: bytes=");

    if (range) {
        sscanf(range, "Range: bytes=%d-%d", &range_start, &range_end);

        if (strcmp(url, "/") == 0) {
            body = os_readfile("./UI/default.html", 0, -1);
            header_length = http_header(header, sizeof(header), strlen(body), 200);
        }

        else if (strncmp(url, "/index.html", 12) == 0) {
            body = os_readfile("./UI/index.html", range_start, range_end);
            header_length = http_header(header, sizeof(header), strlen(body), 200);
        }

        else {
            char path[256];
            snprintf(path, sizeof(path), "./UI%s", url);
            if (os_access(path) == 1) {
                body = os_readfile(path, range_start, range_end);
                header_length = http_header(header, sizeof(header), strlen(body), 200);
            } else {
                body = os_readfile("./UI/404.html", 0, -1);
                header_length = http_header(header, sizeof(header), strlen(body), 404);
            }
        }

        socket_send(c, header, header_length, 0);
        socket_send(c, body, strlen(body), 0);
        socket_close(c);
        // Free the memory of os_readfile().
        free(body);
    } else {
        // The thread operation on the HashMap requires the mutex lock.
        mutex_lock(&mutex);

        if (strcmp(url, "/") == 0) {
            if (!hashmap_get(dict, "./UI/default.html")) {
                body = os_readfile("./UI/default.html", 0, -1);
                hashmap_put(dict, "./UI/default.html", body);
                // Free the memory of os_readfile().
                free(body);
                // The body pointer moves to the memory of the HashMap.
                body = hashmap_get(dict, "./UI/default.html");
            } else body = hashmap_get(dict, "./UI/default.html");
            header_length = http_header(header, sizeof(header), strlen(body), 200);
        }

        else if (strncmp(url, "/index.html", 12) == 0) {
            if (!hashmap_get(dict, "./UI/index.html")) {
                body = os_readfile("./UI/index.html", 0, -1);
                hashmap_put(dict, "./UI/index.html", body);
                // Free the memory of os_readfile().
                free(body);
                // The body pointer moves to the memory of the HashMap.
                body = hashmap_get(dict, "./UI/index.html");
            } else body = hashmap_get(dict, "./UI/index.html");
            header_length = http_header(header, sizeof(header), strlen(body), 200);
        }

        else {
            char path[256];
            snprintf(path, sizeof(path), "./UI%s", url);
            if (os_access(path) == 1) {
                if (!hashmap_get(dict, path)) {
                    body = os_readfile(path, 0, -1);
                    hashmap_put(dict, path, body);
                    // Free the memory of os_readfile().
                    free(body);
                    // The body pointer moves to the memory of the HashMap.
                    body = hashmap_get(dict, path);
                } else body = hashmap_get(dict, path);
                header_length = http_header(header, sizeof(header), strlen(body), 200);
            } else {
                if (!hashmap_get(dict, "./UI/404.html")) {
                    body = os_readfile("./UI/404.html", 0, -1);
                    hashmap_put(dict, "./UI/404.html", body);
                    // Free the memory of os_readfile().
                    free(body);
                    // The body pointer moves to the memory of the HashMap.
                    body = hashmap_get(dict, "./UI/404.html");
                } else body = hashmap_get(dict, "./UI/404.html");
                header_length = http_header(header, sizeof(header), strlen(body), 404);
            }
        }

        mutex_unlock(&mutex);

        socket_send(c, header, header_length, 0);
        socket_send(c, body, strlen(body), 0);
        socket_close(c);
    }

    return 0;
}


int http_server() {
    dict = hashmap_create();

    if (mutex_create(&mutex, 1)) {
        printf("\x1b[1;37;41mError:\x1b[0m Create mutex.\n");
        return 1;
    }

    if (socket_init()) {
        printf("\x1b[1;37;41mError:\x1b[0m Initialize socket.\n");
        return 1;
    }

    S = socket_create(AF_INET, SOCK_STREAM, 0);
    if (S == SOCKET_INVALID) {
        printf("\x1b[1;37;41mError:\x1b[0m Create socket.\n");
        socket_destroy();
        return 1;
    }

    if (socket_setopt(S, SOL_SOCKET, SO_REUSEADDR) == SOCKET_INVALID) {
        printf("\x1b[1;37;41mError:\x1b[0m Set option of socket.\n");
        socket_close(S);
        socket_destroy();
        return 1;
    }

    struct sockaddr_in server;
    memset(&server, 0, sizeof(server));
    socket_config(&server, AF_INET, "127.0.0.1", PORT);

    if (socket_bind(S, &server, sizeof(server)) == SOCKET_INVALID) {
        printf("\x1b[1;37;41mError:\x1b[0m Bind socket.\n");
        socket_close(S);
        socket_destroy();
        return 1;
    }

    if (socket_listen(S, 16) == SOCKET_INVALID) {
        printf("\x1b[1;37;41mError:\x1b[0m Listen socket.\n");
        socket_close(S);
        socket_destroy();
        return 1;
    }

    while (RUNNING) {
        struct sockaddr_in client;
        int client_length = sizeof(client);

        Socket c = socket_accept(S, &client, &client_length);
        if (c == SOCKET_INVALID) {
            if (!RUNNING) break;
            printf("\x1b[1;37;45mWarning:\x1b[0m Accept socket.\n");
            continue;
        }

        log_trace("client (%s:%d)", inet_ntoa(client.sin_addr), ntohs(client.sin_port));

        Thread thread;
        if (thread_create(&thread, route_coroutine, (void *)(uintptr_t)c)) {
            printf("\x1b[1;37;45mWarning:\x1b[0m Create thread.\n");
            socket_close(c);
            continue;
        }
        thread_detach(&thread);
    }
    return 0;
}



int main(int argc, char *argv[], char *envs[]) {
	printf("\x1b[32mINFO:\x1b[0m Started server process ID [\x1b[36m%d\x1b[0m]\n", os_getpid());
    printf("\x1b[32mINFO:\x1b[0m Waiting for application startup.\n");
    printf("\x1b[32mINFO:\x1b[0m Application startup complete.\n");
    printf("\x1b[32mINFO:\x1b[0m C socket service running on \x1b[36mhttp://localhost:%d\x1b[0m (Press \x1b[33mCTRL+C\x1b[0m to quit)\n", PORT);

    signal(SIGINT, interrupt_handle);

    log_setting(0);
    log_config_thread_lock(log_mutex_func, &mutex);    

    FILE *f = fopen("log.log", "w");
    log_config_write(f);

    FILE *csv = fopen("log.csv", "w");
    log_add_callback(log_callback_csv, csv);

    FILE *statistics = fopen("log.statistics", "w");
    log_add_callback(log_callback_statistics, statistics);

    http_server();

    printf("\x1b[32mINFO:\x1b[0m Shutting down.\n");
    printf("\x1b[32mINFO:\x1b[0m Waiting for application shutdown.\n");
    printf("\x1b[32mINFO:\x1b[0m Application shutdown complete.\n");
    printf("\x1b[32mINFO:\x1b[0m Finished server process ID [\x1b[36m%d\x1b[0m]\n", os_getpid());
    fclose(statistics);
    fclose(csv);
    fclose(f);
	return 0;
}