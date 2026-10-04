# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise actual pool allocation/free/realloc code with instrumented libc."""
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
source=(native/'xash3d/engine/common/zone.c').read_text()
block=source[source.index('#define MEMHEADER_SENTINEL_BIG'):source.index('static poolhandle_t Mem_InitPool')]
pre=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <setjmp.h>
#include <limits.h>
typedef unsigned char byte;
typedef unsigned int uint, poolhandle_t;
typedef int qboolean;
#define true 1
#define false 0
#define MEM_SMALL_ALLOC_OPT 1
#define FBitSet(n,b) ((n)&(b))
#define unlikely(n) (n)
#define likely(n) (n)
#define MAX_OSPATH 1024
#define COM_StringEmptyOrNULL(s) (!(s) || !(s)[0])
#define Q_min(a,b) ((a)<(b)?(a):(b))
#define Q_strncpy(d,s,n) snprintf(d,n,"%s",s)
#define STATIC_CHECK_SIZEOF(t,a,b) _Static_assert(sizeof(t)==(sizeof(void*)==4?(a):(b)),"header size")
static jmp_buf errorJump;
static int expectError, errors, failNext;
static size_t mallocCalls, callocCalls, clearBytes, liveBlocks, swapCalls;
static void Sys_Error(const char *fmt, ...) {
    (void)fmt;errors++;assert(expectError);longjmp(errorJump,1);
}
static const char *Q_memprint(size_t n) { (void)n;return "bytes"; }
static void *test_malloc(size_t n) {
    mallocCalls++;if(failNext){failNext=0;return NULL;}
    void *p=malloc(n);if(p){memset(p,0xa7,n);liveBlocks++;}return p;
}
static void *test_calloc(size_t count,size_t n) {
    callocCalls++;if(failNext){failNext=0;return NULL;}
    void *p=calloc(count,n);if(p)liveBlocks++;return p;
}
static void test_free(void *p) { if(p){assert(liveBlocks);liveBlocks--;}free(p); }
static void *test_realloc(void *p,size_t n) {
    if(failNext){failNext=0;return NULL;}
    int had=p!=NULL;void *q=realloc(p,n);if(q && !had)liveBlocks++;return q;
}
static void *test_memset(void *p,int c,size_t n) {if(!c)clearBytes+=n;return memset(p,c,n);}
#ifdef XASH_CUSTOM_SWAP
static void *SWAP_Malloc(size_t n) {swapCalls++;return test_malloc(n);}
static void SWAP_Free(void *p) {test_free(p);}
#endif
#define malloc test_malloc
#define calloc test_calloc
#define realloc test_realloc
#define free test_free
#define memset test_memset
'''
post=r'''
static void verify_zero(const byte *p,size_t n) { for(size_t i=0;i<n;i++)assert(p[i]==0); }
static void verify_dirty(const byte *p,size_t n) {for(size_t i=0;i<n;i++)assert(p[i]==0xa7);}
static void totals(size_t a,size_t b) {
    assert(poolchain[0].totalsize==a && poolchain[1].totalsize==b);
    assert(poolchain[0].realsize==a+(poolchain[0].chain?sizeof(memheader_t)+1:0)+(poolchain[0].chain_small?sizeof(memheader_small_t)+1:0));
}
static void allocation(size_t n,qboolean clear) {
    size_t oldCalloc=callocCalls,oldClear=clearBytes;
    byte *p=_Mem_Alloc(1,n,clear,"test",17);assert(p);
    if(clear)verify_zero(p,n);else verify_dirty(p,n);
    qboolean lazy=false;
#ifndef XASH_CUSTOM_SWAP
    lazy=clear && n>=256*1024;
#endif
    assert(callocCalls==oldCalloc+(lazy?1:0));
    assert(clearBytes==oldClear+(clear && !lazy?n:0));
    assert(Mem_ReadSentinel(p)==(n<=MEM_SMALL_MAX?MEMHEADER_SENTINEL_SMALL:MEMHEADER_SENTINEL_BIG));
    assert(p[n]==MEMHEADER_SENTINEL2);totals(n,0);
    memset(p,0xd3,n);_Mem_Free(p,"test",18);totals(0,0);assert(liveBlocks==0);
}
int main(void) {
    mempool_t pools[2]={0};poolchain=pools;poolcount=2;
    for(int i=0;i<2;i++){pools[i].filename="test";strcpy(pools[i].name,"test pool");}
    pools[0].flags=MEM_SMALL_ALLOC_OPT;
    size_t sizes[]={1,255,256,256*1024-1,256*1024,256*1024+1,4*1024*1024+1396};
    for(int round=0;round<3;round++)for(size_t i=0;i<sizeof(sizes)/sizeof(*sizes);i++) {
        allocation(sizes[i],true);allocation(sizes[i],false);
    }
    // Allocation failures must leave lists and accounting untouched.
    for(size_t i=0;i<sizeof(sizes)/sizeof(*sizes);i++) {
        expectError=1;failNext=1;
        if(!setjmp(errorJump)){_Mem_Alloc(1,sizes[i],true,"failure",1);assert(0);}
        expectError=0;totals(0,0);assert(!poolchain[0].chain && !poolchain[0].chain_small && !liveBlocks);
    }
    // Header/tail sentinels remain checked, including the calloc path.
    byte *p=_Mem_Alloc(1,256*1024,true,"sentinel",1);
    p[256*1024]=0;expectError=1;
    if(!setjmp(errorJump)){_Mem_Free(p,"corrupt",1);assert(0);}
    expectError=0;assert(liveBlocks==1);p[256*1024]=MEMHEADER_SENTINEL2;
    memheader_t *h=(memheader_t *)(p-sizeof(memheader_t));h->sentinel1=0;expectError=1;
    if(!setjmp(errorJump)){_Mem_Free(p,"corrupt",1);assert(0);}
    expectError=0;h->sentinel1=MEMHEADER_SENTINEL_BIG;_Mem_Free(p,"restored",1);
    // Mixed owners must retain links when a large cleared allocation fails.
    p=_Mem_Alloc(1,300*1024,true,"linked",1);
    byte *q=_Mem_Alloc(1,42,false,"linked",1);
    expectError=1;failNext=1;
    if(!setjmp(errorJump)){_Mem_Alloc(1,400*1024,true,"failure",1);assert(0);}
    expectError=0;assert(pools[0].totalsize==300*1024+42);
    verify_zero(p,300*1024);verify_dirty(q,42);
    _Mem_Free(p,"linked",1);_Mem_Free(q,"linked",1);assert(!liveBlocks);
#ifndef XASH_CUSTOM_SWAP
    // Real libc dirty-block reuse: full payload zero checks, not just endpoints.
    for(int i=0;i<10;i++) {
        p=_Mem_Alloc(1,400*1024,false,"reuse",1);memset(p,0xff,400*1024);_Mem_Free(p,"reuse",1);
        p=_Mem_Alloc(1,400*1024,true,"reuse",1);verify_zero(p,400*1024);_Mem_Free(p,"reuse",1);
    }
    // Promotion, growth/shrink, chain relocation and pool migration.
    p=_Mem_Alloc(1,100,true,"grow",1);memset(p,0x55,100);
    p=_Mem_Realloc(1,p,256*1024+1,true,"grow",1);
    for(size_t i=0;i<100;i++)assert(p[i]==0x55);
    verify_zero(p+100,256*1024+1-100);
    p=_Mem_Realloc(2,p,512*1024,true,"migrate",1);assert(!pools[0].totalsize && pools[1].totalsize==512*1024);
    for(size_t i=0;i<100;i++)assert(p[i]==0x55);
    verify_zero(p+100,512*1024-100);
    p=_Mem_Realloc(2,p,50,true,"shrink",1);for(int i=0;i<50;i++)assert(p[i]==0x55);
    byte *same=_Mem_Realloc(2,p,0,true,"zero",1);assert(same==p);
    expectError=1;failNext=1;
    if(!setjmp(errorJump)){_Mem_Realloc(2,p,100,true,"failure",1);assert(0);}
    expectError=0;assert(pools[1].totalsize==50 && p[50]==MEMHEADER_SENTINEL2);
    _Mem_Free(p,"done",1);assert(!pools[1].totalsize && !pools[1].chain);
#else
    assert(!callocCalls && swapCalls==mallocCalls);
#endif
    (void)swapCalls;
    assert(!liveBlocks && !pools[0].totalsize && !pools[1].totalsize);
    puts("Demand-zero pool allocation: zero/dirty data, threshold, failures, sentinels, ownership and allocator paths pass.");
}
'''
out=root/'build/tests';out.mkdir(parents=True,exist_ok=True)
swap=out/'platform/swap';swap.mkdir(parents=True,exist_ok=True)
(swap/'swap.h').write_text('/* Allocator stubs declared by the test prelude. */\n')
test=out/'nano-demand-zero.c';test.write_text(pre+block+post)
for custom in (False,True):
    binary=out/('nano-demand-zero-swap' if custom else 'nano-demand-zero')
    cmd=['gcc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-clobbered','-fsanitize=address,undefined','-I'+str(out)]
    if custom:cmd+=['-DXASH_CUSTOM_SWAP','-Wno-unused-function']
    subprocess.run(cmd+[str(test),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
