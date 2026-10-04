# SPDX-License-Identifier: GPL-3.0-or-later
"""Check the optional experiment's actual snapshot, timing and ready gate."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
lines=(root/'experiments/engine-load-measurement.patch').read_text().splitlines()
start=next(i for i,s in enumerate(lines) if s.startswith('+/* Temporary load measurement'))
end=next(i for i in range(start+1,len(lines)) if lines[i].startswith('--- '))
block='\n'.join(s[1:] for s in lines[start:end] if s.startswith('+'))
code=r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#define Q_strncpy(d,s,n) snprintf(d,n,"%s",s)
static double now;
static double Platform_DoubleTime(void) { return now; }
static FILE *capture;
#undef stderr
#define stderr capture
'''+block+r'''
int main(void) {
    capture=tmpfile();assert(capture);
    nano_load_snapshot_t s=NanoLoadSnapshot();assert(s.valid && s.rss>0 && s.up>0);
    NanoLoadProbeReady();assert(ftell(capture)==0);
    now=1;NanoLoadProbeBegin("save-load");now=1.25;NanoLoadProbeReady();
    long first=ftell(capture);NanoLoadProbeReady();assert(ftell(capture)==first);
    now=2;NanoLoadProbeBegin("map");now=3;NanoLoadProbeBegin("transition");
    now=3.5;NanoLoadProbeReady();assert(!nanoLoadPending && nanoLoadSeq==3);
    rewind(capture);char line[512];int begins=0,ends=0;
    while(fgets(line,sizeof(line),capture)) {
        assert(strlen(line)<sizeof(line)-1);
        if(strstr(line,"nano-load-begin:"))begins++;
        if(strstr(line,"nano-load-ready:")) {
            ends++;assert(strstr(line,"valid=1"));
            assert(strstr(line,ends==1?"seq=1 op=save-load duration_ms=250.000":"seq=3 op=transition duration_ms=500.000"));
        }
    }
    assert(begins==3 && ends==2);fclose(capture);
    puts("Load measurement: live proc parsing, monotonic timing, sequence reset and single-ready records pass.");
}
'''
out=root/'build/tests';out.mkdir(parents=True,exist_ok=True)
p=out/'load-measurement.c';p.write_text(code)
binary=out/'load-measurement'
subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O1','-g','-fsanitize=address,undefined',str(p),'-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
