#include "os.h"


int os_getpid() {
    #if defined(__OS_WINDOWS__)
        return (int)GetCurrentProcessId();
    #elif defined(__OS_UNIX__)
        return (int)getpid();
    #endif
}


int os_access(char *path) {
    FILE *f = fopen(path, "r");
    if (f) {
        fclose(f);
        return 1;
    } else {
        if (errno == ENOENT) return 0;
        return -1;
    }
}


char *os_readfile(char *path, int range_start, int range_end) {
    if (range_start == 0 && range_end == -1) {
        FILE *f = fopen(path, "r");
        if (!f) return NULL;

        fseek(f, 0, SEEK_END);
        long length = ftell(f);
        rewind(f);

        char *buffer = (char *)malloc(sizeof(char) * (length + 1));
        if (!buffer) {
            fclose(f);
            return NULL;
        }

        buffer[fread(buffer, 1, length, f)] = '\0';
        fclose(f);
        return buffer;
    } else {
        FILE *f = fopen(path, "r");
        if (!f) return NULL;

        int length = range_end - range_start + 1;
        fseek(f, range_start, SEEK_SET);
        char *buffer = (char *)malloc(sizeof(char) * (length + 1));
        if (!buffer) {
            fclose(f);
            return NULL;
        }
        buffer[fread(buffer, 1, length, f)] = '\0';
        fclose(f);
        return buffer;
    }
}


double os_time() {
    #if defined(__OS_UNIX__)
        struct timespec t;
        // `CLOCK_MONOTONIC` prevents system time from being tampered with.
        clock_gettime(CLOCK_MONOTONIC, &t);
        return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
    #elif defined(__OS_WINDOWS__)
        LARGE_INTEGER frequency;
        LARGE_INTEGER counter;
        QueryPerformanceFrequency(&frequency);
        QueryPerformanceCounter(&counter);
        return (double)counter.QuadPart / frequency.QuadPart;
    #else
        return (double)time(NULL);
    #endif
}


char *os_basename(char *path) {
    char *base = path;
    if (path == NULL || *path == '\0') return NULL;
    for (char *p = path; *p; p++) if (*p == '/' || *p == '\\') base = p + 1;
    if (*base == '\0') return NULL;
    return base;
}


void os_sleep(double second) {
    if (second <= 0.0) return;
    #if defined(__OS_UNIX__)
        struct timespec requested_time;
        struct timespec remaining_time;
        requested_time.tv_sec = (long)second;
        requested_time.tv_nsec = (long)(1e9 * (second - requested_time.tv_sec));
        while (nanosleep(&requested_time, &remaining_time) == -1 && errno == EINTR) requested_time = remaining_time;
    #elif defined(__OS_WINDOWS__)
        DWORD millisecond = (DWORD)(second * 1000.0);
        if (millisecond == 0 && second > 0) millisecond = 1;
        Sleep(millisecond);
    #endif
}


int os_isdir(char *path) {
    if (path == NULL || *path == '\0') return 0;

    #if defined(__OS_UNIX__)
        struct stat s;
        if (stat(path, &s) != 0) return 0;
        return S_ISDIR(s.st_mode);
    #elif defined(__OS_WINDOWS__)
        DWORD attrs = GetFileAttributesA(path);
        if (attrs == INVALID_FILE_ATTRIBUTES) return 0;
        if (attrs & FILE_ATTRIBUTE_DIRECTORY) return 1;
        return 0;
    #endif
}


int os_mkdir(char *dir) {
    int result = 0;
    errno = 0;
    #if defined(__OS_UNIX__)
        result = mkdir(dir, 0755);
    #elif defined(__OS_WINDOWS__)
        result = _mkdir(dir);
    #endif
    if (result == 0) return 0;
    else {
        if (errno == EEXIST) return 0;
        else return 1;
    }
}