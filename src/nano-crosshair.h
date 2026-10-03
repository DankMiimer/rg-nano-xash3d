// SPDX-License-Identifier: MIT
// Copyright (c) 2026 rg-nano-xash3d contributors
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files, to deal in the Software
// without restriction, including without limitation the rights to use, copy,
// modify, merge, publish, distribute, sublicense, and/or sell copies, and to
// permit persons to whom the Software is furnished to do so, subject to the
// following conditions: the above copyright notice and this permission notice
// shall be included in all copies or substantial portions of the Software.
// THE SOFTWARE IS PROVIDED AS IS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
#ifndef NANO_CROSSHAIR_H
#define NANO_CROSSHAIR_H
#include <math.h>
struct NanoCrosshairRect { int x, y, w, h; };
static void NanoCrosshairRects(int width, int height, float gap, float length,
    NanoCrosshairRect rects[4])
{
    int cx = width/2, cy = height/2;
    int g = (int)floorf(gap+0.5f), l = (int)floorf(length+0.5f);
    if (g < 3) g = 3;
    if (l < 5) l = 5;
    rects[0] = {cx-g-l, cy, l, 1};
    rects[1] = {cx+g+1, cy, l, 1};
    rects[2] = {cx, cy-g-l, 1, l};
    rects[3] = {cx, cy+g+1, 1, l};
}
#endif
