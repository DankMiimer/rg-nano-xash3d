# SPDX-License-Identifier: GPL-3.0-or-later
"""Check bounded diagnostics with steady frames, stalls, ring rollover and reset."""
from pathlib import Path
import subprocess,os
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
host=(native/'xash3d/engine/common/host.c').read_text(encoding='utf-8')
start=host.index('static qboolean Host_Autosleep(');brace=host.index('{',start);depth=1;end=brace+1
while depth:
    depth+=(host[end]=='{')-(host[end]=='}');end+=1
actual_pacing=host[start:end]
code=r'''
#include <assert.h>
#include "nano-frame-stats.h"
#define MIN_FPS 10
#define MAX_FPS_HARD 1000
#define bound(lo,x,hi) ((x)<(lo)?(lo):((x)>(hi)?(hi):(x)))
typedef int qboolean;
#define false 0
#define true 1
static struct { double value; } nano_frame_sleep={1},host_sleeptime_debug={0};
static struct { double pureframetime; } host={0.020};
static double testClock;
static unsigned long lastSleep;
static double Host_CalcFPS(void) { return 30; }
static int Host_CalcSleep(void) { return 1; }
static int Host_IsDedicated(void) { return 0; }
static double Platform_DoubleTime(void) { return testClock; }
static void Platform_NanoSleep(unsigned long ns) { lastSleep=ns;testClock+=ns/1000000000.0; }
static void Con_NPrintf(int row,const char *format,...) { (void)row;(void)format; }
''' + actual_pacing + r'''
int main(void) {
    testClock=0.020;
    int ready=0;
    for (unsigned i=0;i<32;i++) {
        double before=testClock;lastSleep=0;
        ready=Host_Autosleep(testClock,1);
        assert(lastSleep<=5000000);
        if (ready) break;
        if (before==testClock) testClock+=0.00005; // bounded final spin margin
    }
    assert(ready && testClock>=1.0/30 && testClock<1.0/30+0.0001);
    lastSleep=0;assert(Host_Autosleep(0.040,1) && lastSleep==0);
    assert(!Host_Autosleep(0.010,0.5)); // elapsed/target share the same simulation scale
    nano_frame_sleep.value=0;lastSleep=0;
    assert(Host_Autosleep(0.040,1)); // opt-out retains the original path
    assert(NanoFrameSleepNS(0.010,1.0/30,1)==5000000);
    assert(NanoFrameSleepNS(0.032,1.0/30,1)>1000000);
    assert(NanoFrameSleepNS(0.034,1.0/30,1)==0);
    assert(NanoFrameSleepNS(0,1.0/30,0)==0);
    assert(NanoFrameSleepNS(-1,1.0/30,1)==0);
    assert(NanoFrameSleepNS(0,NAN,1)==0);
    NanoFrameStats s={0};
    NanoFrameSummary empty=NanoFrameSummarize(&s);
    assert(empty.count==0 && empty.fps==0);
    assert(!NanoFrameAdd(&s,10,0.01));
    for (unsigned i=1;i<=150;i++) NanoFrameAdd(&s,10+i/30.0,0.012);
    NanoFrameSummary result=NanoFrameSummarize(&s);
    assert(result.count==150 && fabs(result.fps-30)<1e-8);
    assert(fabs(result.medianMS-1000.0/30)<0.001 && fabs(result.p95MS-result.medianMS)<0.001);
    assert(fabs(result.workMeanMS-12)<0.001 && result.slow50==0);
    NanoFrameAdd(&s,15.2,0.18);
    result=NanoFrameSummarize(&s);
    assert(result.slow50==1 && fabs(result.maxMS-200)<0.001 && result.fps<30);
    assert(result.p95MS<34); // A rare stall is reported as max without inflating p95.
    NanoFrameReset(&s,15.2,1);
    NanoFrameAdd(&s,15.2+1.0/30,0.01);
    assert(s.count==1);
    NanoFrameReset(&s,0,0);
    NanoFrameAdd(&s,1,0.01);
    for (unsigned i=1;i<=1600;i++) NanoFrameAdd(&s,1+i/120.0,0.004);
    result=NanoFrameSummarize(&s);
    assert(s.stored==NANO_FRAME_SAMPLES && s.count==1600 && fabs(result.fps-120)<1e-7);
    assert(fabs(result.p95MS-1000.0/120)<0.001);
    unsigned count=s.count;
    assert(!NanoFrameAdd(&s,NAN,0.1) && s.count==count);
    assert(!NanoFrameAdd(&s,50,-1) && s.count==count);
    NanoFrameAdd(&s,0.5,0.01); // Clock discontinuity starts a fresh window.
    assert(s.count==0 && s.havePrevious);
    return 0;
}
'''
path=root/'build/test-nano-frame-stats.c';path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(code,encoding='utf-8');exe=path.with_suffix('')
subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(root/'src'),str(path),'-lm','-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
print('Actual frame wait and diagnostics: bounded sleeps, deadline, scaling, opt-out, stalls and ring passed.')
