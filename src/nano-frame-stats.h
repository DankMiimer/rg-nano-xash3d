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
#ifndef NANO_FRAME_STATS_H
#define NANO_FRAME_STATS_H
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define NANO_FRAME_SAMPLES 512
typedef struct {
    double previous, started, sum, workSum, maximum;
    unsigned count, stored, slow50;
    int havePrevious;
    float intervals[NANO_FRAME_SAMPLES];
} NanoFrameStats;
typedef struct { double fps, medianMS, p95MS, maxMS, workMeanMS; unsigned count, slow50; } NanoFrameSummary;
static void NanoFrameReset(NanoFrameStats *s, double now, int preservePrevious)
{
    memset(s, 0, sizeof(*s));
    s->previous=now; s->started=now; s->havePrevious=preservePrevious;
}
static int NanoFrameAdd(NanoFrameStats *s, double now, double workSeconds)
{
    if (!isfinite(now) || !isfinite(workSeconds) || workSeconds<0) return 0;
    if (!s->havePrevious || now<=s->previous) { NanoFrameReset(s,now,1); return 0; }
    double interval=now-s->previous;
    s->previous=now;
    s->sum+=interval; s->workSum+=workSeconds;
    if (interval>s->maximum) s->maximum=interval;
    if (interval>0.050) ++s->slow50;
    s->intervals[s->count%NANO_FRAME_SAMPLES]=(float)interval;
    ++s->count;
    if (s->stored<NANO_FRAME_SAMPLES) ++s->stored;
    return now-s->started>=5.0;
}
static int NanoFrameCompare(const void *a, const void *b)
{
    float x=*(const float *)a,y=*(const float *)b;
    return (x>y)-(x<y);
}
static NanoFrameSummary NanoFrameSummarize(const NanoFrameStats *s)
{
    NanoFrameSummary result={0};
    float sorted[NANO_FRAME_SAMPLES];
    if (!s->count || !s->stored || !(s->sum>0)) return result;
    memcpy(sorted,s->intervals,s->stored*sizeof(float));
    qsort(sorted,s->stored,sizeof(float),NanoFrameCompare);
    result.count=s->count; result.slow50=s->slow50;
    result.fps=s->count/s->sum;
    result.medianMS=sorted[(s->stored-1)/2]*1000;
    result.p95MS=sorted[(unsigned)ceil(s->stored*0.95)-1]*1000;
    result.maxMS=s->maximum*1000;
    result.workMeanMS=s->workSum/s->count*1000;
    return result;
}
// Sleep in short chunks, leaving a small margin for the next frame deadline.
// This is wall time only; it does not change the simulation time step.
static unsigned long NanoFrameSleepNS(double elapsed, double target, double scale)
{
    if (!isfinite(elapsed) || !isfinite(target) || !isfinite(scale) ||
        elapsed<0 || target<=0 || scale<=0) return 0;
    double remaining=target*scale-elapsed;
    if (!isfinite(remaining) || remaining<=0.0002) return 0;
    remaining-=0.0002;
    if (remaining>0.005) remaining=0.005;
    return (unsigned long)(remaining*1000000000.0);
}
#endif
