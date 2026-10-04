/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include "nano-texture-share.h"

static size_t live_bytes, live_blocks;
static int fail_metadata;
static void *allocate(size_t size)
{
    size_t *h;
    if (fail_metadata && size == sizeof(NanoTextureBuffer)) return NULL;
    h = malloc(sizeof(*h) + size);
    assert(h);
    *h = size; live_bytes += size; live_blocks++;
    return h + 1;
}
static void release(void *data)
{
    size_t *h = (size_t *)data - 1;
    live_bytes -= *h; live_blocks--; free(h);
}
static uint32_t collision(const void *data, size_t size)
{
    (void)data; (void)size; return 7;
}
static void *copy(const void *data, size_t size)
{
    void *p = allocate(size); memcpy(p, data, size); return p;
}
static void empty(NanoTextureShare *s)
{
    assert(!s->buffers && !s->references && !s->logical_bytes && !s->unique_bytes);
    assert(!live_bytes && !live_blocks);
    for (int i=0;i<NANO_TEXTURE_SHARE_BUCKETS;i++) assert(!s->by_hash[i] && !s->by_pointer[i]);
}
int main(void)
{
    NanoTextureShare s = {.alloc=allocate,.free=release,.hash=collision};
    const char a[]="matching pixels", b[]="different bytes";
    assert(sizeof(a)==sizeof(b));
    void *p=NanoTextureIntern(&s,copy(a,sizeof(a)),sizeof(a));
    void *q=NanoTextureIntern(&s,copy(a,sizeof(a)),sizeof(a));
    void *r=NanoTextureIntern(&s,copy(b,sizeof(b)),sizeof(b));
    assert(p==q && p!=r && s.buffers==2 && s.references==3);
    NanoTextureRelease(&s,p);assert(!memcmp(q,a,sizeof(a)));
    NanoTextureRelease(&s,r);NanoTextureRelease(&s,q);empty(&s);
    fail_metadata=1;
    p=NanoTextureIntern(&s,copy(a,sizeof(a)),sizeof(a));
    assert(!s.buffers);NanoTextureRelease(&s,p);fail_metadata=0;empty(&s);
    NanoTextureRelease(&s,NULL);
    // Deterministic randomized lifetime/size/content changes under forced
    // collisions. Repeated empty registries model shutdown/reinitialization.
    unsigned rng=91;
    for(int cycle=0;cycle<100;cycle++) {
        void *owners[64]={0};size_t sizes[64]={0};unsigned char values[64]={0};
        for(int k=0;k<1000;k++) {
            rng=rng*1664525u+1013904223u;unsigned i=rng%64;
            NanoTextureRelease(&s,owners[i]);owners[i]=NULL;sizes[i]=0;
            rng=rng*1664525u+1013904223u;
            if(rng&8) {
                sizes[i]=1+(rng%127);values[i]=(rng>>16)%8;
                unsigned char *fresh=allocate(sizes[i]);memset(fresh,values[i],sizes[i]);
                owners[i]=NanoTextureIntern(&s,fresh,sizes[i]);
            }
            size_t logical=0,refs=0;
            for(int j=0;j<64;j++) if(owners[j]) {
                logical+=sizes[j];refs++;
                for(size_t n=0;n<sizes[j];n++) assert(((unsigned char*)owners[j])[n]==values[j]);
            }
            assert(s.logical_bytes==logical && s.references==refs && s.unique_bytes<=logical);
            assert(live_bytes==s.unique_bytes+s.buffers*sizeof(NanoTextureBuffer));
        }
        for(int i=0;i<64;i++) NanoTextureRelease(&s,owners[i]);
        empty(&s);
    }
    // Also exercise the production hash rather than only the collision seam.
    s.hash=NULL;p=NanoTextureIntern(&s,copy(a,sizeof(a)),sizeof(a));
    q=NanoTextureIntern(&s,copy(a,sizeof(a)),sizeof(a));assert(p==q);
    NanoTextureRelease(&s,q);NanoTextureRelease(&s,p);empty(&s);
    puts("Texture sharing: byte equality, collisions, ownership, allocation failure and repeated lifetimes pass.");
}
