# SPDX-License-Identifier: MIT
"""UTF-8-safe wrapping/name fitting on the shared HUD text code."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
code=r'''
#include <cassert>
#include <cstring>
#include <string>
struct Engine {float pfnGetCvarFloat(const char *s){return !strcmp(s,"nano_hud_text_height")?14:1;}}gEngfuncs;
#include "nano-hud-layout.h"
int width(const char *s){int pixels=0;for(;*s;s++)if(((unsigned char)*s&0xc0)!=0x80)pixels+=6;return pixels;}
int colorwidth(const char *s){int pixels=0;for(;*s;s++){
 if((*s=='\\' && s[1] && strchr("ywrd",s[1])) || (*s=='^' && s[1]>='0' && s[1]<='9')){++s;continue;}
 if(*s==1 || *s==3 || *s==4)continue;
 if(((unsigned char)*s&0xc0)!=0x80)pixels+=6;
}return pixels;}
int main(){
 char result[32],lines[8][1024];
 NanoHudFit("Long player name",result,sizeof(result),42,width);assert(width(result)<=42 && strstr(result,"..."));
 NanoHudFit("abcdef",result,5,100,width);assert(!strcmp(result,"abcd"));
 NanoHudFit("abcdef",result,sizeof(result),4,width);assert(!result[0]);
 NanoHudFit("Åøö",result,4,100,width);assert(!strcmp(result,"Å"));
 NanoHudFit(nullptr,result,sizeof(result),100,width);assert(!result[0]);
 assert(NanoHudWrap("x",lines,0,100,width)==0);
 int n=NanoHudWrap("Fire in the hole!",lines,8,48,width);assert(n==3);
 for(int i=0;i<n;i++)assert(width(lines[i])<=48);
 n=NanoHudWrap("Bomb has been planted",lines,2,48,width);assert(n==2);
 for(int i=0;i<n;i++)assert(width(lines[i])<=48);
 n=NanoHudWrap("Åøöabcdefghijklmnopqrstuvwxyz",lines,8,48,width);
 for(int i=0;i<n;i++){assert(width(lines[i])<=48);assert(!lines[i][0] || ((unsigned char)lines[i][0]&0xc0)!=0x80);}
 n=NanoHudWrap("\\rRed words continue here",lines,8,54,colorwidth);
 for(int i=0;i<n;i++){assert(colorwidth(lines[i])<=54);assert(!strncmp(lines[i],"\\r",2));}
 n=NanoHudWrap("^3Colour words continue",lines,8,54,colorwidth);
 for(int i=0;i<n;i++){assert(colorwidth(lines[i])<=54);assert(!strncmp(lines[i],"^3",2));}
 n=NanoHudWrap("\x03Radio words continue",lines,8,54,colorwidth);
 for(int i=0;i<n;i++){assert(colorwidth(lines[i])<=54);assert(lines[i][0]==3);}
 n=NanoHudWrap("one\ntwo",lines,8,100,width);assert(n==2 && !strcmp(lines[1],"two"));
}
'''
file=root/'build/ui-profile-v2/text-test.cpp';file.write_text(code);exe=file.with_suffix('')
subprocess.run(['g++','-std=c++11','-fsanitize=address,undefined','-I'+str(root/'src'),str(file),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
print('HUD text: UTF-8 boundaries, narrow bounds, long names, long words, wrapping and row limits passed.')
