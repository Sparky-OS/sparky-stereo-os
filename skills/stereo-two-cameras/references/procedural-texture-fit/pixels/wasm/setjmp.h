/* WebAssembly without the exception-handling extension has no setjmp and longjmp, and wasi-libc refuses its own
   header. FreeType (its rasterizer, on a band overflow) and libpng (on a broken file) jump only on an error. This
   stand-in, used only for the WebAssembly build, lets them compile: setjmp returns 0, and a longjmp says which error
   came and stops the program (memory no-silent-fallbacks: never a silent wrong picture). The drawings of milestone
   2b never reach one: their glyphs are small and no PNG is read while drawing. */
#ifndef P2P_WASM_SETJMP_H
#define P2P_WASM_SETJMP_H
typedef int jmp_buf[1];
#ifdef __cplusplus
extern "C" {
#endif
_Noreturn void longjmp(jmp_buf b, int v);
#ifdef __cplusplus
}
#endif
#define setjmp(b) 0
#endif
