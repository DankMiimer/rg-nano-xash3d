# SPDX-License-Identifier: GPL-3.0-or-later
"""Check actual counter-only report totals, ordering and output bound."""
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
source=(native/'xash3d/engine/common/zone.c').read_text()
start=source.index('void Mem_NanoReport_f( void )');brace=source.index('{',start);end=brace+1;depth=1
while depth:
    depth+=(source[end]=='{')-(source[end]=='}');end+=1
code=r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef int qboolean;
#define true 1
#define false 0
typedef struct { size_t totalsize,realsize; const char *filename; char name[64]; } mempool_t;
static mempool_t pools[40],*poolchain=pools;
static size_t poolcount;
static FILE *capture;
#undef stderr
#define stderr capture
'''+source[start:end]+r'''
static void check(size_t n,size_t expected,size_t real,size_t lines) {
    poolcount=n;capture=tmpfile();assert(capture);Mem_NanoReport_f();rewind(capture);
    char line[512];size_t gotn,got,gotreal;
    assert(fgets(line,sizeof(line),capture));
    assert(sscanf(line,"nano-memory: pools=%zu bytes=%zu allocated_bytes=%zu",&gotn,&got,&gotreal)==3);
    assert(got==expected && gotreal==real);
    size_t count=0,prev=(size_t)-1;
    while(fgets(line,sizeof(line),capture)) {
        assert(sscanf(line,"nano-memory-pool: bytes=%zu allocated_bytes=%zu",&got,&gotreal)==2);
        assert(got<=prev && got>0);prev=got;count++;
    }
    assert(count==lines);fclose(capture);
}
int main(void) {
    check(0,0,0,0);
    size_t sum=0,real=0;
    for(size_t i=0;i<40;i++) {
        pools[i].filename="source.c";pools[i].totalsize=(i%4)*100;
        pools[i].realsize=pools[i].totalsize+24;
        snprintf(pools[i].name,sizeof(pools[i].name),"pool%zu",i);
        sum+=pools[i].totalsize;real+=pools[i].realsize;
    }
    check(40,sum,real,16); // ties and nonempty count larger than output budget
    capture=tmpfile();Mem_NanoReport_f();rewind(capture);
    char line[512];assert(fgets(line,sizeof(line),capture));
    for(size_t i=3;i<40;i+=4) {
        assert(fgets(line,sizeof(line),capture));char name[64];
        snprintf(name,sizeof(name),"name=pool%zu\n",i);assert(strstr(line,name));
    }
    fclose(capture);
    pools[3].filename=NULL;sum-=300;real-=324;check(40,sum,real,16);
    memset(pools,0,sizeof(pools));pools[0].filename="live";
    pools[0].totalsize=(size_t)1<<30;pools[0].realsize=pools[0].totalsize+24;
    check(1,pools[0].totalsize,pools[0].realsize,1);
    puts("Counter snapshot totals, stable ties, inactive pools and sixteen-line bound pass.");
}
'''
out=root/'build/tests';out.mkdir(parents=True,exist_ok=True)
test=out/'nano-memory-report.c';test.write_text(code)
binary=out/'nano-memory-report'
subprocess.run(['gcc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(test),'-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
