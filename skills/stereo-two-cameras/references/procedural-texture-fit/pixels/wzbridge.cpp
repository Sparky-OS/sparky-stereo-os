// The bridge between the Zig side of stereotex and Farbrausch's texture operators.
//
// The operators are werkkzeug4's wz3_bitmap_code.cpp (fr_public, BSD licence), Farbrausch's portable C++
// version of werkkzeug3's texture generator, with the small changes of patch_wz3.py (functions that need
// fonts, image files or the vector operator are left out). The calls below follow werkkzeug3's Bitmap_*
// functions parameter for parameter; they are lane 473x's wzrender.cpp, turned into a function that takes
// one operator at a time and says what it refuses.
//
// Everything is extern "C": Zig calls it, and the same file builds natively next to the Zig CLI.
#include "wz3_bitmap_code.cpp"
#include <stdint.h>
#include <stdio.h>
#include <setjmp.h>

static size_t g_live = 0;                    // bytes of bitmaps alive
static size_t g_limit = (size_t) 192 << 20;  // the most the graph may hold at once
static char g_fail[160];
static jmp_buf g_jb;
static int g_jb_on = 0;

extern "C" void wzb_fail(const char *what, int line)
{
  snprintf(g_fail, sizeof g_fail, "the operator code stopped on a check (%.100s, line %d)", what, line);
  if (g_jb_on) longjmp(g_jb, 1);   // the fitter tries values no artist typed: a failed check refuses the candidate
  __builtin_trap();
}

extern "C" const char *wzb_failure(void) { return g_fail; }
extern "C" void wzb_init(void) { xInitPerlin(); }
extern "C" void wzb_set_limit(size_t bytes) { g_limit = bytes; }
extern "C" size_t wzb_live(void) { return g_live; }
extern "C" int wzb_simd(void)
{
#if defined(__wasm_simd128__)
  return 1;
#else
  return 0;
#endif
}

struct Bm { GenBitmap *g; };

static GenBitmap *clone(GenBitmap *in)
{
  GenBitmap *o = new GenBitmap;
  o->Init(in->XSize, in->YSize);
  memcpy(o->Data, in->Data, sizeof(sU64) * in->Size);
  return o;
}

extern "C" void wzb_free(void *p)
{
  GenBitmap *b = (GenBitmap *) p;
  if (!b) return;
  g_live -= (size_t) b->Size * sizeof(sU64);
  delete b;
}

extern "C" int wzb_width(void *p) { return ((GenBitmap *) p)->XSize; }
extern "C" int wzb_height(void *p) { return ((GenBitmap *) p)->YSize; }

// RGBA8: the 15-bit channels of werkkzeug3 (0..0x7fff) become 8 bits the way wzrender did (shift by 7, clamp);
// alpha is not kept: werkkzeug3 textures use it for blending inside the graph, and the result is opaque.
extern "C" void wzb_rgba(void *p, uint8_t *dst)
{
  GenBitmap *b = (GenBitmap *) p;
  for (int i = 0; i < b->Size; i++) {
    const sU16 *q = (const sU16 *) &b->Data[i];   // blue, green, red, alpha
    for (int c = 0; c < 3; c++) { int x = q[2 - c] >> 7; dst[4 * i + c] = x > 255 ? 255 : x; }
    dst[4 * i + 3] = 255;
  }
}

#define SETERR(...) do { snprintf(err, errlen, __VA_ARGS__); return 1; } while (0)

// Draw one operator. w holds its 32 parameter words (as a .k project stores them), in[] its inputs.
// Returns 0 and the new bitmap in *out, or 1 and a sentence in err.
static int wzb_apply_inner(const char *name, const uint32_t *w32, int nin, void **inp, void **out, char *err, int errlen)
{
  GenBitmap **I = (GenBitmap **) inp;
  uint32_t w[32];
  memcpy(w, w32, sizeof w);
  #define U(i) (w[i])
  #define N(i) ((sInt) w[i])
  #define F(i) (*(sF32 *) &w[i])
  #define IS(s) (strcmp(name, s) == 0)
  #define NEED(n) if (nin != (n)) SETERR("takes %d input(s), the graph gives %d", n, nin)

  // how big the answer will be: checked before anything is allocated
  long long xs = 0, ys = 0;
  if (IS("Flat") || IS("Perlin") || IS("Cell") || IS("Bricks")) {
    if (nin != 0) SETERR("takes no input, the graph gives %d", nin);
    if (N(0) < 0 || N(0) > 12 || N(1) < 0 || N(1) > 12) SETERR("size exponents %d and %d are outside 0..12 (a side of 1 to 4096 pixels)", N(0), N(1));
    xs = 1LL << N(0); ys = 1LL << N(1);
  } else if (IS("Gradient")) {
    if (nin != 0) SETERR("takes no input, the graph gives %d", nin);
    if (N(0) < 0 || N(0) > 12 || N(1) < 0 || N(1) > 12) SETERR("size exponents %d and %d are outside 0..12 (a side of 1 to 4096 pixels)", N(0), N(1));
    xs = 1LL << N(0); ys = 1LL << N(1);
  } else if (nin >= 1 && I[0]) {
    xs = I[0]->XSize; ys = I[0]->YSize;
    if (IS("Transform")) {
      if (N(6) < 0 || N(6) > 13 || N(7) < 0 || N(7) > 13) SETERR("new size %d, %d is outside 0..13", N(6), N(7));
      if (N(6)) xs = 1LL << (N(6) - 1);
      if (N(7)) ys = 1LL << (N(7) - 1);
    }
  }
  if (xs * ys * 8 * 3 + (long long) g_live > (long long) g_limit)
    SETERR("a %lldx%lld picture needs about %lld MB and the graph already holds %lld MB; the limit is %lld MB",
           xs, ys, xs * ys * 8 * 3 >> 20, (long long) (g_live >> 20), (long long) (g_limit >> 20));
  if (xs * ys < 4 || (xs * ys & 3)) SETERR("a %lldx%lld picture is too small for the operators (they work four pixels at a time)", xs, ys);

  if (IS("Perlin") && (N(2) < 0 || N(2) > 16 || N(3) < 0 || N(3) > 16)) SETERR("frequency %d and octaves %d are outside 0..16", N(2), N(3));
  if (IS("Distort") && nin == 2 && I[0]->Size != I[1]->Size) SETERR("the map is %dx%d and the picture %dx%d; they must be the same size", I[1]->XSize, I[1]->YSize, I[0]->XSize, I[0]->YSize);

  GenBitmap *o = 0;
  if (IS("Flat")) { o = new GenBitmap; o->Init(1 << N(0), 1 << N(1)); o->Flat(U(2)); }
  else if (IS("Perlin")) { o = new GenBitmap; o->Init(1 << N(0), 1 << N(1)); o->Perlin(N(2), N(3), F(4), N(5), N(6), F(7), F(8), U(9), U(10)); }
  else if (IS("Cell")) { o = new GenBitmap; o->Init(1 << N(0), 1 << N(1)); o->Cell(U(2), U(3), U(4), N(5), N(6), F(7), F(8), N(9), F(10), N(11), F(12)); }
  else if (IS("Gradient")) { o = Bitmap_Gradient(N(0), N(1), U(2), U(3), F(4), F(5), F(6), N(7)); }
  else if (IS("Bricks")) { o = new GenBitmap; o->Init(1 << N(0), 1 << N(1)); o->Bricks(1 << N(0), 1 << N(1), U(2), U(3), U(4), F(5), F(6), N(7), N(8), N(9), N(10), N(11), F(12), F(13)); }
  else if (IS("Color")) { NEED(1); sU64 col = GenBitmap::GetColor64(U(1)); o = new GenBitmap; o->InitSize(I[0]); o->Loop(N(0) + BI_MULCOL, &col, I[0]); }
  else if (IS("Range")) {
    NEED(1);
    sU64 cx[2] = { GenBitmap::GetColor64(U(1)), GenBitmap::GetColor64(U(2)) };
    o = new GenBitmap; o->InitSize(I[0]);
    GenBitmap *src = I[0];
    if (N(0) & 1) { o->Loop(BI_GRAY, cx, src); src = o; }
    if (N(0) & 2) { o->Loop(BI_INVERT, cx, src); src = o; }
    o->Loop(BI_RANGE, cx, src);
  }
  else if (IS("Merge")) {
    if (nin < 1) SETERR("takes at least one input");
    static const sU8 modes[] = { BI_ADD, BI_SUB, BI_MUL, BI_DIFF, BI_ALPHA, BI_BRIGHTNESS, BI_HARDLIGHT, BI_OVER, BI_ADDSMOOTH, BI_MIN, BI_MAX };
    if (N(0) < 0 || N(0) > 10) SETERR("merge mode %d is outside 0..10", N(0));
    for (int i = 1; i < nin; i++)
      if (I[i]->XSize != I[0]->XSize || I[i]->YSize != I[0]->YSize) SETERR("merge of pictures of different sizes");
    o = clone(I[0]);
    for (int i = 1; i < nin; i++) o->Loop(modes[N(0)], I[i], o);
  }
  else if (IS("Mask")) {
    NEED(3);
    if (I[0]->Size != I[1]->Size || I[0]->Size != I[2]->Size) SETERR("mask of pictures of different sizes");
    if (N(0) < 0 || N(0) > 3) SETERR("mask mode %d is outside 0..3", N(0));
    o = new GenBitmap; o->InitSize(I[0]);
    o->Loop(BI_GRAY, I[0], I[0]);
    switch (N(0)) {
      case 0: o->Loop(BI_MERGE, I[1], I[2]); break;
      case 1: o->Loop(BI_MUL, I[1], o); o->Loop(BI_ADD, I[2], o); break;
      case 2: o->Loop(BI_MUL, I[1], o); o->Loop(BI_SUBR, I[2], o); break;
      case 3: o->Loop(BI_MULMERGE, I[1], I[2]); break;
    }
  }
  else if (IS("GlowRect") || IS("GlowRectOld")) { NEED(1); o = clone(I[0]); o->GlowRect(F(0), F(1), F(2), F(3), F(4), F(5), U(6), F(7), F(8), N(9), N(10)); }
  else if (IS("Dots")) { NEED(1); o = clone(I[0]); o->Dots(U(0), U(1), N(2), N(3)); }
  else if (IS("Blur")) { NEED(1); o = clone(I[0]); o->Blur(N(0), F(1), F(2), F(3)); }
  else if (IS("Sharpen")) { NEED(1); o = new GenBitmap; o->InitSize(I[0]); o->Sharpen(I[0], N(0), F(1), F(2), F(3)); }
  else if (IS("HSCB")) { NEED(1); o = clone(I[0]); o->HSCB(F(0), F(1), F(2), F(3)); }
  else if (IS("ColorBalance")) { NEED(1); o = clone(I[0]); o->ColorBalance(sVector30(F(0), F(1), F(2)), sVector30(F(3), F(4), F(5)), sVector30(F(6), F(7), F(8))); }
  else if (IS("Transform")) { NEED(1); o = new GenBitmap; o->Init((sInt) xs, (sInt) ys); o->Rotate(I[0], 0.5f, 0.5f, F(0), F(1), F(2), F(3), F(4), N(5)); }
  else if (IS("TransformMul")) { NEED(1); o = clone(I[0]); o->RotateMul(0.5f, 0.5f, F(0), F(1), F(2), F(3), F(4), N(5), U(6), N(7), N(8), U(9)); }
  else if (IS("Twirl")) { NEED(1); o = new GenBitmap; o->InitSize(I[0]); o->Twirl(I[0], F(0), F(1), F(2), F(3), F(4), F(5), N(6)); }
  else if (IS("Distort")) { NEED(2); o = new GenBitmap; o->InitSize(I[0]); o->Distort(I[0], I[1], F(0), N(1)); }
  else if (IS("Normals")) { NEED(1); o = new GenBitmap; o->InitSize(I[0]); o->Normals(I[0], F(0), N(1)); }
  else if (IS("Light")) { NEED(1); o = clone(I[0]); o->Bump(0, N(0), F(1), F(2), F(3), F(4), F(5), U(6), U(7), F(8), F(9), F(10), U(7), 0, 0); }
  else if (IS("Bump")) {
    NEED(2);
    if (I[0]->Size != I[1]->Size) SETERR("bump of pictures of different sizes");
    o = clone(I[0]); o->Bump(I[1], N(0), F(1), F(2), F(3), F(4), F(5), U(6), U(7), F(8), F(9), F(10), U(11), F(12), F(13));
  }
  else if (IS("Unwrap")) { NEED(1); o = new GenBitmap; o->InitSize(I[0]); o->Unwrap(I[0], N(0)); }
  else if (IS("Bulge")) { NEED(1); o = new GenBitmap; o->InitSize(I[0]); o->Bulge(I[0], F(0)); }
  else if (IS("Paste")) { NEED(2); o = Bitmap_Paste(clone(I[0]), I[1], F(0), F(1), F(2), F(3), F(4), F(5), F(6), N(7)); }
  else if (IS("Format") || IS("Pass")) { NEED(1); o = clone(I[0]); }
  else if (IS("Text")) SETERR("needs Windows fonts, which this module does not have");
  else SETERR("is not an operator of this module");
  if (!o) SETERR("gave nothing");
  g_live += (size_t) o->Size * sizeof(sU64);
  *out = o;
  return 0;
}

// The fitter's entry: the same call, but a failed check inside the operator code refuses the candidate
// (the bitmaps of that one call are lost; the fitter counts them) instead of stopping the program.
extern "C" int wzb_apply(const char *name, const uint32_t *w32, int nin, void **inp, void **out, char *err, int errlen)
{
  g_jb_on = 1;
  if (setjmp(g_jb)) { g_jb_on = 0; snprintf(err, errlen, "%s", g_fail); return 2; }
  int r = wzb_apply_inner(name, w32, nin, inp, out, err, errlen);
  g_jb_on = 0;
  return r;
}
