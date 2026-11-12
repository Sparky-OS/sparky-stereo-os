// A stand-in for altona's sFont2D and its 2D page (base/windows.hpp), only what GenBitmap::Text uses.
// The font is drawn by wzfont.c on FreeType from the font's own outlines. One difference from altona's
// Windows code is meant: the size is the height of the em square, as werkkzeug3's own FontBegin asked
// Windows for it (CreateFont(-ys, xs, ...)), because the graphs drawn here are werkkzeug3's.
#ifndef SHIM_FONT2D_HPP
#define SHIM_FONT2D_HPP
#include "base/types.hpp"
extern "C" {
int hf_begin(int pagex, int pagey, const char *name, int avgw, int emh, char *err, int errlen);
int hf_width(const unsigned char *s, int len);
void hf_abc(int ch, int *abc);
void hf_print(int x, int y, const unsigned char *s, int len);
const unsigned char *hf_page(void);
void hf_end(void);
const char *hf_notes(void);
void hf_notes_clear(void);
int hf_glyph_mask(const char *name, int c, int side, unsigned char *out, float *v, char *err, int errlen);
}
enum { sF2C_ITALICS = 1, sF2C_BOLD = 2, sF2C_SYMBOLS = 0x20 };
enum { sGC_BLACK = 1, sGC_MAX = 16 };
static sInt g_f2d_x, g_f2d_y;        // the page GenBitmap::Text asked for
static char g_f2d_err[300];          // why the text could not be drawn; empty when it was
inline void sRender2DBegin(sInt xs, sInt ys) { g_f2d_x = xs; g_f2d_y = ys; g_f2d_err[0] = 0; }
inline void sRect2D(sInt, sInt, sInt, sInt, sInt) {}
inline void sSetColor2D(sInt, sU32) {}
inline void sRender2DGet(sU32 *data)
{
  const unsigned char *p = hf_page();
  for (sInt i = 0; i < g_f2d_x * g_f2d_y; i++) { sU32 v = p ? p[i] : 0; data[i] = v | (v << 8) | (v << 16); }
}
inline void sRender2DEnd() { hf_end(); }
// the text is 8-bit, Windows code page 1252; the bridge hands each byte over as one sChar
inline void f2d_narrow(const sChar *t, sInt len, unsigned char *out) { for (sInt i = 0; i < len; i++) out[i] = (unsigned char) t[i]; }
class sFont2D
{
  sInt Height;
public:
  sFont2D(const sChar *name, sInt size, sInt flags, sInt width = 0)
  {
    char nm[64]; sInt i = 0;
    for (; name && name[i] && i < 63; i++) nm[i] = (char) name[i];
    nm[i] = 0;
    Height = 0;
    if (flags) { snprintf(g_f2d_err, sizeof g_f2d_err, "bold, italics and symbols are werkkzeug4's; werkkzeug3's Text has none and this module does not draw them"); return; }
    Height = hf_begin(g_f2d_x, g_f2d_y, nm, width, size, g_f2d_err, sizeof g_f2d_err);
    if (Height < 0) Height = 0;
  }
  sInt GetHeight() { return Height; }
  void SetColor(sInt, sInt) {}
  sInt GetWidth(const sChar *text, sInt len)
  {
    if (g_f2d_err[0] || len <= 0) return 0;
    unsigned char *b = new unsigned char[len]; f2d_narrow(text, len, b);
    sInt w = hf_width(b, len); delete[] b; return w;
  }
  void Print(sInt, sInt x, sInt y, const sChar *text, sInt len)
  {
    if (g_f2d_err[0] || len <= 0) return;
    unsigned char *b = new unsigned char[len]; f2d_narrow(text, len, b);
    hf_print(x, y, b, len); delete[] b;
  }
};
#endif
