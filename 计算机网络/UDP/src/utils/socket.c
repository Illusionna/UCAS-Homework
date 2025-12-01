#include "socket.h"


int socket_init() {
    #ifdef __OS_WINDOWS__
        WSADATA wsa;
        if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return 1;
    #endif
    return 0;
}


Socket socket_create(int domain, int type, int protocol) {
    return socket(domain, type, protocol);
}


void socket_close(Socket s) {
    #if defined(__OS_WINDOWS__)
        if (s == SOCKET_INVALID) return;
        else closesocket(s);
    #elif defined(__OS_UNIX__)
        if (s == SOCKET_INVALID) return;
        else close(s);
    #endif
}


void socket_destroy() {
    #ifdef __OS_WINDOWS__
        WSACleanup();
    #endif
}


void socket_config(struct sockaddr_in *server, int domain, char *ip, int port) {
    #if defined(__OS_UNIX__)
        server->sin_family = domain;
        server->sin_addr.s_addr = inet_addr(ip);
        server->sin_port = socket_htons(port);
    #elif defined(__OS_WINDOWS__)
        server->sin_family = domain;
        server->sin_addr.S_un.S_addr = inet_addr(ip);
        server->sin_port = socket_htons(port);
    #endif
}


int socket_connect(Socket s, struct sockaddr_in *server, int size) {
    return connect(s, (struct sockaddr *)server, size);
}


int socket_send(Socket s, char *buffer, int length, int flag) {
    return send(s, buffer, length, flag);
}


int socket_sendto(Socket s, void *buffer, int length, int flag, struct sockaddr_in *to, int size) {
    return sendto(s, buffer, length, flag, (struct sockaddr *)to, size);
}


int socket_recv(Socket s, char *buffer, int length, int flag) {
    return recv(s, buffer, length, flag);
}


int socket_recvfrom(Socket s, void *buffer, int length, int flag, struct sockaddr_in *from, int *size) {
    #if defined(__OS_UNIX__)
        return recvfrom(s, buffer, length, flag, (struct sockaddr *)from, (socklen_t *)size);
    #elif defined(__OS_WINDOWS__)
        return recvfrom(s, buffer, length, flag, (struct sockaddr *)from, size);
    #endif
}


int socket_bind(Socket s, struct sockaddr_in *address_name, int size) {
    return bind(s, (struct sockaddr *)address_name, size);
}


int socket_listen(Socket s, int backlog) {
    return listen(s, backlog);
}


Socket socket_accept(Socket s, struct sockaddr_in *address, int *size_pointer) {
    #if defined(__OS_UNIX__)
        return accept(s, (struct sockaddr *)address, (socklen_t *)size_pointer);
    #elif defined(__OS_WINDOWS__)
        return accept(s, (struct sockaddr *)address, size_pointer);
    #endif
}


int socket_setopt(Socket s, int level, int optname, void *ctx, int size) {
    if (ctx == NULL && size == 0) {
        int opt = 1;
        #if defined(__OS_UNIX__)
            return setsockopt(s, level, optname, (void *)&opt, sizeof(opt));
        #elif defined(__OS_WINDOWS__)
            return setsockopt(s, level, optname, (char *)&opt, sizeof(opt));
        #endif
    } else {
        #if defined(__OS_UNIX__)
            return setsockopt(s, level, optname, ctx, size);
        #elif defined(__OS_WINDOWS__)
            return setsockopt(s, level, optname, (char *)ctx, size);
        #endif
    }
}


unsigned int socket_ntohl(unsigned int value) {
    return ntohl(value);
}


unsigned int socket_htonl(unsigned int value) {
    return htonl(value);
}


unsigned short socket_ntohs(unsigned short value) {
    return ntohs(value);
}


unsigned short socket_htons(unsigned short value) {
    return htons(value);
}