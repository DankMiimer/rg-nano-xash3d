# SPDX-License-Identifier: GPL-3.0-or-later
"""Render glyph bounds from the actual stb Create method and an installed font."""
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
font=Path(os.environ['NANO_MENU_FONT'])
source=(native/'xash3d/3rdparty/mainui/font/StbFont.cpp').read_text()
a=source.index('bool CStbFont::Create(');end=source.index('\nvoid CStbFont::GetCharRGBA',a)
abcStart=source.index('void CStbFont::GetCharABCWidthsNoCache(');abcEnd=source.index('\nbool CStbFont::HasChar',abcStart)
code=r"""
#include <cassert>
#include <cmath>
#include <cstring>
#include <vector>
#include <fstream>
#include <iostream>
#define STB_TRUETYPE_IMPLEMENTATION
#include "stb_truetype.h"
using byte=unsigned char;
static int profile=1;
struct EngFuncs{static float GetCvarFloat(const char*){return profile;}};
void Q_strncpy(char *d,const char *s,size_t n){strncpy(d,s,n);d[n-1]=0;}
void Con_Printf(const char*,const char*){}
struct Fonts{std::vector<byte> data;bool FindFontDataFile(const char*,int,int,int,char*,size_t){return true;}byte *LoadFontDataFile(const char*){return data.data();}} fonts,*g_FontMgr=&fonts;
struct CStbFont {
 char m_szName[256];int m_iTall,m_iWeight,m_iFlags,m_iBlur,m_iOutlineSize,m_iScanlineOffset,m_iAscent,m_iHeight,m_iMaxCharWidth;
 float m_fBrighten,m_fScanlineScale;byte *m_pFontData;stbtt_fontinfo m_fontInfo;double scale;
 bool Create(const char*,int,int,int,float,int,int,float,int);
 void GetCharABCWidthsNoCache(int,int&,int&,int&);
};
"""+source[a:end]+source[abcStart:abcEnd]+r"""
int main(int argc,char **argv){
 assert(argc==2);std::ifstream input(argv[1],std::ios::binary);
 fonts.data.assign(std::istreambuf_iterator<char>(input),{});assert(fonts.data.size()>100);
 for(int height:{12,14,26}){
  CStbFont f;assert(f.Create("Trebuchet MS",height,500,0,1,0,0,0,0));
  int capHeight=0;
  for(int ch=33;ch<127;++ch){int x0,y0,x1,y1;stbtt_GetCodepointBitmapBox(&f.m_fontInfo,ch,f.scale,f.scale,&x0,&y0,&x1,&y1);
   assert(f.m_iAscent+y0>=0);assert(f.m_iAscent+y1<=f.m_iHeight);
   if(ch=='H')capHeight=y1-y0;
   int aa,bb,cc;f.GetCharABCWidthsNoCache(ch,aa,bb,cc);int advance,bearing;stbtt_GetCodepointHMetrics(&f.m_fontInfo,ch,&advance,&bearing);
   int gx0,gx1;stbtt_GetGlyphBox(&f.m_fontInfo,stbtt_FindGlyphIndex(&f.m_fontInfo,ch),&gx0,nullptr,&gx1,nullptr);
   assert(cc==round((advance-bearing-gx1+gx0)*f.scale)+(height==14?1:0));
  }
  assert(capHeight>=height*2/3);assert(f.m_iHeight<=height*1.5);
  std::cout<<height<<" px: capital glyph "<<capHeight<<", cell "<<f.m_iHeight<<", descenders fit\n";
 }
 profile=0;CStbFont legacy;assert(legacy.Create("Trebuchet MS",12,500,0,1,0,0,0,0));
 assert(fabs(legacy.scale-stbtt_ScaleForPixelHeightPrecision(&legacy.m_fontInfo,16))<1e-9);
}
"""
p=root/'build/ui-profile-v2/font-metrics-test.cpp';p.write_text(code);exe=p.with_suffix('')
subprocess.run(['g++','-std=c++11','-O1','-fsanitize=address,undefined','-I'+str(native/'xash3d/3rdparty/mainui/font'),str(p),'-o',str(exe)],check=True)
subprocess.run([str(exe),str(font)],check=True)
