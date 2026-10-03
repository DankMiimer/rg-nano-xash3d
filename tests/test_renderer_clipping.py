# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
root = Path(__file__).resolve().parents[1]
base = root/'build/tests'
base.mkdir(parents=True, exist_ok=True)
source = (root / 'upstream/xash3d/ref/soft/r_draw.c').read_text()
start = source.index('static void R_DrawStretchPicImplementation(')
end = source.index('/*\n=============\nR_DrawStretchPic', start)
function = source[start:end]
prefix = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdbool.h>
#include <string.h>
typedef uint16_t pixel_t;
typedef unsigned int uint;
typedef bool qboolean;
typedef struct { pixel_t *pixels[1], *alpha_pixels; int width; } image_t;
struct { int width,height,rowbytes,alpha,color,rendermode; pixel_t *buffer,*modmap,*addmap; } vid;
#define COLOR_WHITE 65535
#define kRenderTransAdd 1
#define kRenderScreenFadeModulate 2
#define BLEND_COLOR(a,b) (a)
#define BLEND_ALPHA(a,b,c) (b)
'''
suffix = r'''
static pixel_t guarded[16*16+32], texture[16];
static image_t pic;
static void reset(void){
 for(int i=0;i<16*16+32;i++) guarded[i]=0xBEEF;
 memset(guarded+16,0,16*16*sizeof(pixel_t));
 vid.width=16;vid.height=16;vid.rowbytes=16;vid.alpha=7;
 vid.color=COLOR_WHITE;vid.buffer=guarded+16;
 for(int i=0;i<16;i++)texture[i]=i+1;
 pic.pixels[0]=texture;pic.width=4;
}
static void guards(void){
 for(int i=0;i<16;i++){assert(guarded[i]==0xBEEF);assert(guarded[272+i]==0xBEEF);}
}
int main(void){
 reset();R_DrawStretchPicImplementation(20,2,4,4,0,0,4,4,&pic);guards();
 for(int i=0;i<256;i++)assert(vid.buffer[i]==0);
 reset();R_DrawStretchPicImplementation(2,20,4,4,0,0,4,4,&pic);guards();
 reset();R_DrawStretchPicImplementation(2,2,0,4,0,0,4,4,&pic);guards();
 reset();R_DrawStretchPicImplementation(-2,2,4,4,0,0,4,4,&pic);guards();
 assert(vid.buffer[2*16]==3);assert(vid.buffer[2*16+1]==4);assert(vid.buffer[2*16+2]==0);
 reset();R_DrawStretchPicImplementation(2,-2,4,4,0,0,4,4,&pic);guards();
 assert(vid.buffer[2]==9);assert(vid.buffer[16+2]==13);assert(vid.buffer[32+2]==0);
 reset();R_DrawStretchPicImplementation(14,14,4,4,0,0,4,4,&pic);guards();
 assert(vid.buffer[14*16+14]==1);assert(vid.buffer[15*16+15]==6);
 reset();R_DrawStretchPicImplementation(2,2,4,4,0,0,4,4,&pic);guards();
 assert(vid.buffer[2*16+2]==1);assert(vid.buffer[5*16+5]==16);
 puts("Renderer clipping: off-screen, zero-size, all edges and normal drawing passed.");
}
'''
(base / 'renderer-clipping-test.c').write_text(prefix + function + suffix)
