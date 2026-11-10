// ktgtool: a small driver around OpenKTG's reference texture generator
// (fr_public/ktg, written 2007 by Fabian "ryg" Giesen, public domain).
// It includes gentexture.cpp unchanged so that the file's static noise
// functions can be called one octave at a time.
//
//   ktgtool octave  L F type seed            > float32 raw, (1<<L)^2 values
//   ktgtool noise   L freq oct fadeoff seed mode R G B [R G B ...] > RGB8 raw
//   ktgtool seedscan L freq oct fadeoff type abs < float32 raw target
//   ktgtool fields  L freq oct fadeoff type < seed numbers as text
//                   > float32 raw, one (1<<L)^2 field per seed: the octave sum
//                   that GenTexture::Noise forms before scaling and the gradient
//   ktgtool tiles   L < one operator per line > RGB8 raw, one (1<<L)^2 tile per line
//                   N freq oct fadeoff seed mode r0 g0 b0 r1 g1 b1   (Noise, 2-stop gradient)
//                   C k  x y r g b  (k times)                        (Cells, inner, amp 0)
//                   G br bg bb  orgx orgy ux vy rectu rectv  r g b   (GlowRect over a flat colour)
//                   F r g b                                          (a flat colour)
//   ktgtool bench                                                    > nanoseconds per pixel
//
// type: 0 = GNoise2 (the grid gradient noise), 1 = Noise2 (the value noise
// that GenTexture::Noise selects with NoiseBandlimit).
#include "gentexture.cpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <cmath>
#include <ctime>
#include <string>
#include <sstream>
#include <iostream>

static float octaveValue(int x, int y, int L, int F, int type, int pseed)
{
  int px = (x << (16 - L + F)) + ((1 << (16 - L + F)) >> 1);
  int py = (y << (16 - L + F)) + ((1 << (16 - L + F)) >> 1);
  int m = (1 << F) - 1;
  return type ? Noise2(px, py, m, m, pseed) : GNoise2(px, py, m, m, pseed);
}

int main(int argc, char **argv)
{
  if (argc < 2) return 2;
  InitTexgen();
  if (!strcmp(argv[1], "octave") && argc == 6) {
    int L = atoi(argv[2]), F = atoi(argv[3]), type = atoi(argv[4]), seed = P(atoi(argv[5]));
    int n = 1 << L;
    std::vector<float> out(size_t(n) * n);
    for (int y = 0; y < n; y++)
      for (int x = 0; x < n; x++)
        out[size_t(y) * n + x] = octaveValue(x, y, L, F, type, seed);
    fwrite(out.data(), sizeof(float), out.size(), stdout);
    return 0;
  }
  if (!strcmp(argv[1], "noise") && argc >= 11 && (argc - 8) % 3 == 0) {
    int L = atoi(argv[2]), freq = atoi(argv[3]), oct = atoi(argv[4]);
    float fadeoff = atof(argv[5]);
    int seed = atoi(argv[6]), mode = atoi(argv[7]);
    int stops = (argc - 8) / 3;
    GenTexture grad(stops, 1);
    for (int i = 0; i < stops; i++)
      grad.Data[i].Init(sU8(atoi(argv[8 + 3 * i])), sU8(atoi(argv[9 + 3 * i])), sU8(atoi(argv[10 + 3 * i])), 255);
    int n = 1 << L;
    GenTexture tex(n, n);
    tex.Noise(grad, freq, freq, oct, fadeoff, seed, mode);
    std::vector<unsigned char> out(size_t(n) * n * 3);
    for (int i = 0; i < n * n; i++) {
      out[3 * i + 0] = (tex.Data[i].r + 128) / 257;
      out[3 * i + 1] = (tex.Data[i].g + 128) / 257;
      out[3 * i + 2] = (tex.Data[i].b + 128) / 257;
    }
    fwrite(out.data(), 1, out.size(), stdout);
    return 0;
  }
  if (!strcmp(argv[1], "fields") && argc == 7) {
    int L = atoi(argv[2]), freq = atoi(argv[3]), oct = atoi(argv[4]);
    float fadeoff = atof(argv[5]);
    int type = atoi(argv[6]);
    int n = 1 << L;
    std::vector<float> out(size_t(n) * n);
    int s;
    while (scanf("%d", &s) == 1) {
      int ps = P(s);
      for (int y = 0; y < n; y++)
        for (int x = 0; x < n; x++) {
          float v = 0, a = 1;
          for (int i = 0; i < oct; i++) { v += a * octaveValue(x, y, L, freq + i, type, ps); a *= fadeoff; }
          out[size_t(y) * n + x] = v;
        }
      fwrite(out.data(), sizeof(float), out.size(), stdout);
    }
    return 0;
  }
  if (!strcmp(argv[1], "tiles") && argc == 3) {
    int L = atoi(argv[2]);
    int n = 1 << L;
    std::string line;
    std::vector<unsigned char> out(size_t(n) * n * 3);
    while (std::getline(std::cin, line)) {
      if (line.empty()) continue;
      std::istringstream in(line);
      char kind; in >> kind;
      GenTexture tex(n, n);
      if (kind == 'N') {
        int freq, oct, seed, mode, c[6]; float fade;
        in >> freq >> oct >> fade >> seed >> mode;
        for (int i = 0; i < 6; i++) in >> c[i];
        GenTexture grad(2, 1);
        grad.Data[0].Init(sU8(c[0]), sU8(c[1]), sU8(c[2]), 255);
        grad.Data[1].Init(sU8(c[3]), sU8(c[4]), sU8(c[5]), 255);
        tex.Noise(grad, freq, freq, oct, fade, seed, mode);
      } else if (kind == 'C') {
        int k; in >> k;
        std::vector<CellCenter> cc(k);
        for (int i = 0; i < k; i++) {
          int r, g, b; in >> cc[i].x >> cc[i].y >> r >> g >> b;
          cc[i].color.Init(sU8(r), sU8(g), sU8(b), 255);
        }
        GenTexture grad(2, 1);
        grad.Data[0].Init(255, 255, 255, 255);
        grad.Data[1].Init(255, 255, 255, 255);
        tex.Cells(grad, cc.data(), k, 0.0f, GenTexture::CellInner);
      } else if (kind == 'G') {
        int br, bg, bb, r, g, b; float ox, oy, ux, vy, ru, rv;
        in >> br >> bg >> bb >> ox >> oy >> ux >> vy >> ru >> rv >> r >> g >> b;
        GenTexture back(n, n);
        Pixel p; p.Init(sU8(br), sU8(bg), sU8(bb), 255);
        for (int i = 0; i < n * n; i++) back.Data[i] = p;
        GenTexture grad(2, 1);
        grad.Data[0].Init(sU8(r), sU8(g), sU8(b), 255);
        grad.Data[1].Init(0x00000000u);
        tex.GlowRect(back, grad, ox, oy, ux, 0.0f, 0.0f, vy, ru, rv);
      } else if (kind == 'F') {
        int r, g, b; in >> r >> g >> b;
        Pixel p; p.Init(sU8(r), sU8(g), sU8(b), 255);
        for (int i = 0; i < n * n; i++) tex.Data[i] = p;
      } else return 4;
      for (int i = 0; i < n * n; i++) {
        out[3 * i + 0] = (tex.Data[i].r + 128) / 257;
        out[3 * i + 1] = (tex.Data[i].g + 128) / 257;
        out[3 * i + 2] = (tex.Data[i].b + 128) / 257;
      }
      fwrite(out.data(), 1, out.size(), stdout);
    }
    return 0;
  }
  if (!strcmp(argv[1], "bench")) {
    // time OpenKTG's own reference code, one thread: nanoseconds per pixel
    auto now = []() { timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec * 1e9 + t.tv_nsec; };
    const int L = 9, n = 1 << L;
    GenTexture grad(2, 1);
    grad.Data[0].Init(0, 0, 0, 255); grad.Data[1].Init(255, 255, 255, 255);
    for (int type = 0; type < 2; type++)
      for (int oct = 1; oct <= 8; oct *= 2) {
        GenTexture tex(n, n);
        double t0 = now();
        for (int rep = 0; rep < 4; rep++) tex.Noise(grad, 1, 1, oct, 0.7f, 7 + rep, 2 | (type ? 4 : 0));
        printf("noise type %d octaves %d: %.2f ns per pixel\n", type, oct, (now() - t0) / (4.0 * n * n));
      }
    for (int k = 4; k <= 64; k *= 4) {
      std::vector<CellCenter> cc(k);
      for (int i = 0; i < k; i++) { cc[i].x = (i * 37 % 101) / 101.0f; cc[i].y = (i * 53 % 103) / 103.0f; cc[i].color.Init(sU8(i * 5), 100, 50, 255); }
      GenTexture tex(n, n);
      double t0 = now();
      for (int rep = 0; rep < 4; rep++) tex.Cells(grad, cc.data(), k, 0.0f, GenTexture::CellInner);
      printf("cells %d centres: %.2f ns per pixel\n", k, (now() - t0) / (4.0 * n * n));
    }
    {
      GenTexture tex(n, n), back(n, n);
      double t0 = now();
      for (int rep = 0; rep < 4; rep++) tex.GlowRect(back, grad, 0.5f, 0.5f, 0.5f, 0.0f, 0.0f, 0.5f, 0.75f, 0.75f);
      printf("glowrect over the whole tile: %.2f ns per pixel\n", (now() - t0) / (4.0 * n * n));
    }
    {
      // the gradient term: one bilinear blend of four corner colours per pixel
      GenTexture tex(n, n);
      Pixel c[4];
      c[0].Init(10, 20, 30, 255); c[1].Init(200, 20, 30, 255); c[2].Init(10, 220, 30, 255); c[3].Init(10, 20, 230, 255);
      double t0 = now();
      for (int rep = 0; rep < 4; rep++)
        for (int y = 0; y < n; y++)
          for (int x = 0; x < n; x++) {
            Pixel a, b;
            a.Lerp((x << 16) >> L, c[0], c[1]);
            b.Lerp((x << 16) >> L, c[2], c[3]);
            tex.Data[y * n + x].Lerp((y << 16) >> L, a, b);
          }
      printf("bilinear gradient: %.2f ns per pixel\n", (now() - t0) / (4.0 * n * n));
    }
    return 0;
  }
  if (!strcmp(argv[1], "seedscan") && argc == 8) {
    int L = atoi(argv[2]), freq = atoi(argv[3]), oct = atoi(argv[4]);
    float fadeoff = atof(argv[5]);
    int type = atoi(argv[6]), absmode = atoi(argv[7]);
    int n = 1 << L;
    size_t N = size_t(n) * n;
    std::vector<float> target(N);
    if (fread(target.data(), sizeof(float), N, stdin) != N) return 3;
    double tm = 0, tv = 0;
    for (size_t i = 0; i < N; i++) tm += target[i];
    tm /= N;
    for (size_t i = 0; i < N; i++) tv += (target[i] - tm) * (target[i] - tm);
    std::vector<float> img(N);
    double best = -2; int bestSeed = -1; double second = -2;
    for (int s = 0; s < 4096; s++) {
      int ps = P(s);
      double m = 0;
      for (int y = 0; y < n; y++)
        for (int x = 0; x < n; x++) {
          float v = 0, a = 1;
          for (int i = 0; i < oct; i++) {
            float nv = octaveValue(x, y, L, freq + i, type, ps);
            if (absmode) nv = fabsf(nv);
            v += a * nv; a *= fadeoff;
          }
          img[size_t(y) * n + x] = v; m += v;
        }
      m /= N;
      double c = 0, v2 = 0;
      for (size_t i = 0; i < N; i++) { c += (img[i] - m) * (target[i] - tm); v2 += (img[i] - m) * (img[i] - m); }
      double r = (v2 > 0 && tv > 0) ? c / sqrt(v2 * tv) : 0;
      if (r > best) { second = best; best = r; bestSeed = s; }
      else if (r > second) second = r;
    }
    printf("%d %.6f %.6f\n", bestSeed, best, second);
    return 0;
  }
  return 2;
}
