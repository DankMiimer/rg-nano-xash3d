#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise actual triangle dispatch and rasterizer winding with synthetic geometry."""
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
source=native/'xash3d/ref/soft'
def function(text,name):
    start=text.index(name)
    first=text.index('{',start)
    depth=1;end=first+1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return text[start:end]+'\n'
tri=(source/'r_triapi.c').read_text()
alias=(source/'r_trialias.c').read_text()
poly=(source/'r_polyse.c').read_text()
header=r'''#include <assert.h>
#include <stdio.h>
#define GAME_EXPORT
#define TRI_TRIANGLES 0
#define TRI_TRIANGLE_FAN 1
#define TRI_TRIANGLE_STRIP 2
#define TRI_QUADS 3
#define TRI_FRONT 0
#define TRI_NONE 1
#define DPS_MAXSPANS 64
typedef int TRICULLSTYLE;
typedef int spanpackage_t;
typedef struct { int u,v,s,t,l,zi,flags; } finalvert_t;
static struct { TRICULLSTYLE cullFace; } ds;
static struct { int fFlipViewModel; } tr;
static finalvert_t triv[3];
static int mode,n,vertcount;
static short s,t;
static unsigned light;
static struct { finalvert_t *a,*b,*c; } aliastriangleparms;
static int d_xdenom,*a_spans,r_p0[6],r_p1[6],r_p2[6];
static int rasterized,clipped;
static void R_PolysetSetEdgeTable(void) {}
static void R_RasterizeAliasPolySmooth(void) { rasterized++; }
static void R_AliasClipTriangle(finalvert_t*a,finalvert_t*b,finalvert_t*c) { (void)a;(void)b;(void)c;clipped++; }
static void R_SetupFinalVert(finalvert_t*fv,float x,float y,float z,int l,int u,int v) {
    (void)z;fv->u=tr.fFlipViewModel ? -(int)x : (int)x;fv->v=y;
    fv->flags=x>100?1:0;fv->l=l;fv->s=u;fv->t=v;fv->zi=1;
}
'''
code=header
code+=function(poly,'void R_DrawTriangle( void )')
code+=function(alias,'void R_RenderTriangle(')
for name in ('void GAME_EXPORT TriBegin(','static void TriDrawTriangle(','void GAME_EXPORT TriVertex3f(','void GAME_EXPORT TriCullFace('):
    code+=function(tri,name)
code+=r'''
static void reset(int cull,int flip) { rasterized=clipped=0;tr.fFlipViewModel=flip;TriCullFace(cull); }
static void triangle(int reverse) {
    TriBegin(TRI_TRIANGLES);TriVertex3f(0,0,0);
    TriVertex3f(reverse?0:10,reverse?10:0,0);
    TriVertex3f(reverse?10:0,reverse?0:10,0);
}
int main(void) {
    reset(TRI_FRONT,0);triangle(0);assert(rasterized==1);
    reset(TRI_FRONT,0);triangle(1);assert(rasterized==0);
    reset(TRI_NONE,0);triangle(0);assert(rasterized==1);
    reset(TRI_NONE,0);triangle(1);assert(rasterized==1);
    reset(TRI_FRONT,1);triangle(0);assert(rasterized==1);
    reset(TRI_NONE,1);triangle(0);assert(rasterized==1);
    reset(TRI_NONE,0);TriBegin(TRI_QUADS);
    TriVertex3f(0,0,0);TriVertex3f(10,0,0);TriVertex3f(10,10,0);TriVertex3f(0,10,0);
    assert(rasterized==2);
    for(int flip=0;flip<2;flip++) {
        reset(TRI_FRONT,flip);TriBegin(TRI_TRIANGLE_STRIP);
        TriVertex3f(0,0,0);TriVertex3f(10,0,0);TriVertex3f(0,10,0);TriVertex3f(10,10,0);TriVertex3f(0,20,0);
        assert(rasterized==3);
    }
    reset(TRI_NONE,0);TriBegin(TRI_TRIANGLES);
    TriVertex3f(200,0,0);TriVertex3f(200,10,0);TriVertex3f(210,0,0);
    assert(rasterized==0 && clipped==0);
    puts("Renderer triangle tests passed: front/back faces, two-sided tiles, mirrored weapon, quad fan, strip winding, fully clipped geometry.");
}
'''
path=root/'build/tests/renderer-triangle-test.c';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(code)
binary=path.with_suffix('')
subprocess.run(['gcc','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(path),'-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
