// ktgtool: a small driver around OpenKTG's reference texture generator
// (fr_public/ktg, written 2007 by Fabian "ryg" Giesen, public domain).
// It includes gentexture.cpp unchanged so that the file's static noise
// functions can be called one octave at a time.
//
//   ktgtool octave  L F type seed            > float32 raw, (1<<L)^2 values
//   ktgtool noise   L freq oct fadeoff seed mode R G B [R G B ...] > RGB8 raw
//   ktgtool seedscan L freq oct fadeoff type abs < float32 raw target
//
// type: 0 = GNoise2 (the grid gradient noise), 1 = Noise2 (the value noise
// that GenTexture::Noise selects with NoiseBandlimit).
#include "gentexture.cpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <cmath>

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
