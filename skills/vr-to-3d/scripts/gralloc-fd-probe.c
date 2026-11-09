/* SPDX-License-Identifier: MIT */
#define _GNU_SOURCE
#include <android/hardware_buffer.h>
#include <vndk/hardware_buffer.h>
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/dma-buf.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

static int inspect_fd(int fd)
{
    char path[80], target[512], line[512];
    snprintf(path, sizeof(path), "/proc/self/fd/%d", fd);
    ssize_t n = readlink(path, target, sizeof(target) - 1);
    if (n < 0) {
        perror("readlink");
        return -1;
    }
    target[n] = 0;
    printf("fd=%d target=%s\n", fd, target);
    snprintf(path, sizeof(path), "/proc/self/fdinfo/%d", fd);
    FILE *info = fopen(path, "r");
    if (!info) return -1;
    while (fgets(line, sizeof(line), info)) printf("fdinfo: %s", line);
    fclose(info);
    struct dma_buf_sync sync = {.flags = DMA_BUF_SYNC_START | DMA_BUF_SYNC_READ};
    errno = 0;
    int result = ioctl(fd, DMA_BUF_IOCTL_SYNC, &sync);
    int saved = errno;
    printf("DMA_BUF_IOCTL_SYNC_START result=%d errno=%d (%s)\n",
           result, saved, strerror(saved));
    if (result != 0) return saved == ENOTTY ? 0 : -1;
    sync.flags = DMA_BUF_SYNC_END | DMA_BUF_SYNC_READ;
    if (ioctl(fd, DMA_BUF_IOCTL_SYNC, &sync) != 0) return -1;
    return 1;
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    void *library = dlopen("libnativewindow.so", RTLD_NOW | RTLD_LOCAL);
    if (!library) { fprintf(stderr, "%s\n", dlerror()); return 1; }
    const native_handle_t *(*get_handle)(const AHardwareBuffer *) =
        dlsym(library, "AHardwareBuffer_getNativeHandle");
    if (!get_handle) { fprintf(stderr, "%s\n", dlerror()); return 1; }
    int control = open("/dev/null", O_RDONLY | O_CLOEXEC);
    if (control < 0) return 1;
    puts("CONTROL /dev/null must reject dma-buf sync");
    int c = inspect_fd(control);
    close(control);
    if (c != 0) return 1;
    const uint64_t usages[] = {
        AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN | AHARDWAREBUFFER_USAGE_CPU_WRITE_OFTEN,
        AHARDWAREBUFFER_USAGE_GPU_COLOR_OUTPUT | AHARDWAREBUFFER_USAGE_GPU_SAMPLED_IMAGE,
        AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN | AHARDWAREBUFFER_USAGE_CPU_WRITE_OFTEN |
            AHARDWAREBUFFER_USAGE_GPU_COLOR_OUTPUT | AHARDWAREBUFFER_USAGE_GPU_SAMPLED_IMAGE
    };
    unsigned total = 0, dma = 0;
    int errors = 0;
    for (unsigned i = 0; i < sizeof(usages) / sizeof(usages[0]); ++i) {
        AHardwareBuffer_Desc d = {.width = 64, .height = 64, .layers = 1,
            .format = AHARDWAREBUFFER_FORMAT_R8G8B8A8_UNORM, .usage = usages[i]};
        AHardwareBuffer *buffer = NULL;
        int r = AHardwareBuffer_allocate(&d, &buffer);
        printf("ALLOC case=%u usage=0x%llx result=%d\n", i,
               (unsigned long long)d.usage, r);
        if (r != 0 || !buffer) { errors++; continue; }
        AHardwareBuffer_describe(buffer, &d);
        const native_handle_t *h = get_handle(buffer);
        if (!h || h->numFds < 1 || h->numFds > 16) {
            errors++;
        } else {
            printf("HANDLE case=%u width=%u height=%u stride=%u numFds=%d numInts=%d\n",
                   i, d.width, d.height, d.stride, h->numFds, h->numInts);
            for (int j = 0; j < h->numFds; ++j) {
                r = inspect_fd(h->data[j]);
                total++;
                if (r == 1) dma++;
                if (r < 0) errors++;
            }
        }
        AHardwareBuffer_release(buffer);
    }
    FILE *maps = fopen("/proc/self/maps", "r");
    if (!maps) return 1;
    char line[1024];
    while (fgets(line, sizeof(line), maps))
        if (strstr(line, "gralloc") || strstr(line, "mapper")) printf("MAP: %s", line);
    fclose(maps);
    printf("RESULT total_fds=%u dma_buf_fds=%u errors=%d\n", total, dma, errors);
    if (errors || !total) return 1;
    return dma == total ? 0 : 2;
}
