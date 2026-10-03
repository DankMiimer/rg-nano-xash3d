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
#ifndef NANO_HUD_TRANSFORM_H
#define NANO_HUD_TRANSFORM_H
#include <math.h>
static void NanoHudRect(float *x, float *y, float *w, float *h,
    float canvasW, float canvasH, float scale, float anchorX, float anchorY)
{
    if (!(scale >= 0.25f && scale <= 4.0f)) scale = 1.0f;
    if (!(anchorX >= 0.0f && anchorX <= 1.0f)) anchorX = 0.0f;
    if (!(anchorY >= 0.0f && anchorY <= 1.0f)) anchorY = 0.0f;
    float ax = canvasW * anchorX, ay = canvasH * anchorY;
    float nx = ax + (*x - ax) * scale, ny = ay + (*y - ay) * scale;
    float ex = nx + *w * scale, ey = ny + *h * scale;
    float rx = floorf(nx + 0.5f), ry = floorf(ny + 0.5f);
    float rw = floorf(ex + 0.5f) - rx, rh = floorf(ey + 0.5f) - ry;
    if (*w > 0.0f && rw < 1.0f) rw = 1.0f;
    if (*h > 0.0f && rh < 1.0f) rh = 1.0f;
    *x = rx; *y = ry; *w = rw; *h = rh;
}
#endif
