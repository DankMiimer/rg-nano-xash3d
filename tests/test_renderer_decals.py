#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the actual software decal function with guarded synthetic surfaces."""
from pathlib import Path
import os, subprocess
root = Path(__file__).resolve().parents[1]
native = Path(os.environ.get('NANO_NATIVE_DIR', str(root/'build/native')))
source = (native/'xash3d/ref/soft/r_surf.c').read_text()
start = source.index('static void R_DrawSurfaceDecals( void )')
end = source.index('/*\n================\nD_CacheSurface', start)
prefix = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
typedef uint16_t pixel_t;
typedef bool qboolean;
typedef float vec3_t[3];
typedef float vec4_t[4];
#define Vec4(a) {(a)[0],(a)[1],(a)[2],(a)[3]}
#define DotProduct(a,b) ((a)[0]*(b)[0]+(a)[1]*(b)[1]+(a)[2]*(b)[2])
#define TRANSPARENT_COLOR 0x349
#define BLEND_ALPHA(a,b,c) (b)
typedef struct { pixel_t *pixels[1], *alpha_pixels; int width,height; } image_t;
typedef struct decal_s { struct decal_s *pnext; int texture; vec3_t position; } decal_t;
typedef struct { vec4_t vecs[2]; } texinfo_t;
typedef struct { decal_t *pdecals; texinfo_t *texinfo; int texturemins[2]; } msurface_t;
static struct { msurface_t *surf; int surfmip,surfwidth,surfheight,rowbytes; void *surfdat; } r_drawsurf;
static image_t image;
static image_t *R_GetTexture(int n) { (void)n; return &image; }
static void R_DecalComputeBasis(msurface_t *s,int n,vec3_t b[3]) {
    (void)s;(void)n;memset(b,0,3*sizeof(vec3_t));b[0][0]=b[1][1]=b[2][2]=1;
}
'''
suffix = r'''
static pixel_t guarded[16*16+32], opaque[16], alpha[16];
static decal_t decal;
static texinfo_t info;
static msurface_t surface;
static void draw(int x,int y,int w,int h,int transparent) {
    for(int i=0;i<288;i++)guarded[i]=0xBEEF;
    memset(guarded+16,0,256*sizeof(pixel_t));
    for(int i=0;i<16;i++){opaque[i]=i+1;alpha[i]=(7<<13)|(i+1);}
    image=(image_t){{opaque},transparent?alpha:NULL,4,4};
    memset(&info,0,sizeof(info));info.vecs[0][0]=w/4.0f;info.vecs[1][1]=h/4.0f;
    surface=(msurface_t){&decal,&info,{-x-w/2,-y-h/2}};
    r_drawsurf.surf=&surface;r_drawsurf.surfmip=0;
    r_drawsurf.surfwidth=r_drawsurf.surfheight=r_drawsurf.rowbytes=16;
    r_drawsurf.surfdat=guarded+16;
    R_DrawSurfaceDecals();
    for(int i=0;i<16;i++){assert(guarded[i]==0xBEEF);assert(guarded[272+i]==0xBEEF);}
    for(int py=0;py<16;py++)for(int px=0;px<16;px++) {
        if(x>=16||y>=16||x+w<=0||y+h<=0)assert(guarded[16+py*16+px]==0);
    }
}
int main(void) {
    // The old function reads outside the texture for this wholly-above decal.
    draw(2,-8,4,4,0);
    draw(2,-4,4,4,1); // Exact top boundary must also be rejected.
    const int sizes[]={1,2,4,8,16};
    for(int a=0;a<5;a++)for(int b=0;b<5;b++)
        for(int y=-24;y<=24;y++)for(int x=-24;x<=24;x++)
            for(int t=0;t<2;t++)draw(x,y,sizes[a],sizes[b],t);
    draw(2,2,4,4,0);
    for(int y=0;y<4;y++)for(int x=0;x<4;x++)
        assert(guarded[16+(y+2)*16+x+2]==opaque[y*4+x]);
    draw(2,-2,4,4,0);
    assert(guarded[16+2]==9);assert(guarded[16+16+2]==13);
    draw(14,14,4,4,0);
    assert(guarded[16+14*16+14]==1);assert(guarded[16+15*16+15]==6);
    puts("Decals: disjoint rectangles, boundaries, partial edges, alpha and normal pixels passed.");
}
'''
build = root/'build/tests'
build.mkdir(parents=True, exist_ok=True)
c = build/'renderer-decals-test.c'
c.write_text(prefix+source[start:end]+suffix)
exe = build/'renderer-decals-test'
subprocess.run([os.environ.get('CC','cc'),'-std=c99','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer',str(c),'-lm','-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
