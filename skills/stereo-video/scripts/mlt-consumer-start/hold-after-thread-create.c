// SPDX-License-Identifier: GPL-3.0-or-later
// Make a thread-start race certain: hold the creator right after it created a thread of one library.
//
// MLT's avformat consumer (before upstream's pull request 1366) created its thread and only then set
// "running". When the new thread reached its loop first it saw "running" unset, stopped at once, and the
// starter then set "running": the consumer looked running for ever with no thread behind it. On a quiet
// machine the creator almost always wins; this library makes it lose every time, so a fix is proved in one
// run instead of hundreds:
//
//   cc -Wall -Wextra -Werror -fPIC -shared hold-after-thread-create.c -ldl -o hold-after-thread-create.so
//   export HOLD_AFTER_THREAD_CREATE_MS=300 HOLD_AFTER_THREAD_CREATE_IN=libmltavformat
//   LD_PRELOAD=$PWD/hold-after-thread-create.so melt clip.mkv -consumer avformat:out.wav
//
// Unrepaired MLT: melt never ends. Repaired MLT: it ends, 300 ms later than without the library.
// It changes nothing but the order of the two threads; a program that is right in every order is unaffected.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

int pthread_create(pthread_t *thread, const pthread_attr_t *attr, void *(*start)(void *), void *arg)
{
    int (*original)(pthread_t *, const pthread_attr_t *, void *(*)(void *), void *) = dlsym(RTLD_NEXT, "pthread_create");
    int result = original(thread, attr, start, arg);
    const char *hold = getenv("HOLD_AFTER_THREAD_CREATE_MS");
    const char *library = getenv("HOLD_AFTER_THREAD_CREATE_IN");
    Dl_info where;
    if (result == 0 && hold && library && dladdr((void *)start, &where) && where.dli_fname && strstr(where.dli_fname, library)) {
        const long ms = strtol(hold, NULL, 10);
        const struct timespec pause = {.tv_sec = ms / 1000, .tv_nsec = (ms % 1000) * 1000000L};
        nanosleep(&pause, NULL);
    }
    return result;
}
