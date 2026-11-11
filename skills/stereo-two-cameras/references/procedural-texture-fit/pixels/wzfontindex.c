/* The font index and the glyph-shape index (ORDER 508, milestone 1e).
 *
 * fi_index: every font file under the folders given, every face of a collection, one line each: what the
 * font says of itself in its own tables (OpenType 1.9.1 "name": family 16/1, subfamily 17/2, version 5,
 * copyright 0, designer 9, licence 13 and 14; "OS/2" fsType), the form of its glyphs (glyf, CFF, CFF2,
 * COLR and its version, CPAL, SVG, CBDT, sbix, EBDT, the strikes of a bitmap font), its variation axes ("fvar")
 * and named instances, and the characters its cmap maps, counted per Unicode block (Blocks.txt).
 *
 * gi_build: for every font of an index and every character its cmap maps, the glyph's ink stretched to its own
 * box as 16 by 16 bits, with the ink's proportions: the coarse picture a piece of ink is compared with first.
 */
#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_OUTLINE_H
#include FT_TRUETYPE_TABLES_H
#include FT_TRUETYPE_TAGS_H
#include FT_TRUETYPE_IDS_H
#include FT_SFNT_NAMES_H
#include FT_MULTIPLE_MASTERS_H
#include FT_FONT_FORMATS_H
#include <ftw.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include "ublocks.h"   /* generated from Unicode's Blocks.txt: struct { unsigned lo, hi; const char *name; } ublocks[] */

static FT_Library g_lib3;

/* ------------------------------------------------------------------ names */

static void clean(char *s)
{
  for (; *s; s++) if (*s == '\t' || *s == '\n' || *s == '\r') *s = ' ';
}

static void utf8_put(char **o, char *end, unsigned c)
{
  char *p = *o;
  if (c < 0x80) { if (p + 1 < end) *p++ = (char) c; }
  else if (c < 0x800) { if (p + 2 < end) { *p++ = (char) (0xc0 | (c >> 6)); *p++ = (char) (0x80 | (c & 63)); } }
  else if (c < 0x10000) { if (p + 3 < end) { *p++ = (char) (0xe0 | (c >> 12)); *p++ = (char) (0x80 | ((c >> 6) & 63)); *p++ = (char) (0x80 | (c & 63)); } }
  else if (p + 4 < end) { *p++ = (char) (0xf0 | (c >> 18)); *p++ = (char) (0x80 | ((c >> 12) & 63)); *p++ = (char) (0x80 | ((c >> 6) & 63)); *p++ = (char) (0x80 | (c & 63)); }
  *o = p;
}

/* a name of the font's own 'name' table: Windows Unicode English first, then any Windows Unicode, then Mac Roman */
static int sfnt_name(FT_Face f, int id, char *out, int outlen)
{
  int n = (int) FT_Get_Sfnt_Name_Count(f), best = -1, rank = 9;
  FT_SfntName nm;
  for (int i = 0; i < n; i++) {
    if (FT_Get_Sfnt_Name(f, (FT_UInt) i, &nm) || nm.name_id != id) continue;
    int r = 9;
    if (nm.platform_id == TT_PLATFORM_MICROSOFT && (nm.encoding_id == TT_MS_ID_UNICODE_CS || nm.encoding_id == TT_MS_ID_UCS_4)) r = nm.language_id == 0x409 ? 0 : 1;
    else if (nm.platform_id == TT_PLATFORM_APPLE_UNICODE) r = 2;
    else if (nm.platform_id == TT_PLATFORM_MACINTOSH && nm.encoding_id == TT_MAC_ID_ROMAN) r = nm.language_id == 0 ? 3 : 4;
    if (r < rank) { rank = r; best = i; }
  }
  out[0] = 0;
  if (best < 0 || FT_Get_Sfnt_Name(f, (FT_UInt) best, &nm)) return 0;
  char *o = out, *end = out + outlen - 1;
  if (rank <= 2) {
    for (unsigned k = 0; k + 1 < nm.string_len; k += 2) {
      unsigned c = (unsigned) (nm.string[k] << 8 | nm.string[k + 1]);
      if (c >= 0xd800 && c < 0xdc00 && k + 3 < nm.string_len) {
        unsigned d = (unsigned) (nm.string[k + 2] << 8 | nm.string[k + 3]);
        c = 0x10000 + ((c - 0xd800) << 10) + (d - 0xdc00); k += 2;
      }
      utf8_put(&o, end, c);
    }
  } else for (unsigned k = 0; k < nm.string_len; k++) utf8_put(&o, end, nm.string[k] < 0x80 ? nm.string[k] : '?');
  *o = 0;
  clean(out);
  return out[0] != 0;
}

static unsigned long table_len(FT_Face f, FT_ULong tag)
{
  FT_ULong len = 0;
  if (FT_Load_Sfnt_Table(f, tag, 0, NULL, &len)) return 0;
  return len;
}

static int colr_version(FT_Face f)
{
  unsigned char b[2];
  FT_ULong len = 2;
  if (!table_len(f, TTAG_COLR) || FT_Load_Sfnt_Table(f, TTAG_COLR, 0, b, &len)) return -1;
  return b[0] << 8 | b[1];
}

/* ------------------------------------------------------------------ the font index */

struct row { char *line; char key[512]; };
static struct row *g_rows;
static int g_nrows, g_caprows;
static const char *g_source;
static int g_files, g_faces_bad;

static void index_face(const char *path, FT_Face f, int fi, const char *wrapper)
{
  char fam[256] = "", sty[256] = "", ver[256] = "", cpy[600] = "", des[400] = "", lic[600] = "", licu[300] = "";
  if (FT_IS_SFNT(f)) {
    if (!sfnt_name(f, 16, fam, sizeof fam)) sfnt_name(f, 1, fam, sizeof fam);
    if (!sfnt_name(f, 17, sty, sizeof sty)) sfnt_name(f, 2, sty, sizeof sty);
    sfnt_name(f, 5, ver, sizeof ver); sfnt_name(f, 0, cpy, sizeof cpy); sfnt_name(f, 9, des, sizeof des);
    sfnt_name(f, 13, lic, sizeof lic); sfnt_name(f, 14, licu, sizeof licu);
  }
  if (!fam[0] && f->family_name) { snprintf(fam, sizeof fam, "%s", f->family_name); clean(fam); }
  if (!sty[0] && f->style_name) { snprintf(sty, sizeof sty, "%s", f->style_name); clean(sty); }
  if (!fam[0]) { const char *b = strrchr(path, '/'); snprintf(fam, sizeof fam, "%s", b ? b + 1 : path); }
  if (!sty[0]) snprintf(sty, sizeof sty, "Regular");
  if (!ver[0]) snprintf(ver, sizeof ver, "-");
  const char *fmt = FT_Get_Font_Format(f);
  char outl[64] = "-", col[128] = "", axes[600] = "-";
  if (FT_IS_SFNT(f)) {
    if (table_len(f, TTAG_glyf)) snprintf(outl, sizeof outl, "glyf");
    else if (table_len(f, TTAG_CFF2)) snprintf(outl, sizeof outl, "CFF2");
    else if (table_len(f, TTAG_CFF)) snprintf(outl, sizeof outl, "CFF");
    int cv = colr_version(f);
    if (cv >= 0) snprintf(col + strlen(col), sizeof col - strlen(col), "%sCOLRv%d", col[0] ? "," : "", cv);
    if (table_len(f, TTAG_CPAL)) snprintf(col + strlen(col), sizeof col - strlen(col), "%sCPAL", col[0] ? "," : "");
    if (table_len(f, TTAG_SVG)) snprintf(col + strlen(col), sizeof col - strlen(col), "%sSVG", col[0] ? "," : "");
    if (table_len(f, TTAG_CBDT)) snprintf(col + strlen(col), sizeof col - strlen(col), "%sCBDT", col[0] ? "," : "");
    if (table_len(f, TTAG_sbix)) snprintf(col + strlen(col), sizeof col - strlen(col), "%ssbix", col[0] ? "," : "");
    if (table_len(f, TTAG_EBDT)) snprintf(col + strlen(col), sizeof col - strlen(col), "%sEBDT", col[0] ? "," : "");
  } else if (FT_IS_SCALABLE(f)) snprintf(outl, sizeof outl, "%s", fmt);
  if (!FT_IS_SCALABLE(f) && f->num_fixed_sizes) {
    snprintf(col + strlen(col), sizeof col - strlen(col), "%sstrikes:", col[0] ? "," : "");
    for (int i = 0; i < f->num_fixed_sizes && i < 12; i++) snprintf(col + strlen(col), sizeof col - strlen(col), "%s%d", i ? "/" : "", f->available_sizes[i].height);
  }
  if (!col[0]) snprintf(col, sizeof col, "-");
  int inst = 0;
  if (FT_HAS_MULTIPLE_MASTERS(f)) {
    FT_MM_Var *mm;
    if (!FT_Get_MM_Var(f, &mm)) {
      axes[0] = 0;
      for (unsigned a = 0; a < mm->num_axis; a++) {
        char tg[5] = { (char) (mm->axis[a].tag >> 24), (char) (mm->axis[a].tag >> 16), (char) (mm->axis[a].tag >> 8), (char) mm->axis[a].tag, 0 };
        size_t l = strlen(axes);
        snprintf(axes + l, sizeof axes - l, "%s%s:%g:%g:%g", a ? " " : "", tg, mm->axis[a].minimum / 65536.0, mm->axis[a].def / 65536.0, mm->axis[a].maximum / 65536.0);
      }
      inst = (int) mm->num_namedstyles;
      FT_Done_MM_Var(g_lib3, mm);
    }
  }
  /* coverage: the characters the Unicode cmap maps, per block */
  static unsigned blockn[sizeof ublocks / sizeof ublocks[0]];
  memset(blockn, 0, sizeof blockn);
  long chars = 0;
  const char *cmapkind = "unicode";
  if (FT_Select_Charmap(f, FT_ENCODING_UNICODE)) {
    if (!FT_Select_Charmap(f, FT_ENCODING_MS_SYMBOL)) cmapkind = "symbol";
    else cmapkind = "none";
  }
  if (strcmp(cmapkind, "none")) {
    FT_UInt gi;
    FT_ULong c = FT_Get_First_Char(f, &gi);
    size_t b = 0, nb = sizeof ublocks / sizeof ublocks[0];
    while (gi) {
      chars++;
      while (b < nb && ublocks[b].hi < c) b++;   /* the cmap's characters come in rising order */
      if (b < nb && ublocks[b].lo <= c) blockn[b]++;
      c = FT_Get_Next_Char(f, c, &gi);
    }
  }
  char blocks[8192] = "";
  for (size_t b = 0; b < sizeof ublocks / sizeof ublocks[0]; b++) if (blockn[b]) {
    size_t l = strlen(blocks);
    if (l + 80 < sizeof blocks) snprintf(blocks + l, sizeof blocks - l, "%s%s:%u", l ? ";" : "", ublocks[b].name, blockn[b]);
  }
  if (!blocks[0]) snprintf(blocks, sizeof blocks, "-");
  TT_OS2 *os2 = (TT_OS2 *) FT_Get_Sfnt_Table(f, FT_SFNT_OS2);
  char fst[16] = "-";
  if (os2) snprintf(fst, sizeof fst, "0x%04x", os2->fsType);
  char *line = malloc(20000);
  char fmt2[96];
  snprintf(fmt2, sizeof fmt2, "%s%s%s", fmt, wrapper ? " in " : "", wrapper ? wrapper : "");
  snprintf(line, 20000, "%s\t%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%ld\t%ld\t%s\t%s\t%s\t%s\t%s\t%s\t%s",
           path, fi, g_source, fam, sty, ver, fmt2, outl, col, axes, inst, (long) f->num_glyphs, chars, cmapkind, blocks, des[0] ? des : "-", cpy[0] ? cpy : "-",
           lic[0] ? lic : "-", licu[0] ? licu : "-", fst);
  if (g_nrows >= g_caprows) { g_caprows = g_caprows ? 2 * g_caprows : 4096; g_rows = realloc(g_rows, (size_t) g_caprows * sizeof *g_rows); }
  g_rows[g_nrows].line = line;
  snprintf(g_rows[g_nrows].key, sizeof g_rows[g_nrows].key, "%s/%s", fam, sty);
  g_nrows++;
}

static const char *exts[] = { ".ttf", ".otf", ".ttc", ".otc", ".otb", ".pfb", ".pfa", ".t1", ".pcf", ".pcf.gz", ".bdf", ".bdf.gz", ".woff", ".woff2", ".pfr", ".fon", ".fnt", ".dfont", ".t42", 0 };

static int is_font(const char *p)
{
  size_t n = strlen(p);
  for (int i = 0; exts[i]; i++) { size_t e = strlen(exts[i]); if (n > e && !strcasecmp(p + n - e, exts[i])) return 1; }
  return 0;
}

static char **g_paths;
static int g_npaths, g_cappaths;
static int collect(const char *p, const struct stat *st, int type, struct FTW *ftw)
{
  (void) st; (void) ftw;
  if (type != FTW_F || !is_font(p)) return 0;
  if (g_npaths >= g_cappaths) { g_cappaths = g_cappaths ? 2 * g_cappaths : 4096; g_paths = realloc(g_paths, (size_t) g_cappaths * sizeof *g_paths); }
  g_paths[g_npaths++] = strdup(p);
  return 0;
}
static int pcmp(const void *a, const void *b) { return strcmp(*(char *const *) a, *(char *const *) b); }

static const char *wrapper_of(const char *p)
{
  FILE *fp = fopen(p, "rb");
  if (!fp) return 0;
  char m[4] = { 0 };
  size_t r = fread(m, 1, 4, fp);
  fclose(fp);
  if (r == 4 && !memcmp(m, "wOFF", 4)) return "WOFF";
  if (r == 4 && !memcmp(m, "wOF2", 4)) return "WOFF2";
  return 0;
}

/* p2p fontindex SOURCE=DIR ...: the index on standard output, a header line first. Keys are family/style; a key
 * already taken by an earlier source or file gets " #2", " #3" (sources in the order given, files sorted). */
int fi_index(int nsrc, char **srcs)
{
  if (FT_Init_FreeType(&g_lib3)) { fprintf(stderr, "FreeType did not start\n"); return 1; }
  for (int s = 0; s < nsrc; s++) {
    char *eq = strchr(srcs[s], '=');
    if (!eq) { fprintf(stderr, "a source is NAME=FOLDER: %s\n", srcs[s]); return 1; }
    *eq = 0;
    g_source = srcs[s];
    g_npaths = 0;
    nftw(eq + 1, collect, 32, FTW_PHYS);
    qsort(g_paths, (size_t) g_npaths, sizeof *g_paths, pcmp);
    for (int i = 0; i < g_npaths; i++) {
      FT_Face f;
      g_files++;
      if (FT_New_Face(g_lib3, g_paths[i], -1, &f)) { fprintf(stderr, "not a font FreeType reads: %s\n", g_paths[i]); g_faces_bad++; continue; }
      long nf = f->num_faces;
      FT_Done_Face(f);
      const char *wr = wrapper_of(g_paths[i]);
      for (long k = 0; k < nf; k++) {
        if (FT_New_Face(g_lib3, g_paths[i], k, &f)) { fprintf(stderr, "face %ld of %s cannot be read\n", k, g_paths[i]); g_faces_bad++; continue; }
        index_face(g_paths[i], f, (int) k, wr);
        FT_Done_Face(f);
      }
      free(g_paths[i]);
    }
  }
  printf("key\tfile\tface\tsource\tfamily\tstyle\tversion\tformat\toutlines\tcolour\taxes\tinstances\tglyphs\tchars\tcmap\tblocks\tdesigner\tcopyright\tlicence\tlicence_url\tfstype\n");
  for (int i = 0; i < g_nrows; i++) {
    char key[560];
    snprintf(key, sizeof key, "%s", g_rows[i].key);
    int dup = 1;
    for (int j = 0; j < i; j++) if (!strcmp(g_rows[j].key, g_rows[i].key)) dup++;
    if (dup > 1) snprintf(key, sizeof key, "%s #%d", g_rows[i].key, dup);
    printf("%s\t%s\n", key, g_rows[i].line);
  }
  fprintf(stderr, "fontindex: %d files, %d faces, %d not read\n", g_files, g_nrows, g_faces_bad);
  return 0;
}

/* ------------------------------------------------------------------ the glyph-shape index */

/* one entry: the font's place in the index, the character, the ink's width over its height, the form it was drawn
 * in, and its ink stretched to its own box as 16 by 16 bits (row by row, 32 bytes) */
struct gient { uint32_t font, cp; float aspect; uint8_t form, parts, pad[2]; uint8_t bits[32]; };

int ht2_glyph_mask(const char *key, unsigned cp, int side, unsigned char *outm, float *v, int *formp, unsigned char *rgba_out);
int ix_count(void);
const char *ix_key(int i);

static void spans16(int y, int count, const FT_Span *sp, void *user)
{
  unsigned char *m = user;
  int row = 63 - y;
  if (row < 0 || row >= 64) return;
  for (int i = 0; i < count; i++) for (int x = sp[i].x; x < sp[i].x + sp[i].len; x++) if (x >= 0 && x < 64 && m[row * 64 + x] < sp[i].coverage) m[row * 64 + x] = sp[i].coverage;
}

/* the outline's ink at 64 by 64 stretched to its box, then 16 by 16 by majority; 0, or 2 for no ink, 1 failure */
static int outline_bits(FT_Face f, unsigned gid, uint8_t *bits, float *aspect)
{
  if (FT_Load_Glyph(f, gid, FT_LOAD_NO_SCALE | FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP) || f->glyph->format != FT_GLYPH_FORMAT_OUTLINE) return 1;
  FT_Outline *o = &f->glyph->outline;
  if (o->n_points == 0) return 2;
  FT_BBox b;
  FT_Outline_Get_CBox(o, &b);
  double w = b.xMax - b.xMin, h = b.yMax - b.yMin;
  if (w <= 0 || h <= 0) return 2;
  *aspect = (float) (w / h);
  FT_Outline_Translate(o, -b.xMin, -b.yMin);
  FT_Matrix m = { (FT_Fixed) floor(64.0 / w * 64.0 * 65536.0 + 0.5), 0, 0, (FT_Fixed) floor(64.0 / h * 64.0 * 65536.0 + 0.5) };
  FT_Outline_Transform(o, &m);
  unsigned char g[64 * 64];
  memset(g, 0, sizeof g);
  FT_Raster_Params rp;
  memset(&rp, 0, sizeof rp);
  rp.flags = FT_RASTER_FLAG_AA | FT_RASTER_FLAG_DIRECT | FT_RASTER_FLAG_CLIP;
  rp.gray_spans = spans16; rp.user = g;
  rp.clip_box.xMax = 64; rp.clip_box.yMax = 64;
  FT_Outline_Render(g_lib3, o, &rp);
  memset(bits, 0, 32);
  int any = 0;
  for (int y = 0; y < 16; y++) for (int x = 0; x < 16; x++) {
    unsigned s = 0;
    for (int a = 0; a < 4; a++) for (int c = 0; c < 4; c++) s += g[(4 * y + a) * 64 + 4 * x + c];
    if (s >= 16 * 128) { bits[(y * 16 + x) >> 3] |= (uint8_t) (1u << (x & 7)); any = 1; }
  }
  return any ? 0 : 2;
}

/* p2p glyphindex OUT.bin [k n]: every font of the index (WZ_FONTINDEX), every character of its cmap; with k n,
 * only the fonts whose place in the index is k modulo n (several builds side by side, joined afterwards) */
int gi_build(const char *outpath, int shard, int nshard)
{
  if (!g_lib3 && FT_Init_FreeType(&g_lib3)) { fprintf(stderr, "FreeType did not start\n"); return 1; }
  FILE *out = fopen(outpath, "wb");
  if (!out) { fprintf(stderr, "cannot write %s\n", outpath); return 1; }
  int n = ix_count();
  long total = 0, colour = 0, fail = 0;
  const char *ixp = getenv("WZ_FONTINDEX");
  /* the file and face of each key are read again here from the index lines (the renderer keeps them private) */
  FILE *ix = fopen(ixp, "r");
  char *line = malloc(1 << 16);
  int fi = -1;
  while (fgets(line, 1 << 16, ix)) {
    if (!strncmp(line, "key\t", 4)) continue;
    fi++;
    (void) n;
    if (nshard > 1 && fi % nshard != shard) continue;
    char *t1 = strchr(line, '\t'); if (!t1) continue; *t1 = 0;
    char *file = t1 + 1, *t2 = strchr(file, '\t'); if (!t2) continue; *t2 = 0;
    int face = atoi(t2 + 1);
    const char *key = line;
    FT_Face f;
    if (FT_New_Face(g_lib3, file, face, &f)) { fail++; continue; }
    int has_colour = 0;
    if (FT_IS_SFNT(f)) has_colour = table_len(f, TTAG_COLR) || table_len(f, TTAG_SVG) || table_len(f, TTAG_CBDT) || table_len(f, TTAG_sbix);
    if (FT_Select_Charmap(f, FT_ENCODING_UNICODE) && FT_Select_Charmap(f, FT_ENCODING_MS_SYMBOL)) { FT_Done_Face(f); continue; }
    FT_UInt gid;
    FT_ULong c = FT_Get_First_Char(f, &gid);
    while (gid) {
      struct gient e;
      memset(&e, 0, sizeof e);
      e.font = (uint32_t) fi; e.cp = (uint32_t) c;
      int r;
      if (has_colour || !FT_IS_SCALABLE(f)) {
        /* colour glyphs and strikes: the silhouette the renderer draws (alpha of the colour, coverage of a strike) */
        unsigned char m[16 * 16];
        float v[6];
        int form = 0;
        r = ht2_glyph_mask(key, (unsigned) c, 16, m, v, &form, NULL);
        if (r == 0) {
          e.aspect = v[0]; e.form = (uint8_t) form;
          for (int i = 0; i < 256; i++) if (m[i]) e.bits[i >> 3] |= (uint8_t) (1u << (i & 7));
        }
        if (has_colour) colour++;
      } else {
        r = outline_bits(f, gid, e.bits, &e.aspect);
        e.form = 1;
      }
      if (r == 0) { fwrite(&e, sizeof e, 1, out); total++; }
      c = FT_Get_Next_Char(f, c, &gid);
    }
    FT_Done_Face(f);
  }
  fclose(ix);
  fclose(out);
  fprintf(stderr, "glyphindex: %ld glyphs with ink (%ld from colour fonts), %ld fonts not opened\n", total, colour, fail);
  return 0;
}
