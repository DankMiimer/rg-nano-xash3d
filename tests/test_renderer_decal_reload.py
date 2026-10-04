#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check actual decal reset/allocation/linking across cached brush-map reloads."""
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
def function(text,name):
    start=text.index(name);end=text.index('{',start)+1;depth=1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return text[start:end]+'\n'
source=native/'xash3d/ref/soft'
decals=(source/'r_decals.c').read_text()
main=(source/'r_main.c').read_text()
code=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#define MAX_RENDER_DECALS 8
#define FDECAL_PERMANENT 1
#define FBitSet(a,b) ((a)&(b))
#define mod_brush 1
typedef struct surface_s surface_t;
typedef struct decal_s { struct decal_s *pnext; surface_t *psurface; void *polys; int flags; } decal_t;
struct surface_s { decal_t *pdecals; int dlightframe; };
typedef surface_t msurface_t;
typedef struct { int unused; } decalinfo_t;
typedef struct { char name[32]; int type,numsurfaces; surface_t *surfaces; } model_t;
static struct { int value; } limit={8}, *r_decals=&limit;
static struct { int framecount; } tr={42};
static decal_t gDecalPool[MAX_RENDER_DECALS];
static int gDecalCount;
static struct { int nummodels; model_t *models[8]; } cl,*gp_cl=&cl;
static model_t *CL_ModelHandle(int i) { return cl.models[i]; }
static void fail(const char *s,const char *n) { (void)s;(void)n;assert(0); }
static struct { void (*Host_Error)(const char*,const char*); } gEngfuncs={fail};
static void Mem_Free(void *p) { free(p); }
static void *R_DecalCreatePoly(decalinfo_t *i,decal_t *d,surface_t *s) { (void)i;(void)d;(void)s;return NULL; }
'''
for name in ('void R_ClearDecals( void )','static void R_DecalUnlink(','static decal_t *R_DecalAlloc(','static void R_AddDecalToSurface('):
    code+=function(decals,name)
code+=function(main,'static void R_ClearSurfaceDecals( void )')
code+=r'''
int main(void) {
    surface_t world[3]={0},external[2]={0},studio[1]={0};
    model_t models[]={
        {"world.bsp",mod_brush,3,world},{"*1",mod_brush,3,world},
        {"crate.bsp",mod_brush,2,external},{"player.mdl",2,1,studio}
    };
    cl.nummodels=6;
    for(int i=0;i<4;i++)cl.models[i+1]=&models[i]; // Also include a missing handle.
    studio[0].pdecals=(decal_t*)&models[3];
    // Reproduce the stale-head cycle when only the pool is reset.
    R_AddDecalToSurface(R_DecalAlloc(NULL),&world[0],NULL);
    R_ClearDecals();
    decal_t *stale=R_DecalAlloc(NULL);
    R_AddDecalToSurface(stale,&world[0],NULL);
    assert(stale->pnext==stale);
    R_ClearDecals();R_ClearSurfaceDecals();
    for(int cycle=0;cycle<100;cycle++) {
        for(int i=0;i<3;i++)R_AddDecalToSurface(R_DecalAlloc(NULL),&world[i],NULL);
        for(int i=0;i<2;i++)R_AddDecalToSurface(R_DecalAlloc(NULL),&external[i],NULL);
        R_ClearDecals();R_ClearSurfaceDecals();
        for(int i=0;i<3;i++)assert(!world[i].pdecals);
        for(int i=0;i<2;i++)assert(!external[i].pdecals);
        assert(studio[0].pdecals==(decal_t*)&models[3]);
        decal_t *d=R_DecalAlloc(NULL);
        R_AddDecalToSurface(d,&world[0],NULL);
        assert(world[0].pdecals==d && !d->pnext && d->psurface==&world[0]);
        R_AddDecalToSurface(R_DecalAlloc(NULL),&world[0],NULL);
        assert(d->pnext && !d->pnext->pnext);
        decal_t *replacement=R_DecalAlloc(d);
        assert(world[0].pdecals!=replacement);
        R_AddDecalToSurface(replacement,&world[0],NULL);
        assert(world[0].pdecals->pnext==replacement && !replacement->pnext);
        R_ClearDecals();R_ClearSurfaceDecals();
    }
    puts("Decal reload: cached world/inline/external brushes, missing handles, pool reuse and replacement pass.");
}
'''
build=root/'build/tests';build.mkdir(parents=True,exist_ok=True)
c=build/'renderer-decal-reload-test.c';c.write_text(code)
exe=c.with_suffix('')
subprocess.run(['gcc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(c),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
