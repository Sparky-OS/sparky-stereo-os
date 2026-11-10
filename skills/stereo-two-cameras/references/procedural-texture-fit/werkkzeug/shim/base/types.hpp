// A small stand-in for altona's base/types.hpp: only what wz4frlib/wz3_bitmap_code.cpp uses.
// The random generators, sFindLowerPower, sMulShift, sDivShift, sMulDiv and sHermite are copied
// from altona (fr_public/altona_wz4/altona/main/base/types.cpp and math.cpp, BSD licence,
// Dierk Ohlerich, Fabian Giesen, Thomas Mahlke, Christoph Muetze, Tammo Hinrichs, Bastian Zuehlke,
// 49Games GmbH) so that the operators draw what they draw there.
#ifndef SHIM_TYPES_HPP
#define SHIM_TYPES_HPP
#include <cmath>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <vector>
typedef int sInt; typedef float sF32; typedef double sF64; typedef unsigned long long sU64; typedef long long sS64;
typedef unsigned short sU16; typedef short sS16; typedef unsigned int sU32; typedef unsigned char sU8; typedef signed char sS8;
typedef int sBool; typedef wchar_t sChar; typedef long sDInt;
#define sTRUE 1
#define sFALSE 0
#define sINLINE inline
#define sVERIFY(x) do { if(!(x)) { fprintf(stderr,"verify failed: %s line %d\n",#x,__LINE__); abort(); } } while(0)
#define sVERIFYFALSE sVERIFY(0)
#define sALIGNED(type,name,al) type name __attribute__((aligned(al)))
#define __stdcall
#define sPI2 6.28318530717958647692
#define sPI2F 6.28318530717958647692f
#define sPIF 3.14159265358979323846f
#define sTEX_ARGB8888 0
#define sTEX_2D 0
template<class T> inline T sMin(T a,T b) { return a<b?a:b; }
template<class T> inline T sMax(T a,T b) { return a>b?a:b; }
template<class T> inline T sClamp(T a,T mi,T ma) { return a<mi?mi:(a>ma?ma:a); }
template<class T> inline void sSwap(T &a,T &b) { T t=a; a=b; b=t; }
template<class T> inline T sAbs(T a) { return a<0?-a:a; }
inline sF32 sFPow(sF32 a,sF32 b) { return powf(a,b); }
inline sF32 sPow(sF32 a,sF32 b) { return powf(a,b); }
inline sF32 sFSqrt(sF32 a) { return sqrtf(a); }
inline sF32 sFSin(sF32 a) { return sinf(a); }
inline sF32 sFCos(sF32 a) { return cosf(a); }
inline sF32 sFAbs(sF32 a) { return fabsf(a); }
inline sF32 sFCeil(sF32 a) { return ceilf(a); }
inline sF32 sFATan2(sF32 a,sF32 b) { return atan2f(a,b); }
inline sF32 sFRSqrt(sF32 f) { return 1.0f/sqrtf(f); }
inline sF32 sFInvSqrt(sF32 f) { return 1.0f/sqrtf(f); }
inline void sFSinCos(sF32 f,sF32 &s,sF32 &c) { s=sinf(f); c=cosf(f); }
inline sInt sFtol(sF32 f) { return (sInt)f; }
inline void sCopyMem(void *d,const void *s,sDInt n) { memcpy(d,s,n); }
inline void sSetMem(void *d,sInt v,sDInt n) { memset(d,v,n); }
inline void sFatal(const wchar_t *) { fprintf(stderr,"fatal\n"); abort(); }
#define __assume(x)
inline sInt sMulShift(sInt a,sInt b) { return (sS64(a)*b)>>16; }
inline sInt sDivShift(sInt a,sInt b) { return (sS64(a)<<16)/b; }
inline sInt sMulDiv(sInt a,sInt b,sInt c) { return sS64(a)*b/c; }
inline sInt sFindLowerPower(sInt x) { sInt y=0; while((2<<y)<=x) y++; return y; }
inline sInt sFindHigherPower(sInt x) { sInt y=0; while((1<<y)<x) y++; return y; }
inline sU32 sMakeMask(sU32 max) { sU32 m=0; while(m<max) m=m*2+1; return m; }
struct sVector30 { sF32 x,y,z; sVector30() : x(0),y(0),z(0) {} sVector30(sF32 a,sF32 b,sF32 c) : x(a),y(b),z(c) {} void Init(sF32 a,sF32 b,sF32 c) { x=a; y=b; z=c; }
  sF32 operator[](sInt i) const { return (&x)[i]; }
  void Fade(sF32 f,const sVector30 &a,const sVector30 &b) { x=a.x+(b.x-a.x)*f; y=a.y+(b.y-a.y)*f; z=a.z+(b.z-a.z)*f; } };
struct sVector4 { sF32 x,y,z,w; sVector4() : x(0),y(0),z(0),w(0) {} sVector4(sF32 a,sF32 b,sF32 c,sF32 d) : x(a),y(b),z(c),w(d) {}
  void Init(sF32 a,sF32 b,sF32 c,sF32 d) { x=a; y=b; z=c; w=d; }
  sVector4 operator*(sF32 f) const { return sVector4(x*f,y*f,z*f,w*f); }
  sVector4 operator+(const sVector4 &o) const { return sVector4(x+o.x,y+o.y,z+o.z,w+o.w); }
  sVector4 operator-(const sVector4 &o) const { return sVector4(x-o.x,y-o.y,z-o.z,w-o.w); }
  void InitColor(sU32 c) { x=((c>>16)&255)/255.0f; y=((c>>8)&255)/255.0f; z=(c&255)/255.0f; w=((c>>24)&255)/255.0f; } };
inline sVector4 operator*(sF32 f,const sVector4 &v) { return v*f; }
struct sVector2 { sF32 x,y; sVector2() : x(0),y(0) {} sVector2(sF32 a,sF32 b) : x(a),y(b) {} };
struct sRect { sInt x0,y0,x1,y1; sRect() {} sRect(sInt a,sInt b,sInt c,sInt d) : x0(a),y0(b),x1(c),y1(d) {} sInt SizeX() const { return x1-x0; } sInt SizeY() const { return y1-y0; } };
template<class T> struct sArray { std::vector<T> v; void Copy(const sArray &o) { v=o.v; } };
class sRandom
{
  sU32 kern;
  sU32 Step() { const sU32 a = 1103515245; const sU32 c = 12345; kern = a*kern+c; return kern & 0x7fffffff; }
public:
  sRandom() { Seed(0); }
  sRandom(sU32 seed) { Seed(seed); }
  void Init() { Seed(0); }
  void Seed(sU32 seed)
  {
    kern = seed+seed*17+seed*121+(seed*121/17); Int32();
    kern ^= seed+seed*17+seed*121+(seed*121/17); Int32();
    kern ^= seed+seed*17+seed*121+(seed*121/17); Int32();
    kern ^= seed+seed*17+seed*121+(seed*121/17); Int32();
  }
  sU32 Int32() { sU32 r0,r1; r0 = Step(); r1 = Step(); return r0 ^ ((r1<<16) | (r1>>16)); }
  sInt Int(sInt max_) { sU32 max = sU32(max_-1); sU32 mask = sMakeMask(max); sU32 v; do { v = Int32()&mask; } while(v>max); return v; }
  sInt Int16() { return Step()&0xffff; }
  sF32 Float(sF32 max) { return (0x7fffffff & Int32())*max/(0x8000*65536.0f); }
  sF32 FloatSigned(sF32 max) { return Float(2.0f*max)-max; }
};
class sRandomMT
{
  enum Enums { Count = 624, Period = 397, };
  sU32 State[Count];
  sInt Index;
  static sU32 mtwist(sU32 m,sU32 s0,sU32 s1) { return m ^ ((s0&0x80000000)|(s1&0x7fffffff)) ^ (sU32(-sInt(s1&1))&0x9908b0dfUL); }
  void Reload()
  {
    sU32 *p = State;
    for(sInt i=0;i<Count-Period;i++) p[i] = mtwist(p[i+Period],p[i+0],p[i+1]);
    for(sInt i=Count-Period;i<Count-1;i++) p[i] = mtwist(p[i+Period-Count],p[i+0],p[i+1]);
    p[Count-1] = mtwist(p[Period-1],p[Count-1],State[0]);
  }
  sU32 Step()
  {
    if(Index==Count) { Reload(); Index = 0; }
    sU32 v = State[Index++];
    v ^= (v>>11); v ^= (v<< 7)&0x9d2c5680UL; v ^= (v<<15)&0xefc60000UL; v ^= (v>>18);
    return v;
  }
public:
  sRandomMT() { Seed(0); }
  sRandomMT(sU32 seed) { Seed(seed); }
  void Init() { Seed(0); }
  void Seed(sU32 seed) { for(sInt i=0;i<Count;i++) { State[i] = seed; seed = 1812433253UL*(seed^(seed>>30)+i); } Index = Count; }
  sInt Int(sInt max_) { sU32 max = sU32(max_-1); sU32 mask = sMakeMask(max); sU32 v; do { v = Step()&mask; } while(v>max); return v; }
  sInt Int16() { return Step()&0xffff; }
  sU32 Int32() { return Step(); }
  sF32 Float(sF32 max) { return Step()*max/(65536.0f*65536.0f); }
  sF32 FloatSigned(sF32 max) { return Float(2.0f*max)-max; }
};
inline void sHermite(const sF32 x1, sF32 &c0, sF32 &c1, sF32 &c2, sF32 &c3)
{
  sF32 x2=x1*x1;
  sF32 x3=x2*x1;
  c0 = -0.5f*x3 +      x2 - 0.5f*x1       ;
  c1 =  1.5f*x3 - 2.5f*x2           + 1.0f;
  c2 = -1.5f*x3 + 2.0f*x2 + 0.5f*x1       ;
  c3 =  0.5f*x3 - 0.5f*x2                 ;
}
class sImage; class sImageI16;
#endif
