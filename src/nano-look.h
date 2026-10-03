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
#ifndef NANO_LOOK_H
#define NANO_LOOK_H
struct NanoLookState { int direction; float held; };
static float NanoLookRate(struct NanoLookState *s, int direction, int pressed,
    float dt, float delay, float ramp, float low, float high, int fast)
{
    if (!(low > 0.0f && low < 720.0f)) low = 70.0f;
    if (!(high >= low && high < 720.0f)) high = low;
    if (!(delay >= 0.0f && delay <= 2.0f)) delay = 0.15f;
    if (!(ramp >= 0.05f && ramp <= 5.0f)) ramp = 0.75f;
    if (!direction || fast || !(dt >= 0.0f && dt <= 0.25f)) {
        s->direction = 0; s->held = 0.0f;
        return fast ? high : low;
    }
    if (direction != s->direction || pressed) {
        s->direction = direction; s->held = 0.0f;
    } else {
        s->held += dt;
        if (s->held > delay + ramp) s->held = delay + ramp;
    }
    float t = (s->held - delay) / ramp;
    if (t < 0.0f) t = 0.0f;
    if (t > 1.0f) t = 1.0f;
    t = t * t * (3.0f - 2.0f * t);
    return low + (high - low) * t;
}
#endif
