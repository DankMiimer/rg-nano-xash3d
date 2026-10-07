# SPDX-License-Identifier: GPL-3.0-or-later
"""Render an alpha ramp through the actual software drawing routine."""
from pathlib import Path
import os,subprocess,sys
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR','/var/tmp/rg-nano-xash3d-source-build'))
source=(native/'xash3d/ref/soft/r_draw.c').read_text()
start=source.index('static void R_DrawStretchPicImplementation(');brace=source.index('{',start);end=brace+1;depth=1
while depth:
 depth+=(source[end]=='{')-(source[end]=='}');end+=1
routine=source[start:end]
code=(root/"src/nano-ui-alpha.h").read_text()+r"""
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint16_t pixel_t;typedef unsigned int uint;typedef int qboolean;
#define false 0
#define true 1
#define COLOR_WHITE 65535
#define kRenderTransAdd 5
#define kRenderScreenFadeModulate 9
#define BLEND_COLOR(a,b) (b)
#define BLEND_ALPHA(a,s,d) (((unsigned)(s)*(a)+(unsigned)(d)*(7-(a)))/7)
typedef struct {pixel_t *pixels[1],*alpha_pixels;int width;} image_t;
static struct {int width,height,rowbytes,alpha,color,rendermode;pixel_t *buffer;pixel_t modmap[65536],addmap[65536];} vid;
"""+routine+r"""
int main(void){
 for(unsigned i=0;i<65536;i++){if(NanoUIBlend(7,i,0)!=i || NanoUIBlend(0,0,i)!=i)return 2;}
 pixel_t pixels[8],dest[64]={0};
 for(int i=0;i<8;i++)pixels[i]=(i<<13)|0x1fff;
 image_t image={{pixels},pixels,8};vid.width=vid.height=8;vid.rowbytes=8;vid.buffer=dest;vid.color=COLOR_WHITE;
 for(int alpha=0;alpha<8;alpha++){vid.alpha=alpha;R_DrawStretchPicImplementation(0,alpha,8,1,0,0,8,1,&image);}
 int failures=0;
 for(int x=0;x<8;x++)for(int y=1;y<8;y++)if(dest[y*8+x]<dest[(y-1)*8+x])failures++;
 printf("non-monotonic rendered opacity transitions: %d\n",failures);
 return failures?1:0;
}
"""
p=root/'build/ui-profile-v2/alpha-ramp.c';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(code)
subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Wno-unknown-pragmas','-fsanitize=address,undefined',str(p),'-o',str(p.with_suffix(''))],check=True)
result=subprocess.run([str(p.with_suffix(''))])
if '--expect-defect' in sys.argv:
 assert result.returncode==1,'The baseline must reproduce the defect'
else:assert result.returncode==0
