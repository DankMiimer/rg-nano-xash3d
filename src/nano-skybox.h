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
#ifndef NANO_SKYBOX_H
#define NANO_SKYBOX_H
#include <math.h>

/* GoldSrc/FWGS order: right, back, left, forward, up, down.
 * Directions and image orientation match ref/gl/gl_warp.c's cube tables. */
static inline int NanoSkyboxFaceUV(float x, float y, float z,
                                  int *face, float *u, float *v)
{
    float ax=fabsf(x), ay=fabsf(y), az=fabsf(z), s,t,d;
    if (!isfinite(x) || !isfinite(y) || !isfinite(z)) return 0;
    if (ax>=ay && ax>=az) {
        d=ax; *face=x>=0 ? 0 : 2; s=x>=0 ? -y : y; t=z;
    } else if (ay>=az) {
        d=ay; *face=y>=0 ? 1 : 3; s=y>=0 ? x : -x; t=z;
    } else {
        d=az; *face=z>=0 ? 4 : 5; s=-y; t=z>=0 ? -x : x;
    }
    if (!(d>0)) return 0;
    *u=0.5f+0.5f*(s/d);
    *v=0.5f-0.5f*(t/d);
    return 1;
}
#endif
