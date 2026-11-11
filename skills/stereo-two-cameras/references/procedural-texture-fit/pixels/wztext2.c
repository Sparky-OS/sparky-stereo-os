/* werkkzeug's Text, version 2: any font file, any character. Our extension of the operator (ORDER 508, milestone 1e).
 *
 * Version 1 is werkkzeug3's own Text (wzfont.c, 8-bit strings, Windows names, drawn exactly as werkkzeug3 drew
 * them). Version 2 keeps its geometry (the em square's height, the line's top at the font's Windows ascent, the
 * space around letters, the centring flags, the line skip) and adds:
 * - the text is UTF-8: any Unicode scalar value;
 * - the font is an entry of the font index (WZ_FONTINDEX), so any font file FreeType opens: TrueType outlines
 *   ('glyf', quadratic), CFF and CFF2 (cubic), Type 1, CID, Type 42, PFR, PCF, BDF, Windows FNT, and the
 *   WOFF and WOFF2 wrappers (OpenType 1.9.1 "OpenType font file"; FreeType's driver list);
 * - variable fonts: the operator's axis values ('fvar' axes, 'gvar'/'CFF2' deltas, 'avar' mapping) set the
 *   instance, through FreeType for the outlines and HarfBuzz for shaping, painting and metrics;
 * - colour: 'COLR' version 0 layers and version 1 paint graphs with 'CPAL' palettes, and the colour bitmaps
 *   of 'CBDT'/'CBLC' and 'sbix', painted by HarfBuzz's raster library; 'SVG ' glyphs drawn by plutosvg
 *   through FreeType's SVG hooks; embedded bitmap strikes ('EBDT'/'EBLC', PCF, BDF) as the font holds them;
 * - shaping by HarfBuzz (GSUB, GPOS, and the shapers for Arabic, Indic, Thai and the other complex scripts),
 *   in runs split by the Unicode Bidirectional Algorithm (UAX #9, SheenBidi) and by script (UAX #24).
 * Each glyph is drawn from what the font itself holds; which form was drawn, a substituted font, a missing
 * glyph and a refused form are said in the notes, never hidden.
 */
#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_OUTLINE_H
#include FT_TRUETYPE_TABLES_H
#include FT_TRUETYPE_TAGS_H
#include FT_MULTIPLE_MASTERS_H
#include FT_MODULE_H
#include FT_BITMAP_H
#include FT_SFNT_NAMES_H
#include <hb.h>
#include <hb-ft.h>
#include <hb-ot.h>
#include <hb-raster.h>
#include <SheenBidi/SheenBidi.h>
#include <math.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

const void *plutosvg_ft_svg_hooks(void);
void hf_note_line(const char *line);   /* wzfont.c: the one list of notes the render and the fit print */

enum { FORM_AUTO = 0, FORM_OUTLINE = 1, FORM_COLR = 2, FORM_SVG = 3, FORM_PNG = 4, FORM_STRIKE = 5 };
static const char *form_name[] = { "auto", "outline", "COLR", "SVG", "colour bitmap (CBDT or sbix)", "bitmap strike" };

static void note2(const char *fmt, ...)
{
  char line[600];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(line, sizeof line, fmt, ap);
  va_end(ap);
  hf_note_line(line);
}

/* ------------------------------------------------------------------ the font index */

struct ixent { char *key, *file, *source, *family, *style, *version, *label; int face; };
static struct ixent *g_ix;
static int g_nix, g_ix_loaded;
static char g_ix_err[300];

static char *field(char **p)
{
  char *s = *p, *t = strchr(s, '\t');
  if (t) { *t = 0; *p = t + 1; }
  else { char *e = s + strlen(s); while (e > s && (e[-1] == '\n' || e[-1] == '\r')) *--e = 0; *p = e; }
  return s;
}

static int ixcmp(const void *a, const void *b) { return strcmp(((const struct ixent *) a)->key, ((const struct ixent *) b)->key); }

/* The index is a table of tab-separated columns with a header line; the columns read here are
 * key, file, face, source, family, style, version (the first seven, in that order). */
static void ix_load(void)
{
  g_ix_loaded = 1;
  const char *path = getenv("WZ_FONTINDEX");
  if (!path || !path[0]) { snprintf(g_ix_err, sizeof g_ix_err, "no font index is given: set WZ_FONTINDEX to the index file (p2p fontindex)"); return; }
  FILE *f = fopen(path, "r");
  if (!f) { snprintf(g_ix_err, sizeof g_ix_err, "the font index %.200s cannot be read", path); return; }
  char *line = malloc(1 << 16);
  int cap = 0, first = 1;
  while (fgets(line, 1 << 16, f)) {
    if (first) { first = 0; if (strncmp(line, "key\t", 4) == 0) continue; }
    char *p = line;
    struct ixent e;
    e.key = strdup(field(&p)); e.file = strdup(field(&p)); e.face = atoi(field(&p));
    e.source = strdup(field(&p)); e.family = strdup(field(&p)); e.style = strdup(field(&p)); e.version = strdup(field(&p));
    char lb[400], ver[120];
    /* the version as the font says it, up to its first semicolon (the rest is build tools' remarks) */
    snprintf(ver, sizeof ver, "%s", e.version);
    char *semi = strchr(ver, ';');
    if (semi) *semi = 0;
    snprintf(lb, sizeof lb, "%s %s %s (%s)", e.family, e.style, ver, e.source);
    e.label = strdup(lb);
    if (g_nix >= cap) { cap = cap ? 2 * cap : 4096; g_ix = realloc(g_ix, (size_t) cap * sizeof *g_ix); }
    g_ix[g_nix++] = e;
  }
  free(line);
  fclose(f);
  qsort(g_ix, (size_t) g_nix, sizeof *g_ix, ixcmp);
}

static struct ixent *ix_find(const char *key)
{
  if (!g_ix_loaded) ix_load();
  if (!g_nix) return 0;
  struct ixent k; k.key = (char *) key;
  return bsearch(&k, g_ix, (size_t) g_nix, sizeof *g_ix, ixcmp);
}

const char *ix_error(void) { if (!g_ix_loaded) ix_load(); return g_ix_err; }

static int is_regular(const char *s)
{
  return !strcasecmp(s, "Regular") || !strcasecmp(s, "Normal") || !strcasecmp(s, "Book") || !strcasecmp(s, "Roman") || !strcasecmp(s, "Plain");
}

/* A family name as a person installed it: the regular face of that family, the machine's own copy first. */
int ix_resolve_family(const char *name, char *file, int filelen, int *face, char *label, int labellen)
{
  if (!g_ix_loaded) ix_load();
  struct ixent *best = 0;
  int best_rank = 99;
  for (int i = 0; i < g_nix; i++) {
    struct ixent *e = &g_ix[i];
    if (strcasecmp(e->family, name) || !is_regular(e->style)) continue;
    int rank = !strcmp(e->source, "machine") ? 0 : 1;
    if (rank < best_rank) { best_rank = rank; best = e; }
  }
  if (!best) return 0;
  snprintf(file, filelen, "%s", best->file);
  *face = best->face;
  snprintf(label, labellen, "%s %s (%s)", best->family, best->version, best->source);
  return 1;
}

/* ------------------------------------------------------------------ faces */

static FT_Library g_lib2;
struct face2 {
  struct ixent *ix;
  FT_Face ft;
  hb_face_t *hbf;
  hb_font_t *hb;        /* OpenType functions on the font's own tables (sfnt), or FreeType's (other formats) */
  int sfnt, scalable, upem;
  int colr1, colr0, svg, png, strikes;
  FT_MM_Var *mm;
  unsigned long last;
};
#define NFACE 48
static struct face2 g_faces[NFACE];
static unsigned long g_tick;

static int lib2(char *err, int errlen)
{
  if (g_lib2) return 0;
  if (FT_Init_FreeType(&g_lib2)) { snprintf(err, errlen, "FreeType did not start"); return 1; }
  FT_Property_Set(g_lib2, "ot-svg", "svg-hooks", plutosvg_ft_svg_hooks());
  return 0;
}

static void face_close(struct face2 *f)
{
  if (f->hb) hb_font_destroy(f->hb);
  if (f->hbf) hb_face_destroy(f->hbf);
  if (f->mm) FT_Done_MM_Var(g_lib2, f->mm);
  if (f->ft) FT_Done_Face(f->ft);
  memset(f, 0, sizeof *f);
}

static struct face2 *face_open(const char *key, char *err, int errlen)
{
  if (lib2(err, errlen)) return 0;
  struct ixent *e = ix_find(key);
  if (!e) {
    if (g_ix_err[0]) snprintf(err, errlen, "%s", g_ix_err);
    else snprintf(err, errlen, "the text asks for the font \"%.120s\" and the font index has no entry of that name", key);
    return 0;
  }
  g_tick++;
  for (int i = 0; i < NFACE; i++) if (g_faces[i].ix == e) { g_faces[i].last = g_tick; return &g_faces[i]; }
  int v = 0;
  for (int i = 1; i < NFACE; i++) if (g_faces[i].last < g_faces[v].last) v = i;
  struct face2 *f = &g_faces[v];
  face_close(f);
  if (FT_New_Face(g_lib2, e->file, e->face, &f->ft)) { f->ft = 0; snprintf(err, errlen, "the font file of \"%.120s\" cannot be read as a font: %.200s", key, e->file); return 0; }
  f->ix = e;
  f->last = g_tick;
  f->sfnt = FT_IS_SFNT(f->ft);
  f->scalable = FT_IS_SCALABLE(f->ft);
  f->upem = f->ft->units_per_EM ? f->ft->units_per_EM : 1000;
  f->strikes = f->ft->num_fixed_sizes;
  if (FT_HAS_MULTIPLE_MASTERS(f->ft)) FT_Get_MM_Var(f->ft, &f->mm);
  if (f->sfnt) {
    f->hbf = hb_ft_face_create_referenced(f->ft);
    f->hb = hb_font_create(f->hbf);
    hb_font_set_scale(f->hb, f->upem, f->upem);
    f->colr1 = hb_ot_color_has_paint(f->hbf);
    f->colr0 = hb_ot_color_has_layers(f->hbf);
    f->svg = hb_ot_color_has_svg(f->hbf);
    f->png = hb_ot_color_has_png(f->hbf);
  } else {
    f->hb = hb_ft_font_create_referenced(f->ft);
    f->hbf = hb_face_reference(hb_font_get_face(f->hb));
  }
  return f;
}

/* The operator's axis values, "wght=650 wdth=90": every axis named must exist in the font and its value lie
 * in the axis's range ('fvar', VariationAxisRecord minValue..maxValue); the others keep their defaults. */
static int set_axes(struct face2 *f, const char *axes, char *err, int errlen)
{
  hb_variation_t vars[16];
  int nv = 0;
  const char *p = axes ? axes : "";
  while (*p) {
    while (*p == ' ' || *p == ',') p++;
    if (!*p) break;
    const char *q = p;
    while (*q && *q != ' ' && *q != ',') q++;
    char tok[64];
    size_t n = (size_t) (q - p);
    if (n >= sizeof tok) n = sizeof tok - 1;
    memcpy(tok, p, n); tok[n] = 0;
    if (nv >= 16 || !hb_variation_from_string(tok, -1, &vars[nv])) { snprintf(err, errlen, "the axis value \"%s\" is not tag=number", tok); return 1; }
    nv++;
    p = q;
  }
  if (nv && !f->mm) { snprintf(err, errlen, "the text sets axes and %s is not a variable font", f->ix->label); return 1; }
  if (f->mm) {
    FT_Fixed coords[64];
    unsigned na = f->mm->num_axis;
    if (na > 64) na = 64;
    for (unsigned a = 0; a < na; a++) coords[a] = f->mm->axis[a].def;
    for (int k = 0; k < nv; k++) {
      unsigned a = 0;
      for (; a < na; a++) if (f->mm->axis[a].tag == vars[k].tag) break;
      char tg[5]; hb_tag_to_string(vars[k].tag, tg); tg[4] = 0;
      if (a == na) { snprintf(err, errlen, "%s has no axis %s", f->ix->label, tg); return 1; }
      double v = vars[k].value, lo = f->mm->axis[a].minimum / 65536.0, hi = f->mm->axis[a].maximum / 65536.0;
      if (v < lo - 1e-6 || v > hi + 1e-6) { snprintf(err, errlen, "axis %s asks %g and %s has the range %g to %g", tg, v, f->ix->label, lo, hi); return 1; }
      coords[a] = (FT_Fixed) floor(v * 65536.0 + 0.5);
    }
    if (FT_Set_Var_Design_Coordinates(f->ft, na, coords)) { snprintf(err, errlen, "FreeType refused the axis values for %s", f->ix->label); return 1; }
  }
  hb_font_set_variations(f->hb, vars, (unsigned) nv);
  return 0;
}

/* ------------------------------------------------------------------ the page */

struct page {
  int w, h;               /* page pixels: the picture's size times the antialiasing factor */
  uint8_t *cov;           /* outline and strike coverage, the operator's colour */
  uint8_t *bgra;          /* colour glyphs, premultiplied */
};

static void spans_cov(int y, int count, const FT_Span *sp, void *user)
{
  struct page *pg = user;
  int row = pg->h - 1 - y;
  if (row < 0 || row >= pg->h) return;
  uint8_t *p = pg->cov + (size_t) row * pg->w;
  for (int i = 0; i < count; i++) {
    int x0 = sp[i].x, x1 = x0 + sp[i].len;
    if (x0 < 0) x0 = 0;
    if (x1 > pg->w) x1 = pg->w;
    for (int x = x0; x < x1; x++) if (p[x] < sp[i].coverage) p[x] = sp[i].coverage;
  }
}

/* a premultiplied BGRA picture laid over the colour page, its top left at (x0, y0) in page pixels; rows go down */
static void over_bgra(struct page *pg, int x0, int y0, int w, int h, int stride, const uint8_t *src)
{
  for (int j = 0; j < h; j++) {
    int y = y0 + j;
    if (y < 0 || y >= pg->h) continue;
    const uint8_t *s = src + (size_t) j * stride;
    uint8_t *d = pg->bgra + ((size_t) y * pg->w) * 4;
    for (int i = 0; i < w; i++) {
      int x = x0 + i;
      if (x < 0 || x >= pg->w) continue;
      unsigned a = s[4 * i + 3];
      if (!a) continue;
      for (int c = 0; c < 4; c++) d[4 * x + c] = (uint8_t) (s[4 * i + c] + (d[4 * x + c] * (255 - a) + 127) / 255);
    }
  }
}

/* ------------------------------------------------------------------ glyph forms */

static int glyph_has_colr(struct face2 *f, unsigned gid, int *v1)
{
  *v1 = 0;
  if (f->colr1 && hb_ot_color_glyph_has_paint(f->hbf, gid)) { *v1 = 1; return 1; }
  if (f->colr0 && hb_ot_color_glyph_get_layers(f->hbf, gid, 0, NULL, NULL) > 0) return 1;
  return 0;
}

static int glyph_has_svg(struct face2 *f, unsigned gid)
{
  if (!f->svg) return 0;
  hb_blob_t *b = hb_ot_color_glyph_reference_svg(f->hbf, gid);
  int r = hb_blob_get_length(b) > 0;
  hb_blob_destroy(b);
  return r;
}

static int glyph_has_png(struct face2 *f, unsigned gid)
{
  if (!f->png) return 0;
  hb_blob_t *b = hb_ot_color_glyph_reference_png(f->hb, gid);
  int r = hb_blob_get_length(b) > 0;
  hb_blob_destroy(b);
  return r;
}

static int glyph_has_outline(struct face2 *f, unsigned gid)
{
  if (!f->scalable) return 0;
  if (FT_Load_Glyph(f->ft, gid, FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP)) return 0;
  return f->ft->glyph->format == FT_GLYPH_FORMAT_OUTLINE;
}

/* the form a glyph is drawn in: the one asked for, or, when the operator says auto, the richest the font holds
 * for it: a COLR paint graph or layers, then an SVG document, then a colour bitmap, then the outline, then a strike */
static int choose_form(struct face2 *f, unsigned gid, int want, int *colr_v1)
{
  int v1 = 0;
  *colr_v1 = 0;
  if (want == FORM_AUTO) {
    if (glyph_has_colr(f, gid, &v1)) { *colr_v1 = v1; return FORM_COLR; }
    if (glyph_has_svg(f, gid)) return FORM_SVG;
    if (glyph_has_png(f, gid)) return FORM_PNG;
    if (glyph_has_outline(f, gid)) return FORM_OUTLINE;
    if (f->strikes) return FORM_STRIKE;
    return -1;
  }
  switch (want) {
  case FORM_COLR: if (glyph_has_colr(f, gid, &v1)) { *colr_v1 = v1; return want; } return -1;
  case FORM_SVG: return glyph_has_svg(f, gid) ? want : -1;
  case FORM_PNG: return glyph_has_png(f, gid) ? want : -1;
  case FORM_OUTLINE: return glyph_has_outline(f, gid) ? want : -1;
  case FORM_STRIKE: return f->strikes ? want : -1;
  }
  return -1;
}

struct metrics { double sx, sy; int em; int ascent, height; double avg; };

/* the same size rules as version 1 (wzfont.c): an em square em pixels high, stretched sideways by the
 * width asked over the font's average width, the line's top at the Windows ascent */
static int metrics_of(struct face2 *f, int emh, int avgw, struct metrics *m, char *err, int errlen)
{
  memset(m, 0, sizeof *m);
  m->em = emh;
  m->sy = (double) emh / f->upem;
  m->sx = m->sy;
  double asc, desc, avg = 0;
  TT_OS2 *os2 = (TT_OS2 *) FT_Get_Sfnt_Table(f->ft, FT_SFNT_OS2);
  if (os2 && (os2->usWinAscent || os2->usWinDescent)) {
    asc = os2->usWinAscent; desc = os2->usWinDescent; avg = os2->xAvgCharWidth;
    if (os2->version >= 3 && f->scalable) {
      static const char *lc = "abcdefghijklmnopqrstuvwxyz ";
      static const int wt[27] = { 64, 14, 27, 35, 100, 20, 14, 42, 63, 3, 6, 35, 20, 56, 56, 17, 4, 49, 56, 71, 31, 10, 18, 3, 18, 2, 166 };
      long sum = 0; int ok = 1;
      for (int k = 0; k < 27; k++) {
        unsigned gi = FT_Get_Char_Index(f->ft, (unsigned char) lc[k]);
        if (!gi || FT_Load_Glyph(f->ft, gi, FT_LOAD_NO_SCALE | FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP)) { ok = 0; break; }
        sum += (long) f->ft->glyph->metrics.horiAdvance * wt[k];
      }
      if (ok) avg = (double) (sum / 1000);
    }
  } else if (f->scalable) {
    asc = f->ft->ascender; desc = -f->ft->descender;
  } else {
    /* a bitmap font: its strike's own ascent and descent, in the strike's pixels, taken to the em asked for */
    int s = 0;
    for (int i = 1; i < f->ft->num_fixed_sizes; i++) if (f->ft->available_sizes[i].y_ppem > f->ft->available_sizes[s].y_ppem) s = i;
    FT_Select_Size(f->ft, s);
    double ppem = f->ft->available_sizes[s].y_ppem / 64.0;
    if (ppem <= 0) ppem = f->ft->available_sizes[s].height;
    asc = f->ft->size->metrics.ascender / 64.0 / ppem * f->upem;
    desc = -f->ft->size->metrics.descender / 64.0 / ppem * f->upem;
  }
  m->avg = avg;
  m->ascent = (int) floor(asc * m->sy + 0.5);
  m->height = m->ascent + (int) floor(desc * m->sy + 0.5);
  if (avgw > 0) {
    if (avg <= 0) { snprintf(err, errlen, "the text sets a character width and %s states no average width (OS/2 xAvgCharWidth)", f->ix->label); return 1; }
    m->sx = avgw / avg;
  }
  return 0;
}

/* ------------------------------------------------------------------ shaping: UAX #9 runs, UAX #24 scripts, HarfBuzz */

struct pg { unsigned gid; double x, y; unsigned cp; };   /* a glyph placed: pen origin in page pixels (y up from the baseline) */

static int utf8_valid(const char *s, int len)
{
  const unsigned char *p = (const unsigned char *) s, *e = p + len;
  while (p < e) {
    unsigned c = *p;
    int n = c < 0x80 ? 0 : (c >> 5) == 6 ? 1 : (c >> 4) == 14 ? 2 : (c >> 3) == 30 ? 3 : -1;
    if (n < 0 || p + 1 + n > e) return 0;
    unsigned cp = n == 0 ? c : n == 1 ? c & 0x1f : n == 2 ? c & 0x0f : c & 0x07;
    for (int i = 1; i <= n; i++) { if ((p[i] & 0xc0) != 0x80) return 0; cp = (cp << 6) | (p[i] & 0x3f); }
    if ((n == 1 && cp < 0x80) || (n == 2 && cp < 0x800) || (n == 3 && (cp < 0x10000 || cp > 0x10ffff)) || (cp >= 0xd800 && cp <= 0xdfff)) return 0;
    p += 1 + n;
  }
  return 1;
}

static unsigned cp_at(const char *s, unsigned off)
{
  const unsigned char *p = (const unsigned char *) s + off;
  unsigned c = p[0];
  if (c < 0x80) return c;
  if ((c >> 5) == 6) return ((c & 0x1f) << 6) | (p[1] & 0x3f);
  if ((c >> 4) == 14) return ((c & 0x0f) << 12) | ((p[1] & 0x3f) << 6) | (p[2] & 0x3f);
  return ((c & 0x07) << 18) | ((p[1] & 0x3f) << 12) | ((p[2] & 0x3f) << 6) | (p[3] & 0x3f);
}

/* Shape one line: its bidirectional runs in visual order (UAX #9, rules P2 and P3 for the base level, X1 to I2
 * for the levels, L2 for the order), each split by script (UAX #24 with its Common and Inherited resolution),
 * each piece shaped by HarfBuzz in its run's direction. Positions in font units times (sx, sy). */
static int shape_line(struct face2 *f, const char *s, int len, double sx, double sy, int bitmap_k64,
                      struct pg **out, int *nout, double *width, int *nruns_rtl, char *err, int errlen)
{
  *out = 0; *nout = 0; *width = 0; *nruns_rtl = 0;
  if (len == 0) return 0;
  SBCodepointSequence seq = { SBStringEncodingUTF8, s, (SBUInteger) len };
  SBAlgorithmRef alg = SBAlgorithmCreate(&seq);
  if (!alg) { snprintf(err, errlen, "the bidirectional algorithm did not start"); return 1; }
  SBParagraphRef para = SBAlgorithmCreateParagraph(alg, 0, (SBUInteger) len, SBLevelDefaultLTR);
  SBLineRef line = SBParagraphCreateLine(para, 0, (SBUInteger) len);
  SBUInteger nr = SBLineGetRunCount(line);
  const SBRun *runs = SBLineGetRunsPtr(line);
  /* the script runs of the whole line */
  struct srun { unsigned off, len; hb_script_t sc; } *sr = 0;
  int ns = 0, cs = 0;
  SBScriptLocatorRef loc = SBScriptLocatorCreate();
  SBScriptLocatorLoadCodepoints(loc, &seq);
  while (SBScriptLocatorMoveNext(loc)) {
    const SBScriptAgent *ag = SBScriptLocatorGetAgent(loc);
    if (ns >= cs) { cs = cs ? 2 * cs : 16; sr = realloc(sr, (size_t) cs * sizeof *sr); }
    sr[ns].off = (unsigned) ag->offset; sr[ns].len = (unsigned) ag->length;
    sr[ns].sc = hb_script_from_iso15924_tag((hb_tag_t) SBScriptGetUnicodeTag(ag->script));
    ns++;
  }
  SBScriptLocatorRelease(loc);
  int cap = 64, n = 0;
  struct pg *g = malloc((size_t) cap * sizeof *g);
  double pen = 0;
  hb_buffer_t *buf = hb_buffer_create();
  for (SBUInteger r = 0; r < nr; r++) {
    unsigned ro = (unsigned) runs[r].offset, rl = (unsigned) runs[r].length;
    int rtl = runs[r].level & 1;
    if (rtl) (*nruns_rtl)++;
    /* the pieces of this run, one per script; in a right-to-left run the last piece is drawn first */
    int idx[256], np = 0;
    for (int k = 0; k < ns && np < 256; k++) {
      unsigned a = sr[k].off > ro ? sr[k].off : ro, b = (sr[k].off + sr[k].len) < (ro + rl) ? sr[k].off + sr[k].len : ro + rl;
      if (a < b) idx[np++] = k;
    }
    for (int q = 0; q < np; q++) {
      int k = idx[rtl ? np - 1 - q : q];
      unsigned a = sr[k].off > ro ? sr[k].off : ro, b = (sr[k].off + sr[k].len) < (ro + rl) ? sr[k].off + sr[k].len : ro + rl;
      hb_buffer_clear_contents(buf);
      hb_buffer_add_utf8(buf, s, len, a, (int) (b - a));
      hb_buffer_set_direction(buf, rtl ? HB_DIRECTION_RTL : HB_DIRECTION_LTR);
      hb_buffer_set_script(buf, sr[k].sc);
      hb_buffer_set_language(buf, HB_LANGUAGE_INVALID);
      hb_buffer_set_cluster_level(buf, HB_BUFFER_CLUSTER_LEVEL_MONOTONE_CHARACTERS);
      hb_shape(f->hb, buf, NULL, 0);
      unsigned gn = 0;
      hb_glyph_info_t *gi = hb_buffer_get_glyph_infos(buf, &gn);
      hb_glyph_position_t *gp = hb_buffer_get_glyph_positions(buf, &gn);
      for (unsigned i = 0; i < gn; i++) {
        if (n >= cap) { cap *= 2; g = realloc(g, (size_t) cap * sizeof *g); }
        double kx = bitmap_k64 ? sx / 64.0 : sx, ky = bitmap_k64 ? sy / 64.0 : sy;
        g[n].gid = gi[i].codepoint;
        g[n].cp = cp_at(s, gi[i].cluster);
        if (getenv("WZ_TEXTDEBUG")) fprintf(stderr, "glyph %u for U+%04X at byte %u, level %d, script %c%c%c%c, x %.1f\n", gi[i].codepoint, g[n].cp, gi[i].cluster, runs[r].level,
                                           (char) (sr[k].sc >> 24), (char) (sr[k].sc >> 16), (char) (sr[k].sc >> 8), (char) sr[k].sc, pen + gp[i].x_offset * kx);
        g[n].x = pen + gp[i].x_offset * kx;
        g[n].y = gp[i].y_offset * ky;
        pen += gp[i].x_advance * kx;
        n++;
      }
    }
  }
  hb_buffer_destroy(buf);
  free(sr);
  SBLineRelease(line);
  SBParagraphRelease(para);
  SBAlgorithmRelease(alg);
  *out = g; *nout = n; *width = pen;
  return 0;
}

/* ------------------------------------------------------------------ drawing one glyph in its form */

static int draw_outline(struct face2 *f, struct page *pg, unsigned gid, const struct metrics *m, double px, double base_up)
{
  /* the outline at the em size in 26.6 pixels, unhinted, then stretched sideways and placed */
  if (FT_Set_Char_Size(f->ft, 0, (FT_F26Dot6) (m->em * 64), 72, 72)) return 1;
  if (FT_Load_Glyph(f->ft, gid, FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP) || f->ft->glyph->format != FT_GLYPH_FORMAT_OUTLINE) return 1;
  FT_Outline *o = &f->ft->glyph->outline;
  if (o->n_points == 0) return 0;
  double st = m->sx / m->sy;
  if (fabs(st - 1) > 1e-9) {
    FT_Matrix mt = { (FT_Fixed) floor(st * 65536.0 + 0.5), 0, 0, 0x10000 };
    FT_Outline_Transform(o, &mt);
  }
  FT_Outline_Translate(o, (FT_Pos) floor(px * 64 + 0.5), (FT_Pos) floor(base_up * 64 + 0.5));
  FT_Raster_Params rp;
  memset(&rp, 0, sizeof rp);
  rp.flags = FT_RASTER_FLAG_AA | FT_RASTER_FLAG_DIRECT | FT_RASTER_FLAG_CLIP;
  rp.gray_spans = spans_cov;
  rp.user = pg;
  rp.clip_box.xMax = pg->w; rp.clip_box.yMax = pg->h;
  FT_Outline_Render(g_lib2, o, &rp);
  return 0;
}

/* COLR layers and paint graphs, and CBDT and sbix pictures: HarfBuzz's raster library, glyph space mapped to
 * page pixels with y going down; the foreground colour is the operator's colour, the palette the operator's */
static int draw_paint(struct face2 *f, struct page *pg, unsigned gid, const struct metrics *m, double px, double base_down, unsigned col, int palette)
{
  hb_raster_paint_t *p = hb_raster_paint_create_or_fail();
  if (!p) return 1;
  hb_font_set_ppem(f->hb, (unsigned) m->em, (unsigned) m->em);
  double fx = px - floor(px), fy = base_down - floor(base_down);
  hb_raster_paint_set_transform(p, (float) m->sx, 0.f, 0.f, (float) -m->sy, (float) fx, (float) fy);
  hb_raster_paint_set_foreground(p, HB_COLOR(col & 255, (col >> 8) & 255, (col >> 16) & 255, (col >> 24) & 255));
  hb_raster_paint_set_palette(p, (unsigned) palette);
  hb_glyph_extents_t ge;
  int ok = 0;
  if (hb_font_get_glyph_extents(f->hb, gid, &ge) && hb_raster_paint_set_glyph_extents(p, &ge)) {
    if (hb_raster_paint_glyph_or_fail(p, f->hb, gid)) {
      hb_raster_image_t *img = hb_raster_paint_render(p);
      if (img) {
        hb_raster_extents_t ex;
        hb_raster_image_get_extents(img, &ex);
        over_bgra(pg, (int) floor(px) + ex.x_origin, (int) floor(base_down) + ex.y_origin, (int) ex.width, (int) ex.height, (int) ex.stride, hb_raster_image_get_buffer(img));
        hb_raster_image_destroy(img);
        ok = 1;
      }
    }
  } else ok = 1;   /* nothing to paint (a space) */
  hb_font_set_ppem(f->hb, 0, 0);
  hb_raster_paint_destroy(p);
  return ok ? 0 : 1;
}

/* SVG documents: FreeType's 'SVG ' module with plutosvg's hooks, at the em size, stretched sideways */
static int draw_svg(struct face2 *f, struct page *pg, unsigned gid, const struct metrics *m, double px, double base_down)
{
  if (FT_Set_Char_Size(f->ft, 0, (FT_F26Dot6) (m->em * 64), 72, 72)) return 1;
  double st = m->sx / m->sy, fx = px - floor(px);
  FT_Matrix mt = { (FT_Fixed) floor(st * 65536.0 + 0.5), 0, 0, 0x10000 };
  FT_Vector d = { (FT_Pos) floor(fx * 64 + 0.5), 0 };
  FT_Set_Transform(f->ft, &mt, &d);
  int r = 1;
  if (!FT_Load_Glyph(f->ft, gid, FT_LOAD_COLOR | FT_LOAD_NO_HINTING) && f->ft->glyph->format == FT_GLYPH_FORMAT_SVG &&
      !FT_Render_Glyph(f->ft->glyph, FT_RENDER_MODE_NORMAL) && f->ft->glyph->bitmap.pixel_mode == FT_PIXEL_MODE_BGRA) {
    FT_Bitmap *b = &f->ft->glyph->bitmap;
    over_bgra(pg, (int) floor(px) + f->ft->glyph->bitmap_left, (int) floor(base_down) - f->ft->glyph->bitmap_top, (int) b->width, (int) b->rows, b->pitch, b->buffer);
    r = 0;
  }
  FT_Set_Transform(f->ft, NULL, NULL);
  return r;
}

/* a bitmap strike, as the font holds it: the smallest strike at least as large as the em asked for (else the
 * largest), each of its pixels laid as a block of page pixels (nearest neighbour), so no pixel is invented */
static int pick_strike(struct face2 *f, int em, int *ppem_out)
{
  int s = -1, best = -1;
  for (int i = 0; i < f->ft->num_fixed_sizes; i++) {
    int ppem = (int) ((f->ft->available_sizes[i].y_ppem + 32) >> 6);
    if (!ppem) ppem = f->ft->available_sizes[i].height;
    if (ppem >= em && (s < 0 || ppem < best)) { s = i; best = ppem; }
  }
  if (s < 0) for (int i = 0; i < f->ft->num_fixed_sizes; i++) {
    int ppem = (int) ((f->ft->available_sizes[i].y_ppem + 32) >> 6);
    if (!ppem) ppem = f->ft->available_sizes[i].height;
    if (ppem > best) { s = i; best = ppem; }
  }
  *ppem_out = best;
  return s;
}

static int draw_strike(struct face2 *f, struct page *pg, unsigned gid, const struct metrics *m, double px, double base_down, int *strike_px)
{
  int best = 0, s = pick_strike(f, m->em, &best);
  if (s < 0 || FT_Select_Size(f->ft, s)) return 1;
  if (FT_Load_Glyph(f->ft, gid, FT_LOAD_DEFAULT | FT_LOAD_COLOR) || f->ft->glyph->format != FT_GLYPH_FORMAT_BITMAP) return 1;
  *strike_px = best;
  FT_Bitmap *b = &f->ft->glyph->bitmap;
  double k = (double) m->em / best, kx = k * m->sx / m->sy;
  int left = f->ft->glyph->bitmap_left, top = f->ft->glyph->bitmap_top;
  int x0 = (int) floor(px + left * kx), y0 = (int) floor(base_down - top * k);
  int w = (int) ceil(b->width * kx), h = (int) ceil(b->rows * k);
  for (int j = 0; j < h; j++) {
    int sy = (int) (j / k), y = y0 + j;
    if (sy >= (int) b->rows || y < 0 || y >= pg->h) continue;
    const uint8_t *row = b->buffer + (ptrdiff_t) sy * b->pitch;
    for (int i = 0; i < w; i++) {
      int sxp = (int) (i / kx), x = x0 + i;
      if (sxp >= (int) b->width || x < 0 || x >= pg->w) continue;
      if (b->pixel_mode == FT_PIXEL_MODE_BGRA) {
        over_bgra(pg, x, y, 1, 1, 4, row + 4 * sxp);
      } else {
        unsigned v = 0;
        if (b->pixel_mode == FT_PIXEL_MODE_MONO) v = (row[sxp >> 3] >> (7 - (sxp & 7))) & 1 ? 255 : 0;
        else if (b->pixel_mode == FT_PIXEL_MODE_GRAY) v = row[sxp] * 255u / (b->num_grays > 1 ? b->num_grays - 1 : 255);
        else if (b->pixel_mode == FT_PIXEL_MODE_GRAY2) v = ((row[sxp >> 2] >> (6 - 2 * (sxp & 3))) & 3) * 85;
        else if (b->pixel_mode == FT_PIXEL_MODE_GRAY4) v = ((row[sxp >> 1] >> (4 - 4 * (sxp & 1))) & 15) * 17;
        uint8_t *d = pg->cov + (size_t) y * pg->w + x;
        if (*d < v) *d = (uint8_t) v;
      }
    }
  }
  return 0;
}

/* ------------------------------------------------------------------ the operator */

/* Version 2 of werkkzeug's Text into a picture of XS by YS pixels: out is premultiplied BGRA, one byte per
 * channel (what lies over the input picture). x, y, emh, avgw, flags, extspace, lineskip as version 1;
 * text UTF-8; key the font index entry; axes "tag=value ..."; palette the CPAL palette; form 0 auto,
 * 1 outline, 2 COLR, 3 SVG, 4 colour bitmap, 5 bitmap strike; col the operator's colour (0xAARRGGBB). */
int ht2_draw(int XS, int YS, float x, float y, float emh, float avgw, unsigned flags, int extspace, float lineskip,
             const char *text, const char *key, const char *axes, int palette, int form, unsigned col,
             uint8_t *out, char *err, int errlen)
{
  const int alias = 4;
  int xs = XS * alias, ys = YS * alias;
  if (form < 0 || form > 5) { snprintf(err, errlen, "form %d is none of auto, outline, COLR, SVG, colour bitmap, bitmap strike (0 to 5)", form); return 1; }
  if (flags & ~0x3u) { snprintf(err, errlen, "flags 0x%x: version 2 draws plain text only (1 centre across, 2 centre down)", flags); return 1; }
  if (!(emh > 0) || emh > 64) { snprintf(err, errlen, "font height %g of the picture is outside what this module draws", emh); return 1; }
  if (avgw < 0 || avgw > 64) { snprintf(err, errlen, "character width %g of the picture is outside what this module draws", avgw); return 1; }
  if (extspace < 0 || extspace > 1024) { snprintf(err, errlen, "space %d around letters is outside 0..1024", extspace); return 1; }
  if ((long long) xs * ys > (1LL << 28)) { snprintf(err, errlen, "a text page of %d by %d is outside what this module draws", xs, ys); return 1; }
  int tl = (int) strlen(text);
  if (!utf8_valid(text, tl)) { snprintf(err, errlen, "the text of a version 2 Text is not valid UTF-8"); return 1; }
  struct face2 *f = face_open(key, err, errlen);
  if (!f) return 1;
  if (set_axes(f, axes, err, errlen)) return 1;
  /* CPAL: palette 0 is the default; another must exist in the font ("The first palette, palette index 0, is the
   * default palette"; the application chooses among the others) */
  if (palette < 0 || (palette > 0 && (unsigned) palette >= hb_ot_color_palette_get_count(f->hbf))) {
    snprintf(err, errlen, "palette %d is asked and %s has %u palette(s)", palette, f->ix->label, hb_ot_color_palette_get_count(f->hbf));
    return 1;
  }
  int es = extspace * alias + 2 * alias;
  int em_px = (int) (ys * emh), avg_px = (int) (xs * avgw);
  if (em_px < 1) { snprintf(err, errlen, "the text's height is less than one pixel"); return 1; }
  struct metrics m;
  if (metrics_of(f, em_px, avg_px, &m, err, errlen)) return 1;
  struct page pg = { xs, ys, calloc((size_t) xs, (size_t) ys), calloc((size_t) xs * ys, 4) };
  if (!pg.cov || !pg.bgra) { free(pg.cov); free(pg.bgra); snprintf(err, errlen, "no memory for a text page of %d by %d", xs, ys); return 1; }
  int xp = (int) ((x + (float) es / xs) * xs), yp = (int) ((y + (float) es / ys) * ys);
  int lsk = (int) (lineskip * m.height);
  int lf = 0;
  for (int i = 0; i < tl; i++) if (text[i] == '\n') lf++;
  if (flags & 2) yp -= m.height * (lf + 1) / 2;
  /* positions: for a font with outlines, font units times the scale; for a bitmap-only font, FreeType's
   * advances at the strike in 26.6 pixels times the strike's scale */
  double ksx = m.sx, ksy = m.sy;
  int k64 = 0, strike_sel = -1, strike_ppem = 0;
  if (!f->sfnt) {
    /* FreeType's functions behind HarfBuzz (Type 1, PCF, BDF and the other formats without OpenType tables) */
    k64 = 1;
    if (!f->scalable) {
      strike_sel = pick_strike(f, m.em, &strike_ppem);
      if (strike_sel < 0) { free(pg.cov); free(pg.bgra); snprintf(err, errlen, "%s has no bitmap strike to draw from", f->ix->label); return 1; }
      ksx = (double) m.em / strike_ppem * m.sx / m.sy; ksy = (double) m.em / strike_ppem;
    }
  }
  int counts[6] = { 0 }, colr_v1n = 0, missing = 0, refused = 0, rtl_runs = 0, strike_px = 0;
  char miss[300] = "", why[300] = "";
  const char *p = text;
  while (*p || p == text) {
    int i = 0;
    while (p[i] && p[i] != '\n') i++;
    if (i > 0) {
      struct pg *g; int n; double w; int nrtl;
      /* FreeType's functions behind a font of another format read the face's current size: set it before shaping */
      if (k64 && f->scalable) { FT_Set_Char_Size(f->ft, 0, (FT_F26Dot6) f->upem * 64, 72, 72); hb_ft_font_changed(f->hb); }
      if (k64 && !f->scalable) { FT_Select_Size(f->ft, strike_sel); hb_ft_font_changed(f->hb); }
      if (shape_line(f, p, i, ksx, ksy, k64, &g, &n, &w, &nrtl, err, errlen)) { free(pg.cov); free(pg.bgra); return 1; }
      rtl_runs += nrtl;
      double x0 = (flags & 1) ? xp - w / 2 : xp;
      double base_down = yp + m.ascent;
      for (int k = 0; k < n; k++) {
        int v1 = 0, fm = choose_form(f, g[k].gid, form, &v1);
        if (g[k].gid == 0) {
          missing++;
          size_t l = strlen(miss);
          if (l < sizeof miss - 12) snprintf(miss + l, sizeof miss - l, "%sU+%04X", l ? ", " : "", g[k].cp);
        }
        if (fm < 0) {
          refused++;
          if (!why[0]) snprintf(why, sizeof why, "U+%04X has no %s form in %s", g[k].cp, form_name[form], f->ix->label);
          continue;
        }
        double gx = x0 + g[k].x, gyd = base_down - g[k].y;
        int bad = 0;
        if (fm == FORM_OUTLINE) bad = draw_outline(f, &pg, g[k].gid, &m, gx, ys - gyd);
        else if (fm == FORM_COLR) bad = draw_paint(f, &pg, g[k].gid, &m, gx, gyd, col, palette);
        else if (fm == FORM_SVG) bad = draw_svg(f, &pg, g[k].gid, &m, gx, gyd);
        else bad = draw_strike(f, &pg, g[k].gid, &m, gx, gyd, &strike_px);   /* CBDT and sbix pictures too: FreeType decodes them (libpng) per strike */
        if (bad) { refused++; if (!why[0]) snprintf(why, sizeof why, "U+%04X: its %s form could not be drawn", g[k].cp, form_name[fm]); continue; }
        counts[fm]++;
        if (fm == FORM_COLR && v1) colr_v1n++;
      }
      free(g);
    }
    p += i;
    if (*p == '\n') { yp += lsk; p++; }
    else break;
  }
  if (refused && form != FORM_AUTO) {
    free(pg.cov); free(pg.bgra);
    snprintf(err, errlen, "%s", why);
    return 1;
  }
  /* the notes: the font, the forms drawn, what was missing */
  char forms[300] = "";
  for (int k = 1; k <= 5; k++) if (counts[k]) {
    size_t l = strlen(forms);
    if (k == FORM_COLR) snprintf(forms + l, sizeof forms - l, "%s%d from COLR (%d of them version 1 paint graphs)", l ? ", " : "", counts[k], colr_v1n);
    else if (k == FORM_STRIKE) snprintf(forms + l, sizeof forms - l, "%s%d from the font's %d px bitmap strike laid at %d px", l ? ", " : "", counts[k], strike_px, m.em / alias);
    else snprintf(forms + l, sizeof forms - l, "%s%d from %s", l ? ", " : "", counts[k], form_name[k]);
  }
  char pal[48] = "";
  if (palette > 0) snprintf(pal, sizeof pal, "; CPAL palette %d", palette);
  note2("%s: %s%s%s%s%s", f->ix->label, forms[0] ? forms : "no glyph drawn",
        axes && axes[0] ? "; axes " : "", axes && axes[0] ? axes : "", rtl_runs ? "; right-to-left runs by UAX #9" : "", pal);
  if (missing) note2("%s: no glyph for %s, the font's missing glyph is drawn", f->ix->label, miss);
  if (refused) note2("%s: %d glyph(s) not drawn: %s", f->ix->label, refused, why);
  if (counts[FORM_SVG]) note2("%s: SVG glyphs are drawn by plutosvg through FreeType's hooks, which pass no foreground colour: currentColor is black", f->ix->label);
  /* 4 by 4 page pixels to one picture pixel; the operator's colour where outlines and strikes cover, the colour
   * glyphs over that */
  unsigned cb = col & 255, cg = (col >> 8) & 255, cr = (col >> 16) & 255, ca = (col >> 24) & 255;
  for (int yi = 0; yi < YS; yi++) for (int xi = 0; xi < XS; xi++) {
    unsigned cov = 0, c4[4] = { 0, 0, 0, 0 };
    for (int a = 0; a < alias; a++) for (int b = 0; b < alias; b++) {
      size_t o = (size_t) (yi * alias + a) * xs + xi * alias + b;
      cov += pg.cov[o];
      for (int c = 0; c < 4; c++) c4[c] += pg.bgra[4 * o + c];
    }
    cov >>= 4;
    for (int c = 0; c < 4; c++) c4[c] = (c4[c] + 8) >> 4;
    unsigned mono[4] = { cb * cov / 255, cg * cov / 255, cr * cov / 255, ca * cov / 255 };
    uint8_t *d = out + 4 * ((size_t) yi * XS + xi);
    for (int c = 0; c < 4; c++) d[c] = (uint8_t) (c4[c] + (mono[c] * (255 - c4[3]) + 127) / 255);
  }
  free(pg.cov); free(pg.bgra);
  return 0;
}

/* ------------------------------------------------------------------ for the reading: one glyph's ink */

/* The ink of the glyph that character cp maps to in the font with this key, stretched to side by side pixels
 * (its silhouette: the alpha of a colour glyph, the coverage of an outline or a strike), and its measures in em
 * squares, as hf_glyph_mask gives them for version 1: v[0] the ink's width over its height, v[1] its height,
 * v[2] its top below the line's top, v[3] the advance, v[4] the ink's left edge after the pen, v[5] the average
 * character width. form says which form was drawn (FORM_*), colour 1 when it was a colour form.
 * Returns 0; 2 when the glyph has no ink; 1 when the font or the glyph is missing. */
int ht2_glyph_mask(const char *key, unsigned cp, int side, unsigned char *outm, float *v, int *formp, unsigned char *rgba_out)
{
  char err[300];
  struct face2 *f = face_open(key, err, sizeof err);
  if (!f) return 1;
  if (set_axes(f, "", err, sizeof err)) return 1;
  unsigned gid = FT_Get_Char_Index(f->ft, cp);
  if (!gid) return 1;
  /* drawn at four times the picture's side to the em: enough for a 16 or 24 pixel silhouette and its colours */
  const int em = side * 4 < 48 ? 48 : side * 4;
  struct metrics m;
  if (metrics_of(f, em, 0, &m, err, sizeof err)) return 1;
  int v1x = 0, fm0 = choose_form(f, gid, FORM_AUTO, &v1x);
  if (fm0 == FORM_OUTLINE && !rgba_out) {
    /* an outline: read in font units and drawn straight into the side by side box (fast: no page) */
    if (FT_Load_Glyph(f->ft, gid, FT_LOAD_NO_SCALE | FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP) || f->ft->glyph->format != FT_GLYPH_FORMAT_OUTLINE) return 1;
    if (formp) *formp = FORM_OUTLINE;
    double advu = f->sfnt ? hb_font_get_glyph_h_advance(f->hb, gid) : f->ft->glyph->metrics.horiAdvance;
    v[3] = (float) (advu / f->upem);
    v[5] = (float) (m.avg / f->upem);
    FT_Outline *o = &f->ft->glyph->outline;
    if (o->n_points == 0) return 2;
    FT_BBox b;
    FT_Outline_Get_CBox(o, &b);
    double w = b.xMax - b.xMin, h = b.yMax - b.yMin;
    if (w <= 0 || h <= 0) return 2;
    double ascu = m.ascent / m.sy;   /* the line's top above the baseline, in font units */
    v[0] = (float) (w / h);
    v[1] = (float) (h / f->upem);
    v[2] = (float) ((ascu - b.yMax) / f->upem);
    v[4] = (float) (b.xMin / (double) f->upem);
    FT_Outline_Translate(o, -b.xMin, -b.yMin);
    FT_Matrix mt = { (FT_Fixed) floor(side / w * 64.0 * 65536.0 + 0.5), 0, 0, (FT_Fixed) floor(side / h * 64.0 * 65536.0 + 0.5) };
    FT_Outline_Transform(o, &mt);
    struct page pg = { side, side, calloc((size_t) side, (size_t) side), 0 };
    FT_Raster_Params rp;
    memset(&rp, 0, sizeof rp);
    rp.flags = FT_RASTER_FLAG_AA | FT_RASTER_FLAG_DIRECT | FT_RASTER_FLAG_CLIP;
    rp.gray_spans = spans_cov; rp.user = &pg;
    rp.clip_box.xMax = side; rp.clip_box.yMax = side;
    FT_Outline_Render(g_lib2, o, &rp);
    for (int i = 0; i < side * side; i++) outm[i] = pg.cov[i] >= 128 ? 255 : 0;
    free(pg.cov);
    return 0;
  }
  /* the advance and the ink box from a drawing at 256 pixels to the em, on a page large enough for any glyph */
  int W = 4 * em, H = 4 * em;
  struct page pg = { W, H, calloc((size_t) W, (size_t) H), calloc((size_t) W * H, 4) };
  int v1 = 0, fm = choose_form(f, gid, FORM_AUTO, &v1), sp = 0;
  double px = em, base_down = em + m.ascent;
  int bad = fm < 0;
  if (fm == FORM_OUTLINE) bad = draw_outline(f, &pg, gid, &m, px, H - base_down);
  else if (fm == FORM_COLR) bad = draw_paint(f, &pg, gid, &m, px, base_down, 0xff000000u, 0);
  else if (fm == FORM_PNG) bad = draw_strike(f, &pg, gid, &m, px, base_down, &sp);
  else if (fm == FORM_SVG) bad = draw_svg(f, &pg, gid, &m, px, base_down);
  else if (fm == FORM_STRIKE) bad = draw_strike(f, &pg, gid, &m, px, base_down, &sp);
  if (bad) { free(pg.cov); free(pg.bgra); return 1; }
  if (formp) *formp = fm;
  /* the advance as shaping gives it for this one glyph */
  hb_position_t adv;
  double adv_em;
  if (f->sfnt) { adv = hb_font_get_glyph_h_advance(f->hb, gid); adv_em = adv / (double) f->upem; }
  else if (f->scalable) { FT_Set_Char_Size(f->ft, 0, (FT_F26Dot6) em * 64, 72, 72); FT_Load_Glyph(f->ft, gid, FT_LOAD_NO_HINTING); adv_em = f->ft->glyph->advance.x / 64.0 / em; }
  else { int pp = 0, s2 = pick_strike(f, em, &pp); FT_Select_Size(f->ft, s2); FT_Load_Glyph(f->ft, gid, FT_LOAD_DEFAULT); adv_em = f->ft->glyph->advance.x / 64.0 / (pp ? pp : em); }
  (void) adv;
  v[3] = (float) adv_em;
  v[5] = (float) (m.avg / f->upem);
  int x0 = W, y0 = H, x1 = -1, y1 = -1;
  for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) {
    size_t o = (size_t) y * W + x;
    unsigned a = pg.cov[o] > pg.bgra[4 * o + 3] ? pg.cov[o] : pg.bgra[4 * o + 3];
    if (a >= 128) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  }
  if (x1 < 0) { free(pg.cov); free(pg.bgra); return 2; }
  int w = x1 - x0 + 1, h = y1 - y0 + 1;
  v[0] = (float) w / h;
  v[1] = (float) h / em;
  v[2] = (float) (y0 - (base_down - m.ascent)) / em;
  v[4] = (float) (x0 - px) / em;
  for (int gy = 0; gy < side; gy++) for (int gx = 0; gx < side; gx++) {
    int ya = y0 + gy * h / side, yb = y0 + (gy + 1) * h / side, xa = x0 + gx * w / side, xb = x0 + (gx + 1) * w / side;
    if (yb <= ya) yb = ya + 1;
    if (xb <= xa) xb = xa + 1;
    unsigned cnt = 0, tot = 0, sum[4] = { 0, 0, 0, 0 };
    for (int y = ya; y < yb; y++) for (int x = xa; x < xb; x++) {
      size_t o = (size_t) y * W + x;
      unsigned a = pg.cov[o] > pg.bgra[4 * o + 3] ? pg.cov[o] : pg.bgra[4 * o + 3];
      tot++;
      if (a >= 128) cnt++;
      for (int c = 0; c < 4; c++) sum[c] += pg.bgra[4 * o + c];
    }
    outm[gy * side + gx] = (unsigned char) (2 * cnt >= tot ? 255 : 0);
    if (rgba_out) for (int c = 0; c < 4; c++) rgba_out[4 * (gy * side + gx) + c] = (unsigned char) (sum[c] / (tot ? tot : 1));
  }
  free(pg.cov); free(pg.bgra);
  return 0;
}

/* the advance of the space and the average character width of a font, in em squares; 1 when the font is missing */
int ht2_font_spacing(const char *key, float *space, float *avg)
{
  char err[300];
  struct face2 *f = face_open(key, err, sizeof err);
  if (!f) return 1;
  set_axes(f, "", err, sizeof err);
  struct metrics m;
  if (metrics_of(f, 256, 0, &m, err, sizeof err)) return 1;
  unsigned gid = FT_Get_Char_Index(f->ft, ' ');
  if (!gid) *space = 0.25f;
  else if (f->sfnt) *space = (float) (hb_font_get_glyph_h_advance(f->hb, gid) / (double) f->upem);
  else if (f->scalable) { FT_Set_Char_Size(f->ft, 0, 256 * 64, 72, 72); FT_Load_Glyph(f->ft, gid, FT_LOAD_NO_HINTING); *space = (float) (f->ft->glyph->advance.x / 64.0 / 256.0); }
  else { int pp = 0, s2 = pick_strike(f, 256, &pp); FT_Select_Size(f->ft, s2); FT_Load_Glyph(f->ft, gid, FT_LOAD_DEFAULT); *space = (float) (f->ft->glyph->advance.x / 64.0 / (pp ? pp : 256)); }
  *avg = (float) (m.avg / f->upem);
  return 0;
}

#include "uvariant.h"
static int in_ranges(const unsigned (*r)[2], size_t n, unsigned cp)
{
  size_t lo = 0, hi = n;
  while (lo < hi) { size_t m = (lo + hi) / 2; if (r[m][1] < cp) lo = m + 1; else hi = m; }
  return lo < n && r[lo][0] <= cp && cp <= r[lo][1];
}
/* 2: a presentation variant of another character (the reading takes the plain one); 1: a letter of a specialist
 * block (taken only when it lies clearly closer); 0: a plain character */
int uc_class(unsigned cp)
{
  if (in_ranges(uvariant_ranges, sizeof uvariant_ranges / sizeof uvariant_ranges[0], cp)) return 2;
  if (in_ranges(uspecial_ranges, sizeof uspecial_ranges / sizeof uspecial_ranges[0], cp)) return 1;
  return 0;
}

/* 1: a character that is a drawing rather than a letter (Unicode general category So or Sm, or private use, where
 * icon fonts put their pictures); the seeds of milestone 2 prefer them */
int uc_drawing(unsigned cp)
{
  return in_ranges(udrawing_ranges, sizeof udrawing_ranges / sizeof udrawing_ranges[0], cp);
}

/* how many entries the index has, and the key of entry i (for the tools that walk it) */
int ix_count(void) { if (!g_ix_loaded) ix_load(); return g_nix; }
const char *ix_key(int i) { return (i >= 0 && i < g_nix) ? g_ix[i].key : ""; }
const char *ix_label_of(const char *key) { struct ixent *e = ix_find(key); return e ? e->label : ""; }
