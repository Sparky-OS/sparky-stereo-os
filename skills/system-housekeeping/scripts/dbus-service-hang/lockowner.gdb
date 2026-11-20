set pagination off
set print pretty on
set confirm off
echo === threads\n
info threads
echo === the main thread: the GOnce it owns and the mutex it waits for\n
thread 1
frame function g_vfs_get_default
print vfs_default_singleton
print &vfs_default_singleton
frame function _g_io_module_get_default
print extension_point
print default_modules_lock
print *(pthread_mutex_t *) default_modules_lock.p
echo === owner (kernel thread id) and recursion count of default_modules_lock\n
print ((pthread_mutex_t *) default_modules_lock.p)->__data.__owner
print ((pthread_mutex_t *) default_modules_lock.p)->__data.__count
echo === the proxy resolver's GOnce\n
print 'gproxyresolver.c'::proxy_resolver_default_singleton
print &'gproxyresolver.c'::proxy_resolver_default_singleton
echo === every location whose GOnce is being initialised right now (gthread.c g_once_init_list)\n
print 'gthread.c'::g_once_init_list
print *'gthread.c'::g_once_init_list
print *'gthread.c'::g_once_init_list->next
echo === every thread\n
thread apply all bt
echo === every thread, full\n
thread apply all bt full
