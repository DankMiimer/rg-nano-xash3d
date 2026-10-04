# SPDX-License-Identifier: GPL-3.0-or-later
"""Differential pixel checks and ownership checks on actual renderer functions."""
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
source=(native/'xash3d/ref/soft/r_image.c').read_text()
baseline=subprocess.check_output(['git','-C',str(native/'xash3d'),'show','HEAD:ref/soft/r_image.c'],text=True)
def function(text,name):
    start=text.index(name);start=text.rfind('\n',0,start)+1
    brace=text.index('{',start);end=brace+1;depth=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]
code=r'''
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "nano-texture-share.h"
typedef unsigned char byte;
typedef unsigned int uint;
typedef uint16_t pixel_t;
typedef unsigned int texFlags_t;
typedef int qboolean;
typedef float vec3_t[3];
#define true 1
#define false 0
#define BIT(n) (1u<<(n))
#define MASK(n) (BIT(n)-1)
#define MOVE_BIT(v,from,to) ((((v)>>(from))&1u)<<(to))
#define Q_max(a,b) ((a)>(b)?(a):(b))
#define ALIGN(x,n) (((x)+(n)-1)&~((n)-1))
#define FBitSet(v,f) ((v)&(f))
#define SetBits(v,f) ((v)|=(f))
#define ClearBits(v,f) ((v)&=~(f))
#define Assert assert
#define ASSERT assert
#define S_ERROR ""
#define TF_NORMALMAP BIT(0)
#define TF_HAS_ALPHA BIT(1)
#define TF_NOMIPMAP BIT(2)
#define TF_CLAMP BIT(3)
#define TF_IMAGE (TF_NOMIPMAP|TF_CLAMP)
#define TF_FORCE_COLOR BIT(4)
#define TF_KEEP_SOURCE BIT(5)
#define TF_IMG_UPLOADED BIT(6)
#define TF_HAS_LUMA BIT(7)
#define TF_QUAKEPAL BIT(8)
#define TF_MAKELUMA BIT(9)
#define TF_LUMINANCE BIT(10)
#define TF_ALPHACONTRAST BIT(11)
#define TF_SKYSIDE BIT(12)
#define IMAGE_ONEBIT_ALPHA BIT(0)
#define IMAGE_HAS_ALPHA BIT(1)
#define IMAGE_HAS_COLOR BIT(2)
#define IMAGE_HAS_LUMA BIT(3)
#define IMAGE_QUAKEPAL BIT(4)
#define IMAGE_MAKE_LUMA BIT(5)
#define IMAGE_FORCE_RGBA BIT(6)
#define PF_INDEXED_24 1
#define PF_INDEXED_32 2
#define TRANSPARENT_COLOR 0x0349
#define MAKE_SIGNED(x) (((float)(x)-128.0f)/127.0f)
#define VectorSet(v,x,y,z) ((v)[0]=(x),(v)[1]=(y),(v)[2]=(z))
static float VectorNormalizeLength(vec3_t v) {
    float n=sqrtf(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);
    if(n) for(int i=0;i<3;i++) v[i]/=n;
    return n;
}
typedef struct { int width,height,depth,type,numMips; unsigned flags; byte fogParams[4]; byte *buffer; } rgbdata_t;
typedef struct image_s { unsigned flags; byte fogParams[4]; int width,height,depth,srcWidth,srcHeight,numMips; size_t size; pixel_t *pixels[4],*alpha_pixels; rgbdata_t *original; char name[64]; unsigned hashValue; struct image_s *nextHash; } image_t;
static image_t *r_imagesHashTable[8];
static struct { int value; } sw_noalphabrushes={0};
static size_t liveBytes,liveBlocks;
typedef struct { size_t size; } Allocation;
static void *TestAlloc(int pool,size_t size) {
    (void)pool; Allocation *h=calloc(1,sizeof(*h)+size); assert(h);
    h->size=size;liveBytes+=size;liveBlocks++;return h+1;
}
static void TestFree(void *p) {
    assert(p);Allocation *h=(Allocation*)p-1;
    liveBytes-=h->size;liveBlocks--;free(h);
}
#define Mem_Calloc TestAlloc
#define Mem_Free TestFree
static int r_temppool;
static void *ShareAlloc(size_t n) { return TestAlloc(0,n); }
static NanoTextureShare nanoTextureShare={.alloc=ShareAlloc,.free=TestFree};
static rgbdata_t *CopyImage(rgbdata_t *p) { rgbdata_t *c=malloc(sizeof(*c));*c=*p;return c; }
static void FreeImage(rgbdata_t *p) { free(p); }
static void Console(const char *f,...) { (void)f;assert(!"Unexpected texture deletion warning"); }
static struct { rgbdata_t *(*FS_CopyImage)(rgbdata_t*); void (*FS_FreeImage)(rgbdata_t*); void (*Con_Printf)(const char*,...); } gEngfuncs={CopyImage,FreeImage,Console};
static int ImageCompressed(int type) { (void)type;return 0; }
static byte *GL_ResampleTexture(byte *p,int a,int b,int c,int d,int normal) {
    (void)p;(void)a;(void)b;(void)c;(void)d;(void)normal;assert(!"Unexpected resample in fixture");return NULL;
}
'''
for name in ('GL_CalcTextureSize(', 'GL_SetTextureDimensions(', 'GL_BuildMipMap('):
    code+='\n'+function(source,name)+'\n'
code+='\n'+function(source,'GL_UploadTexture(')+'\n'
code+='\n'+function(source,'GL_ProcessImage(')+'\n'
code+='\n'+function(source,'GL_DeleteTexture(')+'\n'
code+='\n'+function(baseline,'GL_UploadTexture(').replace('GL_UploadTexture','BaselineUpload')+'\n'
code+=r'''
static void release(image_t *t) {
    if(!t->pixels[0]) { if(t->original) FreeImage(t->original);memset(t,0,sizeof(*t));return; }
    strcpy(t->name,"fixture");t->nextHash=r_imagesHashTable[0];r_imagesHashTable[0]=t;
    GL_DeleteTexture(t);assert(r_imagesHashTable[0]!=t);
}
static void accounting(size_t expected) {
    assert(nanoTextureShare.logical_bytes==expected);
    assert(liveBytes==nanoTextureShare.unique_bytes+nanoTextureShare.buffers*sizeof(NanoTextureBuffer));
    assert(liveBlocks==nanoTextureShare.buffers*2);
    assert(nanoTextureShare.unique_bytes<=expected);
}
static void fill(byte *data,int w,int h,int seed) {
    for(int i=0;i<w*h*4;i++) data[i]=(byte)(i*37+seed);
}
static void compare(int w,int h,unsigned flags) {
    byte a[64*64*4],b[64*64*4];fill(a,w,h,21);memcpy(b,a,sizeof(a));
    rgbdata_t pa={.width=w,.height=h,.depth=1,.buffer=a,.flags=IMAGE_ONEBIT_ALPHA};
    rgbdata_t pb=pa;pb.buffer=b;
    image_t original={.flags=flags},patched={.flags=flags};
    assert(BaselineUpload(&original,&pa));assert(GL_UploadTexture(&patched,&pb));
    int mips=(flags&TF_IMAGE)==TF_IMAGE?1:4;
    assert(patched.numMips==mips);
    for(int j=0;j<mips;j++) {
        size_t bytes=(size_t)Q_max(1,w>>j)*Q_max(1,h>>j)*sizeof(pixel_t);
        assert(!memcmp(original.pixels[j],patched.pixels[j],bytes));
    }
    if(flags&TF_HAS_ALPHA) assert(!memcmp(original.alpha_pixels,patched.alpha_pixels,(size_t)w*h*sizeof(pixel_t)));
    for(int j=mips;j<4;j++) assert(!patched.pixels[j]);
    release(&original);release(&patched);assert(!liveBlocks && !liveBytes);
}
int main(void) {
    compare(32,32,0);compare(31,19,0);compare(1,1,0);
    compare(32,32,TF_HAS_ALPHA);compare(32,32,TF_IMAGE);
    compare(31,19,TF_IMAGE|TF_HAS_ALPHA);compare(1,1,TF_IMAGE);
    compare(32,32,TF_NOMIPMAP); // world/sky-compatible four-level path retained
    compare(32,32,TF_IMAGE|TF_SKYSIDE); // base-only skybox image keeps identical pixels
    image_t t={0};byte data[64*64*4];
    rgbdata_t p={.width=32,.height=32,.depth=1,.buffer=data};
    for(int k=0;k<200;k++) {
        int w=k%2?32:64;int h=k%3?32:64;
        p.width=w;p.height=h;fill(data,w,h,k);
        t.flags=k%2?TF_IMAGE|TF_HAS_ALPHA:0;
        assert(GL_UploadTexture(&t,&p));
        size_t expected=0;
        for(int j=0;j<t.numMips;j++) expected+=(size_t)Q_max(1,w>>j)*Q_max(1,h>>j)*sizeof(pixel_t);
        if(t.flags&TF_HAS_ALPHA) expected+=(size_t)w*h*sizeof(pixel_t);
        accounting(expected);
        assert(t.size==expected-((t.flags&TF_HAS_ALPHA)?(size_t)w*h*sizeof(pixel_t):0));
    }
    p.buffer=NULL;size_t before=liveBytes;
    assert(GL_UploadTexture(&t,&p) && before==liveBytes);
    release(&t);assert(!liveBytes && !liveBlocks);
    // Equal uploads share final pixels/alpha. Changing either owner detaches;
    // the other image remains valid through updates and deletion in either order.
    for(int order=0;order<2;order++) {
        image_t a={.flags=TF_IMAGE|TF_HAS_ALPHA},b=a;
        p.width=p.height=32;p.buffer=data;
        fill(data,32,32,7);assert(GL_UploadTexture(&a,&p));
        fill(data,32,32,7);assert(GL_UploadTexture(&b,&p));
        assert(a.pixels[0]==b.pixels[0] && a.alpha_pixels==b.alpha_pixels);
        pixel_t old[32*32];memcpy(old,b.pixels[0],sizeof(old));
        pixel_t alpha[32*32];memcpy(alpha,b.alpha_pixels,sizeof(alpha));
        accounting(4*sizeof(old));
        fill(data,32,32,91);assert(GL_UploadTexture(&a,&p));
        assert(a.pixels[0]!=b.pixels[0]);
        assert(!memcmp(old,b.pixels[0],sizeof(old)) && !memcmp(alpha,b.alpha_pixels,sizeof(alpha)));
        if(order) { release(&a);assert(!memcmp(old,b.pixels[0],sizeof(old)));release(&b); }
        else { release(&b);assert(a.pixels[0]);release(&a); }
        accounting(0);assert(!liveBytes && !liveBlocks);
    }
    image_t retained={.flags=TF_KEEP_SOURCE};
    GL_ProcessImage(&retained,&p);rgbdata_t *saved=retained.original;assert(saved);
    for(int i=0;i<100;i++) { GL_ProcessImage(&retained,&p);assert(retained.original==saved); }
    release(&retained);
    puts("Texture pixels match baseline; shared uploads detach safely; actual deletion releases ownership.");
}
'''
out=root/'build/tests';out.mkdir(parents=True,exist_ok=True)
test=out/'nano-texture-memory.c';test.write_text(code)
binary=out/'nano-texture-memory'
subprocess.run(['gcc','-std=c99','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(root/'src'),str(test),'-lm','-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
