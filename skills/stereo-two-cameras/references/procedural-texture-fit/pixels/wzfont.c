/* The font renderer under werkkzeug's Text operator.
 *
 * werkkzeug3 drew text with Windows GDI (sSystem_::FontBegin, FontPrint, FontWidth, FontCharWidth in
 * fr_public/werkkzeug3/_start.cpp). This file gives the same calls on FreeType, reading the font's own
 * outlines and nothing else: no bitmap strike, no hinting program, no pre-rendered glyph.
 *
 * What is followed, and where it is written:
 * - A glyph's outline is the font's 'glyf' data (TrueType outlines, quadratic curves: OpenType 1.9.1,
 *   "glyf - Glyph Data") or its CFF charstring (cubic curves: "CFF - Compact Font Format table").
 *   FreeType hands both over as one outline of lines, conic and cubic arcs (FreeType Glyph Conventions,
 *   VI, "FreeType Outlines"); it is filled by the non-zero winding rule, as TrueType asks.
 * - The character to glyph step is the font's 'cmap' table; a character with no entry gets glyph 0,
 *   ".notdef" ("cmap", "Use of the missing glyph"), and that is noted, never hidden.
 * - CreateFont(-h, w, ...) asks for an em square h pixels high: the scale is h / unitsPerEm ("head").
 *   The line's top and height are GDI's tmAscent and tmHeight, which come from usWinAscent and
 *   usWinDescent ("OS/2"); the advance of a glyph is advanceWidth ("hmtx"), rounded to whole pixels.
 *   A width w other than 0 asks for that average character width: the outlines are stretched sideways
 *   by w over the natural average (xAvgCharWidth, "OS/2").
 * - ExtTextOut with the default alignment puts the top left of the first character cell at (x, y);
 *   GDI adds no kerning there, and neither does this file.
 * - The 8-bit text is Windows code page 1252, the ANSI code page of a western Windows.
 *
 * Which font file stands for a name is never chosen here: it is read from a font map the person gives
 * (WZ_FONTMAP), and every font used is noted with the map's own sentence for the caption.
 */
#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_OUTLINE_H
#include FT_TRUETYPE_TABLES_H
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAXMAP 16
#define NOTES 4096

struct entry { char name[64]; char file[512]; char label[200]; FT_Face face; int tried; };
static struct entry g_map[MAXMAP];
static int g_nmap = 0, g_map_loaded = 0;
static char g_map_err[300];
static FT_Library g_lib;
static char g_notes[NOTES];

static FT_Face g_face;
static double g_sx, g_sy;            /* pixels per font unit, across and down */
static int g_ascent, g_height;       /* GDI's tmAscent and tmHeight, in pixels */
static double g_avg;                 /* the font's average character width, in font units */
static unsigned char *g_page;
static int g_px, g_py;
static const char *g_label = "";
static int g_quiet = 0;             /* the fitter's reading looks at glyphs without drawing a text: nothing to note */

/* Windows-1252 bytes 0x80 to 0x9f; every other byte is the same number in Unicode */
static const unsigned short cp1252_high[32] = {
  0x20AC, 0x0081, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, 0x02C6, 0x2030, 0x0160, 0x2039, 0x0152, 0x008D, 0x017D, 0x008F,
  0x0090, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x02DC, 0x2122, 0x0161, 0x203A, 0x0153, 0x009D, 0x017E, 0x0178 };

static unsigned unicode_of(unsigned char c) { return (c >= 0x80 && c <= 0x9f) ? cp1252_high[c - 0x80] : c; }

static void note(const char *fmt, ...)
{
  char line[400];
  va_list ap;
  if (g_quiet) return;
  va_start(ap, fmt);
  vsnprintf(line, sizeof line, fmt, ap);
  va_end(ap);
  size_t n = strlen(g_notes), m = strlen(line);
  /* every sentence once */
  const char *p = g_notes;
  while (*p) {
    const char *e = strchr(p, '\n');
    if (!e) break;
    if ((size_t) (e - p) == m && memcmp(p, line, m) == 0) return;
    p = e + 1;
  }
  if (n + m + 2 < NOTES) { memcpy(g_notes + n, line, m); g_notes[n + m] = '\n'; g_notes[n + m + 1] = 0; }
}

const char *hf_notes(void) { return g_notes; }
void hf_notes_clear(void) { g_notes[0] = 0; }

static char *trim(char *s)
{
  while (*s == ' ' || *s == '\t') s++;
  char *e = s + strlen(s);
  while (e > s && (e[-1] == ' ' || e[-1] == '\t' || e[-1] == '\r' || e[-1] == '\n')) *--e = 0;
  return s;
}

/* The font map: one line per name,  name = file | the sentence for the caption.  The file is taken
 * relative to the map's own folder. Lines starting with # are notes. */
static void map_load(void)
{
  g_map_loaded = 1;
  const char *path = getenv("WZ_FONTMAP");
  if (!path || !path[0]) { snprintf(g_map_err, sizeof g_map_err, "no font map is given: set WZ_FONTMAP to a file of lines  name = font file | sentence for the caption"); return; }
  FILE *f = fopen(path, "r");
  if (!f) { snprintf(g_map_err, sizeof g_map_err, "the font map %.200s cannot be read", path); return; }
  char dir[512];
  snprintf(dir, sizeof dir, "%s", path);
  char *sl = strrchr(dir, '/');
  if (sl) sl[1] = 0; else dir[0] = 0;
  char line[900];
  while (fgets(line, sizeof line, f)) {
    char *s = trim(line);
    if (!*s || *s == '#') continue;
    char *eq = strchr(s, '='), *bar = eq ? strchr(eq, '|') : 0;
    if (!eq || !bar) { snprintf(g_map_err, sizeof g_map_err, "the font map has a line that is not  name = file | sentence: %.150s", s); break; }
    *eq = 0; *bar = 0;
    if (g_nmap >= MAXMAP) { snprintf(g_map_err, sizeof g_map_err, "the font map has more than %d names", MAXMAP); break; }
    struct entry *e = &g_map[g_nmap];
    memset(e, 0, sizeof *e);
    char *nm = trim(s), *fl = trim(eq + 1), *lb = trim(bar + 1);
    for (size_t i = 0; nm[i] && i < sizeof e->name - 1; i++) e->name[i] = (char) tolower((unsigned char) nm[i]);
    if (fl[0] == '/') snprintf(e->file, sizeof e->file, "%s", fl);
    else snprintf(e->file, sizeof e->file, "%s%s", dir, fl);
    snprintf(e->label, sizeof e->label, "%s", lb);
    if (!e->name[0] || !fl[0] || !lb[0]) { snprintf(g_map_err, sizeof g_map_err, "the font map needs a name, a file and a sentence on every line: %.120s", nm); break; }
    g_nmap++;
  }
  fclose(f);
}

/* werkkzeug3's FontBegin: a page of pagex by pagey, the font by its Windows name, the average character
 * width (0: the font's own) and the height of the em square, both in page pixels.
 * Returns the line height (GDI's tmHeight), or -1 and a sentence in err. */
int hf_begin(int pagex, int pagey, const char *name, int avgw, int emh, char *err, int errlen)
{
  if (!g_map_loaded) map_load();
  if (g_map_err[0]) { snprintf(err, errlen, "%s", g_map_err); return -1; }
  char want[64];
  /* werkkzeug3, _start.cpp, FontBegin: if(name[0]==0) name = "arial"; */
  if (!name || !name[0]) name = "arial";
  size_t i = 0;
  for (; name[i] && i < sizeof want - 1; i++) want[i] = (char) tolower((unsigned char) name[i]);
  want[i] = 0;
  struct entry *e = 0;
  for (int k = 0; k < g_nmap; k++) if (strcmp(g_map[k].name, want) == 0) e = &g_map[k];
  if (!e) { snprintf(err, errlen, "the text asks for the font \"%s\" and the font map has no line for it", want); return -1; }
  if (!e->tried) {
    e->tried = 1;
    if (!g_lib && FT_Init_FreeType(&g_lib)) { snprintf(err, errlen, "FreeType did not start"); return -1; }
    if (FT_New_Face(g_lib, e->file, 0, &e->face)) e->face = 0;
  }
  if (!e->face) { snprintf(err, errlen, "the font file for \"%s\" cannot be read as a font: %.200s", want, e->file); return -1; }
  if (!FT_IS_SCALABLE(e->face)) { snprintf(err, errlen, "the font file for \"%s\" has no outlines (a bitmap font is not drawn): %.200s", want, e->file); return -1; }
  if (emh < 1) { snprintf(err, errlen, "the text's height is less than one pixel"); return -1; }
  if (pagex < 1 || pagey < 1 || (long long) pagex * pagey > (1LL << 28)) { snprintf(err, errlen, "a text page of %d by %d is outside what this module draws", pagex, pagey); return -1; }
  g_face = e->face;
  g_label = e->label;
  double upem = g_face->units_per_EM;
  g_sy = emh / upem;
  g_sx = g_sy;
  TT_OS2 *os2 = (TT_OS2 *) FT_Get_Sfnt_Table(g_face, FT_SFNT_OS2);
  double asc, desc, avg = 0;
  if (os2 && (os2->usWinAscent || os2->usWinDescent)) {
    asc = os2->usWinAscent; desc = os2->usWinDescent; avg = os2->xAvgCharWidth;
    /* "OS/2", xAvgCharWidth: up to version 2 of the table it is the weighted average of the lower-case letters
     * and the space; from version 3 on it is the plain average of every glyph, a much larger number (Arial 2.82
     * states 904, Liberation Sans 2.1.5 states 1187 for the same letter widths). The fonts werkkzeug3's artists
     * had used the older rule, so a newer font's average is worked out by that rule from its own advances:
     * then a font with the same advances gives the same stretch. */
    if (os2->version >= 3) {
      static const char *lc = "abcdefghijklmnopqrstuvwxyz ";
      static const int wt[27] = { 64, 14, 27, 35, 100, 20, 14, 42, 63, 3, 6, 35, 20, 56, 56, 17, 4, 49, 56, 71, 31, 10, 18, 3, 18, 2, 166 };
      long sum = 0; int ok = 1;
      for (int k = 0; k < 27; k++) {
        unsigned gi = FT_Get_Char_Index(g_face, (unsigned char) lc[k]);
        if (!gi || FT_Load_Glyph(g_face, gi, FT_LOAD_NO_SCALE | FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP)) { ok = 0; break; }
        sum += (long) g_face->glyph->metrics.horiAdvance * wt[k];
      }
      if (ok) avg = (double) (sum / 1000);
    }
  }
  else { asc = g_face->ascender; desc = -g_face->descender; note("%s: the font has no OS/2 table, the line height is taken from hhea", e->label); }
  g_avg = avg;
  g_ascent = (int) floor(asc * g_sy + 0.5);
  g_height = g_ascent + (int) floor(desc * g_sy + 0.5);
  if (avgw > 0) {
    if (avg <= 0) { snprintf(err, errlen, "the text sets a character width and the font \"%s\" states no average width (OS/2 xAvgCharWidth)", want); return -1; }
    g_sx = avgw / avg;
  }
  free(g_page);
  g_page = (unsigned char *) calloc((size_t) pagex, (size_t) pagey);
  if (!g_page) { snprintf(err, errlen, "no memory for a text page of %d by %d", pagex, pagey); return -1; }
  g_px = pagex; g_py = pagey;
  note("%s", e->label);
  return g_height;
}

static unsigned glyph_of(unsigned char c)
{
  unsigned u = unicode_of(c);
  unsigned gi = FT_Get_Char_Index(g_face, u);
  if (gi == 0) note("%s: no glyph for character 0x%02x, the font's missing-glyph shape (.notdef) is drawn as Windows does", g_label, c);
  return gi;
}

static int load(unsigned gi)
{
  return FT_Load_Glyph(g_face, gi, FT_LOAD_NO_SCALE | FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP) == 0 && g_face->glyph->format == FT_GLYPH_FORMAT_OUTLINE;
}

static int advance_of(unsigned gi)
{
  if (!load(gi)) return 0;
  return (int) floor(g_face->glyph->metrics.horiAdvance * g_sx + 0.5);
}

/* GDI's GetTextExtentPoint32: the sum of the advances */
int hf_width(const unsigned char *s, int len)
{
  int w = 0;
  if (!g_face) return 0;
  for (int i = 0; i < len; i++) w += advance_of(glyph_of(s[i]));
  return w;
}

/* GDI's GetCharABCWidths: the space before the ink, the ink's width, the space after it */
void hf_abc(int ch, int *abc)
{
  abc[0] = abc[1] = abc[2] = 0;
  if (!g_face) return;
  unsigned gi = glyph_of((unsigned char) ch);
  if (!load(gi)) return;
  int adv = (int) floor(g_face->glyph->metrics.horiAdvance * g_sx + 0.5);
  FT_BBox b;
  FT_Outline_Get_CBox(&g_face->glyph->outline, &b);
  int a = (int) floor(b.xMin * g_sx), r = (int) ceil(b.xMax * g_sx);
  if (g_face->glyph->outline.n_points == 0) { a = 0; r = 0; }
  abc[0] = a; abc[1] = r - a; abc[2] = adv - r;
}

static void spans(int y, int count, const FT_Span *sp, void *user)
{
  (void) user;
  int row = g_py - 1 - y;          /* the rasteriser counts rows upward from the page's bottom */
  if (row < 0 || row >= g_py) return;
  unsigned char *p = g_page + (size_t) row * g_px;
  for (int i = 0; i < count; i++) {
    int x0 = sp[i].x, x1 = x0 + sp[i].len;
    if (x0 < 0) x0 = 0;
    if (x1 > g_px) x1 = g_px;
    for (int x = x0; x < x1; x++) if (p[x] < sp[i].coverage) p[x] = sp[i].coverage;
  }
}

/* GDI's ExtTextOut with the default alignment: (x, y) is the top left of the first character cell */
void hf_print(int x, int y, const unsigned char *s, int len)
{
  if (!g_face || !g_page) return;
  int pen = x;
  for (int i = 0; i < len; i++) {
    unsigned gi = glyph_of(s[i]);
    if (!load(gi)) continue;
    int adv = (int) floor(g_face->glyph->metrics.horiAdvance * g_sx + 0.5);
    FT_Outline *o = &g_face->glyph->outline;
    if (o->n_points > 0) {
      FT_Matrix m;
      m.xx = (FT_Fixed) floor(g_sx * 64.0 * 65536.0 + 0.5); m.xy = 0; m.yx = 0;
      m.yy = (FT_Fixed) floor(g_sy * 64.0 * 65536.0 + 0.5);
      FT_Outline_Transform(o, &m);
      FT_Outline_Translate(o, (FT_Pos) pen * 64, (FT_Pos) (g_py - (y + g_ascent)) * 64);
      FT_Raster_Params rp;
      memset(&rp, 0, sizeof rp);
      rp.flags = FT_RASTER_FLAG_AA | FT_RASTER_FLAG_DIRECT | FT_RASTER_FLAG_CLIP;
      rp.gray_spans = spans;
      rp.clip_box.xMin = 0; rp.clip_box.yMin = 0; rp.clip_box.xMax = g_px; rp.clip_box.yMax = g_py;
      FT_Outline_Render(g_lib, o, &rp);
    }
    pen += adv;
  }
}

const unsigned char *hf_page(void) { return g_page; }
int hf_page_x(void) { return g_px; }
int hf_page_y(void) { return g_py; }

void hf_end(void)
{
  free(g_page);
  g_page = 0; g_px = g_py = 0; g_face = 0;
}

/* One glyph's ink as a small picture, for the fitter's reading: the glyph of character c of the named
 * font, its ink box stretched to fill side by side pixels (so the picture says the shape and v[] says the size).
 * v[0] the ink's width over its height, v[1] the ink's height, v[2] the ink's top below the line's top,
 * v[3] the advance, v[4] the ink's left edge after the pen, v[5] the font's average character width: all in em squares.
 * Returns 0; 2 when the glyph has no ink (a space: v[3] and v[5] are set); 1 when the font or the glyph is missing. */
int hf_glyph_mask(const char *name, int c, int side, unsigned char *out, float *v, char *err, int errlen)
{
  int em = 2048;
  g_quiet = 1;
  int r0 = hf_begin(1, 1, name, 0, em, err, errlen);
  g_quiet = 0;
  if (r0 < 0) return 1;
  double upem = g_face->units_per_EM;
  unsigned u = unicode_of((unsigned char) c);
  unsigned gi = FT_Get_Char_Index(g_face, u);
  if (gi == 0 || !load(gi)) { hf_end(); return 1; }
  v[3] = (float) (floor(g_face->glyph->metrics.horiAdvance * g_sx + 0.5) / em);
  v[5] = (float) (g_avg / upem);
  FT_Outline *o = &g_face->glyph->outline;
  if (o->n_points == 0) { hf_end(); return 2; }
  FT_BBox b;
  FT_Outline_Get_CBox(o, &b);
  double w = (b.xMax - b.xMin), h = (b.yMax - b.yMin);
  if (w <= 0 || h <= 0) { hf_end(); return 2; }
  v[0] = (float) (w / h);
  v[1] = (float) (h / upem);
  v[2] = (float) ((g_ascent / (double) em) - b.yMax / upem);
  v[4] = (float) (b.xMin / upem);
  FT_Matrix m;
  m.xx = (FT_Fixed) floor(side / w * 64.0 * 65536.0 + 0.5); m.xy = 0; m.yx = 0;
  m.yy = (FT_Fixed) floor(side / h * 64.0 * 65536.0 + 0.5);
  FT_Outline_Transform(o, &m);
  FT_Outline_Get_CBox(o, &b);
  FT_Outline_Translate(o, -b.xMin, -b.yMin);
  free(g_page);
  g_page = (unsigned char *) calloc((size_t) side, (size_t) side);
  g_px = g_py = side;
  FT_Raster_Params rp;
  memset(&rp, 0, sizeof rp);
  rp.flags = FT_RASTER_FLAG_AA | FT_RASTER_FLAG_DIRECT | FT_RASTER_FLAG_CLIP;
  rp.gray_spans = spans;
  rp.clip_box.xMax = side; rp.clip_box.yMax = side;
  FT_Outline_Render(g_lib, o, &rp);
  memcpy(out, g_page, (size_t) side * side);
  hf_end();
  return 0;
}
