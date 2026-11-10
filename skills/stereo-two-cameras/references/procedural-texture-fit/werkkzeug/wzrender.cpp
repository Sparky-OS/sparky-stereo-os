// wzrender: draw a werkkzeug3 texture graph with Farbrausch's own operator code.
//
// The operators are the ones of werkkzeug4's wz3_bitmap_code.cpp (fr_public/altona_wz4/wz4/wz4frlib,
// BSD licence), which is Farbrausch's portable C++ version of werkkzeug3's texture generator
// (werkkzeug3's own genbitmap.cpp is written in x86 MMX assembly inside Visual C++ and does not
// compile here). The calls below follow werkkzeug3's Bitmap_* functions parameter for parameter.
//
// Input, one operator per line:   ID NAME INPUTS WORDS...
//   INPUTS is "-" or ids joined by commas; WORDS are the operator's 32-bit parameter words in hex,
//   exactly as a .k project file stores them. The last line is "out ID".
// Output: (width, height) as two int32, then RGB8.
#include "wz3_bitmap_code.cpp"
#include <map>
#include <string>
#include <sstream>
#include <iostream>

static GenBitmap *clone(GenBitmap *in)
{
  GenBitmap *o = new GenBitmap;
  o->Init(in->XSize, in->YSize);
  memcpy(o->Data, in->Data, sizeof(sU64) * in->Size);
  return o;
}

int main()
{
  xInitPerlin();
  std::map<std::string, GenBitmap *> v;
  std::string line;
  while (std::getline(std::cin, line)) {
    std::istringstream in(line);
    std::string id, name, ins;
    in >> id;
    if (id.empty() || id[0] == '#') continue;
    if (id == "out") {
      in >> name;
      GenBitmap *b = v.count(name) ? v[name] : 0;
      if (!b) { fprintf(stderr, "no result %s\n", name.c_str()); return 3; }
      int wh[2] = { b->XSize, b->YSize };
      fwrite(wh, 4, 2, stdout);
      std::vector<unsigned char> out(size_t(b->Size) * 3);
      for (int i = 0; i < b->Size; i++) {
        const sU16 *p = (const sU16 *) &b->Data[i];   // blue, green, red, alpha; 0..0x7fff
        for (int c = 0; c < 3; c++) { int x = p[2 - c] >> 7; out[3 * i + c] = x > 255 ? 255 : x; }
      }
      fwrite(out.data(), 1, out.size(), stdout);
      return 0;
    }
    in >> name >> ins;
    std::vector<GenBitmap *> I;
    if (ins != "-") {
      std::istringstream is(ins);
      std::string t;
      while (std::getline(is, t, ',')) {
        if (!v.count(t) || !v[t]) { fprintf(stderr, "%s: input %s missing\n", id.c_str(), t.c_str()); return 4; }
        I.push_back(v[t]);
      }
    }
    std::vector<sU32> w;
    std::string hx;
    while (in >> hx) w.push_back((sU32) strtoul(hx.c_str(), 0, 16));
    w.resize(32, 0);
    #define U(i) (w[i])
    #define N(i) ((sInt) w[i])
    #define F(i) (*(sF32 *) &w[i])
    GenBitmap *o = 0;
    #define NEED(n) if ((int) I.size() < n) { fprintf(stderr, "%s %s: needs %d inputs\n", id.c_str(), name.c_str(), n); return 5; }
    if (name == "Flat") { o = new GenBitmap; o->Init(1 << N(0), 1 << N(1)); o->Flat(U(2)); }
    else if (name == "Perlin") { o = new GenBitmap; o->Init(1 << N(0), 1 << N(1)); o->Perlin(N(2), N(3), F(4), N(5), N(6), F(7), F(8), U(9), U(10)); }
    else if (name == "Cell") { o = new GenBitmap; o->Init(1 << N(0), 1 << N(1)); o->Cell(U(2), U(3), U(4), N(5), N(6), F(7), F(8), N(9), F(10), N(11), F(12)); }
    else if (name == "Gradient") { o = Bitmap_Gradient(N(0), N(1), U(2), U(3), F(4), F(5), F(6), N(7)); }
    else if (name == "Bricks") { o = new GenBitmap; o->Init(1 << N(0), 1 << N(1)); o->Bricks(1 << N(0), 1 << N(1), U(2), U(3), U(4), F(5), F(6), N(7), N(8), N(9), N(10), N(11), F(12), F(13)); }
    else if (name == "Color") { NEED(1); sU64 col = GenBitmap::GetColor64(U(1)); o = new GenBitmap; o->InitSize(I[0]); o->Loop(N(0) + BI_MULCOL, &col, I[0]); }
    else if (name == "Range") {
      NEED(1);
      sU64 cx[2] = { GenBitmap::GetColor64(U(1)), GenBitmap::GetColor64(U(2)) };
      o = new GenBitmap; o->InitSize(I[0]);
      GenBitmap *src = I[0];
      if (N(0) & 1) { o->Loop(BI_GRAY, cx, src); src = o; }
      if (N(0) & 2) { o->Loop(BI_INVERT, cx, src); src = o; }
      o->Loop(BI_RANGE, cx, src);
    }
    else if (name == "Merge") {
      NEED(1);
      static sU8 modes[] = { BI_ADD, BI_SUB, BI_MUL, BI_DIFF, BI_ALPHA, BI_BRIGHTNESS, BI_HARDLIGHT, BI_OVER, BI_ADDSMOOTH, BI_MIN, BI_MAX };
      if (N(0) < 0 || N(0) > 10) { fprintf(stderr, "%s: merge mode %d\n", id.c_str(), N(0)); return 6; }
      for (size_t i = 1; i < I.size(); i++)
        if (I[i]->XSize != I[0]->XSize || I[i]->YSize != I[0]->YSize) { fprintf(stderr, "%s: merge of different sizes\n", id.c_str()); return 6; }
      o = clone(I[0]);
      for (size_t i = 1; i < I.size(); i++) o->Loop(modes[N(0)], I[i], o);
    }
    else if (name == "Mask") {
      NEED(3);
      if (I[0]->Size != I[1]->Size || I[0]->Size != I[2]->Size) { fprintf(stderr, "%s: mask of different sizes\n", id.c_str()); return 6; }
      o = new GenBitmap; o->InitSize(I[0]);
      o->Loop(BI_GRAY, I[0], I[0]);
      switch (N(0)) {
        case 0: o->Loop(BI_MERGE, I[1], I[2]); break;
        case 1: o->Loop(BI_MUL, I[1], o); o->Loop(BI_ADD, I[2], o); break;
        case 2: o->Loop(BI_MUL, I[1], o); o->Loop(BI_SUBR, I[2], o); break;
        case 3: o->Loop(BI_MULMERGE, I[1], I[2]); break;
      }
    }
    else if (name == "GlowRect" || name == "GlowRectOld") { NEED(1); o = clone(I[0]); o->GlowRect(F(0), F(1), F(2), F(3), F(4), F(5), U(6), F(7), F(8), N(9), N(10)); }
    else if (name == "Dots") { NEED(1); o = clone(I[0]); o->Dots(U(0), U(1), N(2), N(3)); }
    else if (name == "Blur") { NEED(1); o = clone(I[0]); o->Blur(N(0), F(1), F(2), F(3)); }
    else if (name == "Sharpen") { NEED(1); o = new GenBitmap; o->InitSize(I[0]); o->Sharpen(I[0], N(0), F(1), F(2), F(3)); }
    else if (name == "HSCB") { NEED(1); o = clone(I[0]); o->HSCB(F(0), F(1), F(2), F(3)); }
    else if (name == "ColorBalance") { NEED(1); o = clone(I[0]); o->ColorBalance(sVector30(F(0), F(1), F(2)), sVector30(F(3), F(4), F(5)), sVector30(F(6), F(7), F(8))); }
    else if (name == "Transform") {
      NEED(1);
      int sx = N(6) ? 1 << (N(6) - 1) : I[0]->XSize, sy = N(7) ? 1 << (N(7) - 1) : I[0]->YSize;
      o = new GenBitmap; o->Init(sx, sy);
      o->Rotate(I[0], 0.5f, 0.5f, F(0), F(1), F(2), F(3), F(4), N(5));
    }
    else if (name == "TransformMul") { NEED(1); o = clone(I[0]); o->RotateMul(0.5f, 0.5f, F(0), F(1), F(2), F(3), F(4), N(5), U(6), N(7), N(8), U(9)); }
    else if (name == "Twirl") { NEED(1); o = new GenBitmap; o->InitSize(I[0]); o->Twirl(I[0], F(0), F(1), F(2), F(3), F(4), F(5), N(6)); }
    else if (name == "Distort") { NEED(2); o = new GenBitmap; o->InitSize(I[0]); o->Distort(I[0], I[1], F(0), N(1)); }
    else if (name == "Normals") { NEED(1); o = new GenBitmap; o->InitSize(I[0]); o->Normals(I[0], F(0), N(1)); }
    else if (name == "Light") { NEED(1); o = clone(I[0]); o->Bump(0, N(0), F(1), F(2), F(3), F(4), F(5), U(6), U(7), F(8), F(9), F(10), U(7), 0, 0); }
    else if (name == "Bump") {
      NEED(2);
      if (I[0]->Size != I[1]->Size) { fprintf(stderr, "%s: bump of different sizes\n", id.c_str()); return 6; }
      o = clone(I[0]); o->Bump(I[1], N(0), F(1), F(2), F(3), F(4), F(5), U(6), U(7), F(8), F(9), F(10), U(11), F(12), F(13));
    }
    else if (name == "Unwrap") { NEED(1); o = new GenBitmap; o->InitSize(I[0]); o->Unwrap(I[0], N(0)); }
    else if (name == "Bulge") { NEED(1); o = new GenBitmap; o->InitSize(I[0]); o->Bulge(I[0], F(0)); }
    else if (name == "Paste") { NEED(2); o = Bitmap_Paste(clone(I[0]), I[1], F(0), F(1), F(2), F(3), F(4), F(5), F(6), N(7)); }
    else if (name == "Format" || name == "Text" || name == "Pass") { NEED(1); o = clone(I[0]); }   // Text needs Windows fonts: left out, said in the output
    else { fprintf(stderr, "%s: operator %s is not known here\n", id.c_str(), name.c_str()); return 7; }
    if (!o) { fprintf(stderr, "%s %s gave nothing\n", id.c_str(), name.c_str()); return 8; }
    v[id] = o;
  }
  fprintf(stderr, "no out line\n");
  return 2;
}
