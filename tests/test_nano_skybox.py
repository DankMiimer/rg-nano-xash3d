#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check sky projection against upstream GL orientation and actual span/lifetime code."""
from pathlib import Path
import os,re,subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
source=native/'xash3d/ref'
def function(text,name):
    start=text.index(name);end=text.index('{',start)+1;depth=1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return text[start:end]+'\n'
gl=(source/'gl/gl_warp.c').read_text()
table=re.search(r'st_to_vec\[SKYBOX_MAX_SIDES\]\[3\]\s*=\s*(\{.*?\n\});',gl,re.S)[1]
table=re.sub(r'//[^\n]*','',table)
code=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>
#include "nano-skybox.h"
#define GAME_EXPORT
#define SKYBOX_MAX_SIDES 6
#define MAX_TEXTURES 8
#define Q_max(a,b) ((a)>(b)?(a):(b))
#define Q_min(a,b) ((a)<(b)?(a):(b))
#define bound(a,b,c) Q_max(a,Q_min(b,c))
typedef uint16_t pixel_t;
typedef struct { pixel_t *pixels[1]; int width,height; } image_t;
typedef struct span_s { int u,v,count; struct span_s *pnext; } espan_t;
static struct { int skyboxTextures[6]; } tr;
static struct { int width,height; } vid={16,16};
static struct { float base_vpn[3],base_vright[3],base_vup[3]; } RI;
static struct { int value; } sw_clearcolor={0x1234};
static image_t images[8];
static pixel_t pixels[6][15],guarded[352],*d_viewbuffer=guarded+16;
static int r_screenwidth=20;
static float xcenter=7.5f,ycenter=7.5f,xscaleinv=0.125f,yscaleinv=0.125f;
static image_t *R_GetTexture(int n) { assert(n>0&&n<8);return &images[n]; }
static int frees;
static void GL_FreeTexture(int n) { if(n){assert(n>0&&n<8);frees++;} }
'''
code+=function((source/'soft/r_edge.c').read_text(),'static void D_DrawSkySpans(')
code+=function((source/'soft/r_context.c').read_text(),'static void GAME_EXPORT R_SetupSky(')
code+='static const int oracle[6][3]='+table+';\n'
code+=r'''
static const int order[6]={0,2,1,3,4,5};
static void projection(void) {
    float uv[2];int face;
    assert(!NanoSkyboxFaceUV(0,0,0,&face,&uv[0],&uv[1]));
    assert(!NanoSkyboxFaceUV(NAN,1,0,&face,&uv[0],&uv[1]));
    assert(!NanoSkyboxFaceUV(1,INFINITY,0,&face,&uv[0],&uv[1]));
    for(int axis=0;axis<6;axis++)for(int si=-7;si<=7;si++)for(int ti=-7;ti<=7;ti++)
        for(int scale=0;scale<3;scale++) {
            float factor=scale==0?0.01f:scale==1?1:10000;
            float b[3]={si/8.0f*factor,ti/8.0f*factor,factor},d[3];
            for(int j=0;j<3;j++){int k=oracle[axis][j];d[j]=k<0?-b[-k-1]:b[k-1];}
            assert(NanoSkyboxFaceUV(d[0],d[1],d[2],&face,&uv[0],&uv[1]));
            assert(face==order[axis]);
            assert(fabsf(uv[0]-(si/8.0f+1)*0.5f)<1e-6f);
            assert(fabsf(uv[1]-(1-ti/8.0f)*0.5f)<1e-6f);
        }
    for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)for(int z=-1;z<=1;z++) {
        if(!x&&!y&&!z)continue;
        assert(NanoSkyboxFaceUV(x,y,z,&face,&uv[0],&uv[1]));
        assert(face>=0&&face<6&&uv[0]>=0&&uv[0]<=1&&uv[1]>=0&&uv[1]<=1);
    }
}
static void reset(void) {
    for(int i=0;i<352;i++)guarded[i]=0xBEEF;
    for(int y=0;y<16;y++)for(int x=0;x<16;x++)d_viewbuffer[y*20+x]=0;
}
static void guards(void) {
    for(int i=0;i<16;i++)assert(guarded[i]==0xBEEF&&guarded[336+i]==0xBEEF);
    for(int y=0;y<16;y++)for(int x=16;x<20;x++)assert(d_viewbuffer[y*20+x]==0xBEEF);
}
int main(void) {
    projection();
    int ids[6]={1,2,3,4,5,6};R_SetupSky(ids);assert(!frees);
    R_SetupSky(NULL);assert(frees==6);
    for(int i=0;i<6;i++)assert(!tr.skyboxTextures[i]);
    R_SetupSky(NULL);assert(frees==6);R_SetupSky(ids);
    for(int i=0;i<6;i++) {
        images[i+1]=(image_t){{pixels[i]},3,5};
        for(int p=0;p<15;p++)pixels[i][p]=i*100+p+1;
    }
    RI.base_vpn[0]=1;RI.base_vright[1]=-1;RI.base_vup[2]=1;
    espan_t spans[]={{-4,0,24,NULL},{0,15,INT_MAX,NULL},{0,-1,16,NULL},{0,16,16,NULL},{18,3,2,NULL},{0,4,0,NULL}};
    for(int i=0;i<5;i++)spans[i].pnext=&spans[i+1];
    reset();D_DrawSkySpans(spans);guards();
    for(int y=0;y<16;y++)for(int x=0;x<16;x++) {
        if(y!=0&&y!=15)assert(!d_viewbuffer[y*20+x]);
        else {
            int face;float u,v;
            assert(NanoSkyboxFaceUV(1,-(x-7.5f)*0.125f,-(y-7.5f)*0.125f,&face,&u,&v));
            int tx=bound(0,(int)(u*3),2),ty=bound(0,(int)(v*5),4);
            assert(d_viewbuffer[y*20+x]==pixels[face][ty*3+tx]);
        }
    }
    reset();R_SetupSky(NULL);D_DrawSkySpans(spans);guards();
    for(int x=0;x<16;x++)assert(d_viewbuffer[x]==0x1234);
    puts("Skybox: upstream cube orientation, rays, ties, clipping/stride, texture reads, missing faces and unload/reload pass.");
}
'''
build=root/'build/tests';build.mkdir(parents=True,exist_ok=True)
p=build/'nano-skybox-test.c';p.write_text(code)
exe=p.with_suffix('')
subprocess.run(['gcc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(root/'src'),str(p),'-lm','-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
