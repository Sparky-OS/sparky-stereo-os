// Stand-ins for the two werkkzeug4 classes GenBitmap derives from.
#ifndef SHIM_BASIC_HPP
#define SHIM_BASIC_HPP
#include "base/types.hpp"
#define GenBitmapType 0
struct wObject { int Type; virtual ~wObject() {} void AddRef() {} void Release() {} bool IsType(int t) const { return Type == t; } };
struct BitmapAtlasShim { sArray<int> Entries; };
struct BitmapBase : wObject { BitmapAtlasShim Atlas; };
#endif
