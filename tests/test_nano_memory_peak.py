# SPDX-License-Identifier: GPL-3.0-or-later
"""Check actual peak hooks, interval seeding/reset and disabled behavior."""
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
source=(native/'xash3d/engine/common/zone.c').read_text()
start=source.index('/* Nano peak interval:')
end=source.index('/* End Nano peak interval. */',start)
block=source[start:end]
def function(name):
    start=source.index(name);start=source.rfind('\n',0,start)+1
    brace=source.index('{',start);end=brace+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]
code=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef int qboolean;
#define true 1
#define false 0
#define Q_strncpy(dst,src,n) snprintf(dst,n,"%s",src)
typedef struct { size_t totalsize,realsize; const char *filename; char name[64]; } mempool_t;
static mempool_t pools[3],*poolchain=pools;
static size_t poolcount=3;
static FILE *capture;
#undef stderr
#define stderr capture
'''+block+'\n'+function('Mem_PoolAdd(')+'\n'+function('Mem_PoolSubtract(')+r'''
static uint64_t live(void) {
    uint64_t n=0;for(int i=0;i<3;i++) if(pools[i].filename) n+=pools[i].totalsize;return n;
}
int main(void) {
    capture=tmpfile();assert(capture);
    pools[0].filename="live";strcpy(pools[0].name,"renderer");
    pools[1].filename="live";strcpy(pools[1].name,"decoder");
    pools[2].totalsize=999; // inactive pool must be excluded
    Mem_PoolAdd(&pools[0],100,125);assert(!nanoMemPeak.current);
    Mem_NanoBegin_f();assert(nanoMemPeak.start==100 && nanoMemPeak.peak==100);
    Mem_PoolAdd(&pools[1],4096,4121);assert(nanoMemPeak.peak==4196);
    Mem_PoolSubtract(&pools[1],4096,4121);assert(nanoMemPeak.current==100);
    Mem_PoolAdd(&pools[0],300,300); // realloc growth delta
    assert(nanoMemPeak.current==400 && nanoMemPeak.peak==4196);
    Mem_PoolSubtract(&pools[0],150,150); // realloc shrink
    Mem_PoolSubtract(&pools[0],50,75);Mem_PoolAdd(&pools[1],50,75); // migration
    assert(nanoMemPeak.current==live() && nanoMemPeak.peak==4196);
    assert(nanoMemPeak.largestGrowth==4096 && !strcmp(nanoMemPeak.largestPool,"decoder"));
    Mem_NanoEnd_f();assert(!nanoMemPeak.enabled);
    uint64_t old=nanoMemPeak.current;
    Mem_PoolAdd(&pools[0],1024,1049);assert(nanoMemPeak.current==old);
    Mem_NanoBegin_f();assert(nanoMemPeak.current==live() && nanoMemPeak.peak==live());
    assert(!nanoMemPeak.largestGrowth && !nanoMemPeak.grows);
    unsigned rng=42;uint64_t expectedPeak=live();
    for(int i=0;i<10000;i++) {
        rng=rng*1664525u+1013904223u;size_t delta=rng%500;
        int p=(rng>>16)%2;
        if((rng&8) && pools[p].totalsize>=delta) Mem_PoolSubtract(&pools[p],delta,delta);
        else Mem_PoolAdd(&pools[p],delta,delta);
        uint64_t total=live();if(total>expectedPeak) expectedPeak=total;
        assert(nanoMemPeak.current==total && nanoMemPeak.peak==expectedPeak);
    }
    // Seeding and reports retain totals beyond 32 bits on a 64-bit host.
    pools[0].totalsize=(uint64_t)1<<33;Mem_NanoBegin_f();assert(nanoMemPeak.start==live());
    Mem_NanoEnd_f();rewind(capture);
    char line[512];int begins=0,ends=0;
    while(fgets(line,sizeof(line),capture)) {
        assert(strlen(line)<sizeof(line)-1);
        begins+=strstr(line,"nano-memory-begin:")!=NULL;
        ends+=strstr(line,"nano-memory-peak:")!=NULL;
    }
    assert(begins==3 && ends==2);fclose(capture);
    puts("Memory peak intervals: live seeding, allocation/free/growth/shrink/migration, resets and disabled hooks pass.");
}
'''
out=root/'build/tests';out.mkdir(parents=True,exist_ok=True)
test=out/'nano-memory-peak.c';test.write_text(code)
binary=out/'nano-memory-peak'
subprocess.run(['gcc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(test),'-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
