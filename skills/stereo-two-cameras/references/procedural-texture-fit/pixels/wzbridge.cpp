// The bridge between the Zig side of stereotex and Farbrausch's texture operators.
//
// The operators are werkkzeug4's wz3_bitmap_code.cpp (fr_public, BSD licence), Farbrausch's portable C++
// version of werkkzeug3's texture generator, with the small changes of patch_wz3.py (functions that need
// image files or the vector operator are left out). Text draws through wzfont.c, a font renderer on
// FreeType that reads the font's own outlines; which font file stands for a name comes from the font map. The calls below follow werkkzeug3's Bitmap_*
// functions parameter for parameter; they are lane 473x's wzrender.cpp, turned into a function that takes
// one operator at a time and says what it refuses.
//
// Everything is extern "C": Zig calls it, and the same file builds natively next to the Zig CLI.
#include "wz3_bitmap_code.cpp"
#include <stdint.h>
#include <stdio.h>
#if !defined(__wasm__)
#include <setjmp.h>
#endif

static size_t g_live = 0;                    // bytes of bitmaps alive
static size_t g_limit = (size_t) 192 << 20;  // the most the graph may hold at once
static char g_fail[160];
#if !defined(__wasm__)
static jmp_buf g_jb;
#endif
static int g_jb_on = 0;

extern "C" void wzb_fail(const char *what, int line)
{
  snprintf(g_fail, sizeof g_fail, "the operator code stopped on a check (%.100s, line %d)", what, line);
#if !defined(__wasm__)
  if (g_jb_on) longjmp(g_jb, 1);   // the fitter tries values no artist typed: a failed check refuses the candidate
#else
  // WebAssembly without the exception extension has no longjmp: the drawing path says the check and stops (lane
  // 514's finding); the fitter, which needs the refusal, runs natively
  fprintf(stderr, "%s\n", g_fail);
#endif
  __builtin_trap();
}

extern "C" const char *wzb_failure(void) { return g_fail; }
#if defined(__wasm__)
// the stand-in of wasm/setjmp.h: an error that would jump (FreeType's rasterizer, libpng) is said, and the program stops
extern "C" _Noreturn void longjmp(int *, int)
{
  fprintf(stderr, "stopped: a library (FreeType's rasterizer or libpng) asked for a long jump after an error; this WebAssembly build has none\n");
  abort();
}
#endif
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

#define SETERR(...) do { snprintf(err, errlen, __VA_ARGS__); return 1; } while (0)

struct Bm { GenBitmap *g; };

// The two strings of the next Text operator (the text and the font's name, 8-bit, Windows code page 1252).
static const unsigned char *g_text = (const unsigned char *) "", *g_font = (const unsigned char *) "";
extern "C" void wzb_strings(const char *text, const char *font)
{
  g_text = (const unsigned char *) (text ? text : "");
  g_font = (const unsigned char *) (font ? font : "");
}
// Version 2 of Text (our extension, wztext2.c): the text is UTF-8, the font an entry of the font index, and a
// third string holds the variable font's axis values.
static const char *g_axes = "";
extern "C" void wzb_strings3(const char *text, const char *font, const char *axes)
{
  wzb_strings(text, font);
  g_axes = axes ? axes : "";
}
extern "C" int ht2_draw(int XS, int YS, float x, float y, float emh, float avgw, unsigned flags, int extspace, float lineskip,
                        const char *text, const char *key, const char *axes, int palette, int form, unsigned col,
                        uint8_t *out, char *err, int errlen);
extern "C" int ht2_glyph_mask(const char *key, unsigned cp, int side, unsigned char *outm, float *v, int *formp, unsigned char *rgba_out);
extern "C" int ht2_font_spacing(const char *key, float *space, float *avg);
extern "C" int wzb_glyph_mask2(const char *key, unsigned cp, int side, uint8_t *out, float *v, int *form, uint8_t *rgba)
{
  return ht2_glyph_mask(key, cp, side, out, v, form, rgba);
}
extern "C" int wzb_font_spacing(const char *key, float *space, float *avg) { return ht2_font_spacing(key, space, avg); }
// What the font renderer has to say about the texts drawn so far: one sentence per line (the font that
// stood in for each name, every character the font had no glyph for).
extern "C" const char *wzb_notes(void) { return hf_notes(); }
extern "C" void wzb_notes_clear(void) { hf_notes_clear(); }
// One glyph's ink stretched to a square and its measures, for the fitter's reading of shapes (see wzfont.c).
extern "C" int wzb_glyph_mask(const char *font, int c, int side, uint8_t *out, float *v)
{
  char err[300];
  return hf_glyph_mask(font, c, side, out, v, err, sizeof err);
}
// A picture handed in as a bitmap, so the fitter can run one operator on the picture it reads (Twirl backwards).
extern "C" void *wzb_from_rgba(int xs, int ys, const uint8_t *rgba)
{
  GenBitmap *o = new GenBitmap;
  o->Init(xs, ys);
  for (int i = 0; i < o->Size; i++) {
    sU16 *q = (sU16 *) &o->Data[i];   // blue, green, red, alpha
    for (int c = 0; c < 3; c++) { int x = rgba[4 * i + c]; q[2 - c] = (sU16) ((x << 7) | (x >> 1)); }
    q[3] = 0x7fff;
  }
  g_live += (size_t) o->Size * sizeof(sU64);
  return o;
}

// werkkzeug3's Bitmap_Text (fr_public/werkkzeug3/genbitmap.cpp), parameter for parameter:
//   x, y        where the text starts, in parts of the picture
//   width       the height of the font's em square, in parts of the picture's height (werkkzeug3 hands
//               ys*width to CreateFont as the height: FontBegin(xs,ys,font,xs*height,ys*width,4))
//   height      the average character width, in parts of the picture's width; 0 keeps the font's own
//   flags       1 centre across, 2 centre down, 0x10..0x70 a font page (one letter after the other), 0x80 keep the drawing
//   extspace, inspace   the space around every letter of a font page; extspace + 2 pixels also moves a plain text
//   lineskip    the line's height in font heights
// A plain text is drawn by Farbrausch's own GenBitmap::Text (werkkzeug4's copy of the same code, which
// lacks only the extspace offset: it is added to the position). A font page is not in werkkzeug4's copy:
// its loop is werkkzeug3's, taken over line by line.
static int text_wz3(GenBitmap *bm, sF32 x, sF32 y, sF32 width, sF32 height, sU32 col, sU32 flags, sInt extspace, sF32 inspace, sF32 lineskip,
                    const unsigned char *text, const unsigned char *font, char *err, int errlen)
{
  const sInt alias = 4;
  sInt xs = bm->XSize * alias, ys = bm->YSize * alias;
  if (flags & ~0xf3u) SETERR("flags 0x%x hold bits werkkzeug3's Text does not have", flags);
  if (!(width > 0) || width > 64) SETERR("font height %g of the picture is outside what this module draws", width);
  if (height < 0 || height > 64) SETERR("character width %g of the picture is outside what this module draws", height);
  if (extspace < 0 || extspace > 1024) SETERR("space %d around letters is outside 0..1024", extspace);
  sInt es = extspace * alias + 2 * alias;
  sInt page = (flags & 0x70) >> 4;
  size_t tl = strlen((const char *) text), fl = strlen((const char *) font);
  if (!page) {
    sChar *wt = new sChar[tl + 1], *wf = new sChar[fl + 1];
    for (size_t i = 0; i <= tl; i++) wt[i] = text[i];
    for (size_t i = 0; i <= fl; i++) wf[i] = font[i];
    bm->Text(x + (sF32) es / xs, y + (sF32) es / ys, height, width, col, flags & 3, lineskip, wt, wf);
    delete[] wt; delete[] wf;
    if (g_f2d_err[0]) SETERR("%s", g_f2d_err);
    return 0;
  }
  // font page mode (werkkzeug3 only)
  char nm[64]; size_t k = 0;
  for (; font[k] && k < 63; k++) nm[k] = (char) font[k];
  nm[k] = 0;
  sInt yf = hf_begin(xs, ys, nm, (sInt) (xs * height), (sInt) (ys * width), err, errlen);
  if (yf < 0) return 1;
  sInt is = inspace * xs;
  sInt xp = x * xs + es, yp = y * ys + es;
  sInt count = 0, chr = 'a', widths[3];
  const unsigned char *t = text;
  while (*t || chr < count) {
    if (t[0] == '-' && t[1] != '-' && t[1] != 0) { t++; count = (*t++) & 255; }
    if (t[0] == '-' && t[1] == '-') t++;
    if (chr < count) chr++;
    else { count = 0; chr = (*t++) & 255; }
    hf_abc(chr, widths);
    sInt w1 = widths[1];
    if (xp + w1 + es + 2 * is >= xs) {
      yp = (yp + yf + 2 * is + alias - 1) & ~(alias - 1);
      yp += es;
      xp = x * xs + es;
      if (yp + yf + es + 2 * is >= ys) break;
    }
    unsigned char c = (unsigned char) chr;
    hf_print(xp + is - widths[0], yp + is, &c, 1);
    xp = (xp + w1 + 2 * is + alias - 1) & ~(alias - 1);
    xp += es;
  }
  // write to bitmap: the same averaging of 4 by 4 page pixels and the same fade as GenBitmap::Text
  const unsigned char *pg = hf_page();
  __m128i color = GetColor128(col);
  sInt i = 0;
  for (sInt yi = 0; yi < bm->YSize; yi++) {
    const unsigned char *sp = pg + (size_t) yi * xs * alias;
    for (sInt xi = 0; xi < bm->XSize; xi++) {
      sU32 fade = 0;
      for (sInt a = 0; a < 4; a++) for (sInt b = 0; b < 4; b++) fade += sp[b + a * xs];
      fade >>= 4;
      fade = (fade) | (fade << 8);
      FadeOver(bm->Data[i], color, fade);
      i++; sp += alias;
    }
  }
  hf_end();
  return 0;
}

// Version 2: wztext2.c draws the text as a premultiplied picture; it lies over the input the way GenBitmap::Text's
// FadeOver lays the operator's colour (where the text covers fully, the text; where it does not, the input).
static int text_v2(GenBitmap *bm, sF32 x, sF32 y, sF32 width, sF32 height, sU32 col, sU32 flags, sInt extspace, sF32 lineskip,
                   sInt palette, sInt form, char *err, int errlen)
{
  uint8_t *pic = new uint8_t[(size_t) bm->Size * 4];
  if (ht2_draw(bm->XSize, bm->YSize, x, y, width, height, flags, extspace, lineskip, (const char *) g_text, (const char *) g_font, g_axes,
               palette, form, col, pic, err, errlen)) { delete[] pic; return 1; }
  for (sInt i = 0; i < bm->Size; i++) {
    sU16 *q = (sU16 *) &bm->Data[i];   // blue, green, red, alpha
    unsigned a = pic[4 * i + 3];
    if (!a) continue;
    for (int c = 0; c < 4; c++) {
      unsigned s15 = ((unsigned) pic[4 * i + c] << 7) | (pic[4 * i + c] >> 1);
      q[c] = (sU16) (s15 + ((unsigned) q[c] * (255 - a) + 127) / 255);
    }
  }
  delete[] pic;
  return 0;
}

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

// Milestone 2b: an empty bitmap for a modern operator (ops/*.zig draws into it), and its pixels (blue, green, red,
// alpha; 15 bits each), so the modern operators and werkkzeug's own take each other's pictures.
extern "C" void *wzb_new(int xs, int ys)
{
  if (xs < 1 || ys < 1 || (long long) xs * ys > (1LL << 26)) return 0;
  if ((size_t) xs * ys * sizeof(sU64) + g_live > g_limit) return 0;
  GenBitmap *o = new GenBitmap;
  o->Init(xs, ys);
  memset(o->Data, 0, sizeof(sU64) * o->Size);
  g_live += (size_t) o->Size * sizeof(sU64);
  return o;
}
extern "C" uint16_t *wzb_data(void *p) { return (uint16_t *) ((GenBitmap *) p)->Data; }

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
  else if (IS("Text")) {
    NEED(1);
    o = clone(I[0]);
    // version 2 (our extension) says so in its tenth word; werkkzeug3's own Text has nine
    if (U(9) == 2) { if (text_v2(o, F(0), F(1), F(2), F(3), U(4), U(5), N(6), F(8), N(10), N(11), err, errlen)) { delete o; return 1; } }
    else if (U(9) != 0) { delete o; SETERR("Text version %u is not known (1: werkkzeug3's, 2: any font, any character)", U(9)); }
    else if (text_wz3(o, F(0), F(1), F(2), F(3), U(4), U(5), N(6), F(7), F(8), g_text, g_font, err, errlen)) { delete o; return 1; }
  }
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
#if !defined(__wasm__)
  if (setjmp(g_jb)) { g_jb_on = 0; snprintf(err, errlen, "%s", g_fail); return 2; }
#endif
  int r = wzb_apply_inner(name, w32, nin, inp, out, err, errlen);
  g_jb_on = 0;
  return r;
}
