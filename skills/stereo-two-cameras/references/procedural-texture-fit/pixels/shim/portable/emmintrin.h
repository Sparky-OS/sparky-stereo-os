// A portable stand-in for the SSE2 intrinsics that werkkzeug4's wz3_bitmap_code.cpp uses (its texture
// operators were written for SSE2, and the older werkkzeug3 for MMX). Only the 40 intrinsics that file calls
// are here, each with the meaning Intel's Intrinsics Guide gives it, written with Clang's generic vectors.
// Built with -msimd128 Clang turns them into WebAssembly SIMD128 instructions; without it, into scalar code.
// Both give the same integers, because every operation is integer arithmetic.
//
// First written for the edition's stereo texture module (ORDER 503; published in w3c-cg/pm-kr,
// experiments/stereo-texture, by Daniel Campos Ramos with Claude Sonnet 5.5) and carried here unchanged below
// this note, so that the editor's core and that module draw with the same stand-in. build.sh puts this folder
// on the include path only where the processor has no SSE2 (WebAssembly); on x86 the compiler's own header
// is used.
#ifndef STEREOTEX_EMMINTRIN_H
#define STEREOTEX_EMMINTRIN_H
#include <string.h>
#include <stdint.h>

typedef long long __m128i __attribute__((vector_size(16), __may_alias__));
typedef short v8s __attribute__((vector_size(16)));
typedef unsigned short v8u __attribute__((vector_size(16)));
typedef int v4i __attribute__((vector_size(16)));
typedef unsigned int v4u __attribute__((vector_size(16)));
typedef long long v2l __attribute__((vector_size(16)));
typedef unsigned long long v2ul __attribute__((vector_size(16)));
typedef int v8i32 __attribute__((vector_size(32)));
typedef unsigned int v8u32 __attribute__((vector_size(32)));

#define SI static inline __attribute__((always_inline))
#define S16(x) ((v8s)(x))
#define U16(x) ((v8u)(x))
#define S32(x) ((v4i)(x))
#define U32(x) ((v4u)(x))

SI __m128i _mm_setzero_si128(void) { return (__m128i){0, 0}; }
SI __m128i _mm_set1_epi16(short a) { return (__m128i)(v8s){a, a, a, a, a, a, a, a}; }
SI __m128i _mm_set1_epi32(int a) { return (__m128i)(v4i){a, a, a, a}; }
SI __m128i _mm_set_epi16(short e7, short e6, short e5, short e4, short e3, short e2, short e1, short e0) { return (__m128i)(v8s){e0, e1, e2, e3, e4, e5, e6, e7}; }
SI __m128i _mm_cvtsi32_si128(int a) { return (__m128i)(v4i){a, 0, 0, 0}; }

SI __m128i _mm_loadl_epi64(const __m128i *p) { long long v; memcpy(&v, p, 8); return (__m128i){v, 0}; }
SI __m128i _mm_load_si128(const __m128i *p) { return *p; }
SI void _mm_storel_epi64(__m128i *p, __m128i a) { long long v = a[0]; memcpy(p, &v, 8); }
SI void _mm_store_si128(__m128i *p, __m128i a) { *p = a; }

SI __m128i _mm_and_si128(__m128i a, __m128i b) { return a & b; }
SI __m128i _mm_or_si128(__m128i a, __m128i b) { return a | b; }
SI __m128i _mm_xor_si128(__m128i a, __m128i b) { return a ^ b; }
SI __m128i _mm_andnot_si128(__m128i a, __m128i b) { return ~a & b; }

SI __m128i _mm_add_epi16(__m128i a, __m128i b) { return (__m128i)(U16(a) + U16(b)); }
SI __m128i _mm_add_epi32(__m128i a, __m128i b) { return (__m128i)(U32(a) + U32(b)); }
SI __m128i _mm_sub_epi16(__m128i a, __m128i b) { return (__m128i)(U16(a) - U16(b)); }
SI __m128i _mm_sub_epi32(__m128i a, __m128i b) { return (__m128i)(U32(a) - U32(b)); }

SI __m128i _mm_adds_epi16(__m128i a, __m128i b)
{
  v8i32 s = __builtin_convertvector(S16(a), v8i32) + __builtin_convertvector(S16(b), v8i32);
  v8i32 hi = s > 32767, lo = s < -32768;
  s = (hi & 32767) | (lo & -32768) | (~(hi | lo) & s);
  return (__m128i)__builtin_convertvector(s, v8s);
}
SI __m128i _mm_subs_epi16(__m128i a, __m128i b)
{
  v8i32 s = __builtin_convertvector(S16(a), v8i32) - __builtin_convertvector(S16(b), v8i32);
  v8i32 hi = s > 32767, lo = s < -32768;
  s = (hi & 32767) | (lo & -32768) | (~(hi | lo) & s);
  return (__m128i)__builtin_convertvector(s, v8s);
}
SI __m128i _mm_adds_epu16(__m128i a, __m128i b)
{
  v8u32 s = __builtin_convertvector(U16(a), v8u32) + __builtin_convertvector(U16(b), v8u32);
  v8i32 hi = (v8i32)(s > 65535u);
  s = (v8u32)(((v8i32)s & ~hi) | (hi & 65535));
  return (__m128i)__builtin_convertvector(s, v8u);
}
SI __m128i _mm_subs_epu16(__m128i a, __m128i b)
{
  v8u x = U16(a), y = U16(b);
  v8s gt = (v8s)(x > y);
  return (__m128i)((x - y) & (v8u)gt);
}
SI __m128i _mm_avg_epu16(__m128i a, __m128i b)
{
  v8u32 s = __builtin_convertvector(U16(a), v8u32) + __builtin_convertvector(U16(b), v8u32) + 1u;
  return (__m128i)__builtin_convertvector(s >> 1, v8u);
}

SI __m128i _mm_cmpgt_epi16(__m128i a, __m128i b) { return (__m128i)(S16(a) > S16(b)); }
SI __m128i _mm_cmpgt_epi32(__m128i a, __m128i b) { return (__m128i)(S32(a) > S32(b)); }
SI __m128i _mm_max_epi16(__m128i a, __m128i b) { v8s m = S16(a) > S16(b); return (__m128i)((m & S16(a)) | (~m & S16(b))); }
SI __m128i _mm_min_epi16(__m128i a, __m128i b) { v8s m = S16(a) < S16(b); return (__m128i)((m & S16(a)) | (~m & S16(b))); }

SI __m128i _mm_mullo_epi16(__m128i a, __m128i b) { return (__m128i)(U16(a) * U16(b)); }
SI __m128i _mm_mulhi_epi16(__m128i a, __m128i b)
{
  v8i32 p = __builtin_convertvector(S16(a), v8i32) * __builtin_convertvector(S16(b), v8i32);
  return (__m128i)__builtin_convertvector(p >> 16, v8s);
}
SI __m128i _mm_mulhi_epu16(__m128i a, __m128i b)
{
  v8u32 p = __builtin_convertvector(U16(a), v8u32) * __builtin_convertvector(U16(b), v8u32);
  return (__m128i)__builtin_convertvector(p >> 16, v8u);
}
SI __m128i _mm_madd_epi16(__m128i a, __m128i b)
{
  v8i32 p = __builtin_convertvector(S16(a), v8i32) * __builtin_convertvector(S16(b), v8i32);
  v4i e = __builtin_shufflevector(p, p, 0, 2, 4, 6), o = __builtin_shufflevector(p, p, 1, 3, 5, 7);
  return (__m128i)(e + o);
}
SI __m128i _mm_packs_epi32(__m128i a, __m128i b)
{
  v8i32 s = __builtin_shufflevector(S32(a), S32(b), 0, 1, 2, 3, 4, 5, 6, 7);
  v8i32 hi = s > 32767, lo = s < -32768;
  s = (hi & 32767) | (lo & -32768) | (~(hi | lo) & s);
  return (__m128i)__builtin_convertvector(s, v8s);
}

SI __m128i _mm_slli_epi16(__m128i a, int n) { return n > 15 || n < 0 ? _mm_setzero_si128() : (__m128i)(U16(a) << n); }
SI __m128i _mm_srli_epi16(__m128i a, int n) { return n > 15 || n < 0 ? _mm_setzero_si128() : (__m128i)(U16(a) >> n); }
SI __m128i _mm_slli_epi32(__m128i a, int n) { return n > 31 || n < 0 ? _mm_setzero_si128() : (__m128i)(U32(a) << n); }
SI __m128i _mm_srli_epi32(__m128i a, int n) { return n > 31 || n < 0 ? _mm_setzero_si128() : (__m128i)(U32(a) >> n); }
SI __m128i _mm_srai_epi32(__m128i a, int n) { return (__m128i)(S32(a) >> (n > 31 || n < 0 ? 31 : n)); }
SI __m128i _mm_slli_epi64(__m128i a, int n) { return n > 63 || n < 0 ? _mm_setzero_si128() : (__m128i)((v2ul)a << n); }
SI __m128i _mm_srli_epi64(__m128i a, int n) { return n > 63 || n < 0 ? _mm_setzero_si128() : (__m128i)((v2ul)a >> n); }

#define _mm_shuffle_epi32(a, imm) ((__m128i)__builtin_shufflevector(S32(a), S32(a), (imm) & 3, ((imm) >> 2) & 3, ((imm) >> 4) & 3, ((imm) >> 6) & 3))
#define _mm_shufflelo_epi16(a, imm) ((__m128i)__builtin_shufflevector(S16(a), S16(a), (imm) & 3, ((imm) >> 2) & 3, ((imm) >> 4) & 3, ((imm) >> 6) & 3, 4, 5, 6, 7))
#define _mm_shufflehi_epi16(a, imm) ((__m128i)__builtin_shufflevector(S16(a), S16(a), 0, 1, 2, 3, 4 + ((imm) & 3), 4 + (((imm) >> 2) & 3), 4 + (((imm) >> 4) & 3), 4 + (((imm) >> 6) & 3)))

SI __m128i _mm_unpacklo_epi16(__m128i a, __m128i b) { return (__m128i)__builtin_shufflevector(S16(a), S16(b), 0, 8, 1, 9, 2, 10, 3, 11); }
SI __m128i _mm_unpackhi_epi16(__m128i a, __m128i b) { return (__m128i)__builtin_shufflevector(S16(a), S16(b), 4, 12, 5, 13, 6, 14, 7, 15); }

#undef SI
#endif
