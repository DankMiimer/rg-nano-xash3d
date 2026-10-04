# SPDX-License-Identifier: GPL-3.0-or-later
"""Check actual counter-only report totals, ordering and output bound."""
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
source=(native/'xash3d/engine/common/zone.c').read_text()
def function(signature):
    start=source.index(signature);brace=source.index('{',start);end=brace+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]
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
'''+function('static void Mem_NanoAssets_f( void )')+'\n'+function('void Mem_NanoReport_f( void )')+r'''
static void check(size_t n,size_t expected,size_t real,size_t lines) {
    poolcount=n;capture=tmpfile();assert(capture);Mem_NanoReport_f();rewind(capture);
    char line[512];size_t gotn,got,gotreal;
    assert(fgets(line,sizeof(line),capture));
    assert(sscanf(line,"nano-memory: pools=%zu bytes=%zu allocated_bytes=%zu",&gotn,&got,&gotreal)==3);
    assert(got==expected && gotreal==real);
    size_t active=0;for(size_t i=0;i<n;i++) if(pools[i].filename) active++;
    assert(gotn==active);
    assert(fgets(line,sizeof(line),capture));
    assert(strncmp(line,"nano-memory-assets: ",20)==0);
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
    assert(fgets(line,sizeof(line),capture));
    for(size_t i=3;i<40;i+=4) {
        assert(fgets(line,sizeof(line),capture));char name[64];
        snprintf(name,sizeof(name),"name=pool%zu\n",i);assert(strstr(line,name));
    }
    fclose(capture);
    pools[3].filename=NULL;sum-=300;real-=324;check(40,sum,real,16);
    memset(pools,0,sizeof(pools));pools[0].filename="live";
    pools[0].totalsize=(size_t)1<<30;pools[0].realsize=pools[0].totalsize+24;
    check(1,pools[0].totalsize,pools[0].realsize,1);
    memset(pools,0,sizeof(pools));
    const char *names[]={"^2models/player/urban/urban.mdl^7","models/player.mdl", "models/v_ak47.mdl", "SoundLib Pool", "ref_soft zone", "^2maps/de_dust.bsp^7", "other", "models/ignored.mdl"};
    for(size_t i=0;i<8;i++) {
        strcpy(pools[i].name,names[i]);pools[i].filename="live";
        pools[i].totalsize=(i+1)*100;pools[i].realsize=pools[i].totalsize;
    }
    pools[7].filename=NULL;poolcount=8;
    capture=tmpfile();assert(capture);Mem_NanoAssets_f();rewind(capture);
    assert(fgets(line,sizeof(line),capture));
    size_t models,players;unsigned long long modelbytes,playerbytes,sounds,maps,renderer,other;
    assert(sscanf(line,"nano-memory-assets: model_pools=%zu model_bytes=%llu player_pools=%zu player_model_bytes=%llu sound_pool_bytes=%llu map_pool_bytes=%llu renderer_pool_bytes=%llu other_pool_bytes=%llu",&models,&modelbytes,&players,&playerbytes,&sounds,&maps,&renderer,&other)==8);
    assert(models==3 && modelbytes==600 && players==2 && playerbytes==300);
    assert(sounds==400 && maps==600 && renderer==500 && other==700);
    assert(!fgets(line,sizeof(line),capture));fclose(capture);
    // Aggregates must not truncate at 32 bits on hosts that can represent these pools.
    if(sizeof(size_t)>4) {
        pools[0].totalsize=(size_t)3<<30;pools[1].totalsize=(size_t)3<<30;
        capture=tmpfile();Mem_NanoAssets_f();rewind(capture);assert(fgets(line,sizeof(line),capture));
        assert(sscanf(line,"nano-memory-assets: model_pools=%zu model_bytes=%llu",&models,&modelbytes)==2);
        assert(modelbytes==((unsigned long long)6<<30)+300);fclose(capture);
    }
    puts("Counter totals, asset categories, wide sums, stable ties, inactive pools and bounded output pass.");
}
'''
out=root/'build/tests';out.mkdir(parents=True,exist_ok=True)
test=out/'nano-memory-report.c';test.write_text(code)
binary=out/'nano-memory-report'
subprocess.run(['gcc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(test),'-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
