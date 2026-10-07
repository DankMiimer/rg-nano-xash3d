# SPDX-License-Identifier: GPL-3.0-or-later
"""Actual shared confirmation layout: wrapping, scrolling and reachable buttons."""
from pathlib import Path
import os,subprocess
root=Path(__file__).resolve().parents[1];native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
def function(s,signature):
 start=s.index(signature);brace=s.index('{',start);end=brace+1;depth=1
 while depth:depth+=(s[end]=='{')-(s[end]=='}');end+=1
 return s[start:end]
for game,base in [('hl',native/'xash3d/3rdparty/mainui'),('cs',root/'upstream/cs16-client/3rdparty/mainui_cpp')]:
 actual=function((base/'controls/YesNoMessageBox.cpp').read_text(),'void CMenuYesNoMessageBox::NanoArrangeDialog()')
 code=r"""
#include <cassert>
#include <cmath>
#include <cstring>
#include <cstdint>
#include <string>
#define Q_max(a,b) ((a)>(b)?(a):(b))
#define bound(lo,x,hi) ((x)<(lo)?(lo):((x)>(hi)?(hi):(x)))
#define QM_TOP 0
static int ScreenWidth=240,ScreenHeight=240;
static struct {float scaleX,scaleY;} uiStatic={240.f/1024,240.f/1024};
typedef int HFont;
struct Fonts {int GetTextWideScaled(int,const char *s,int){return strlen(s)*7;}} fonts,*g_FontMgr=&fonts;
struct Point{int x,y;Point(int x=0,int y=0):x(x),y(y){}};
struct Size{int w,h;Size(int w=0,int h=0):w(w),h(h){}};
struct EngFuncs{static float GetCvarFloat(const char*){return 1;}};
struct CMenuBaseItem {
 enum {NANO_ROW_NONE,NANO_ROW_CHECK,NANO_ROW_TABLE,NANO_ROW_TABS,NANO_ROW_SLIDER,NANO_ROW_SPIN,NANO_ROW_FIELD,NANO_ROW_DROP,NANO_ROW_PREVIEW,NANO_ROW_GROUP};
 char nanoLabel[256];int iFlags=0;bool IsVisible(){return true;}int NanoRowType(){return NANO_ROW_NONE;}
 Point pos;Size size;int font=0,pixels=0,eTextAlignment=0;const char *szName="",*nanoLabelSource="";
 void SetNanoFont(int n=12){pixels=n;}void SetNanoScale(float){}void VidInit(){}void CalcPosition(){}void CalcSizes(){}
 void SetRect(int x,int y,int w,int h){pos=Point(x,y);size=Size(w,h);}
};
#define QMF_HIDDENBYPARENT 64
#define QMF_NOTIFY 8
#define QMF_GRAYED 16
#define QMF_INACTIVE 32
#define Q_min(a,b) ((a)<(b)?(a):(b))
#define QM_LEFT 0
#define ETF_SHADOW 1
#define ETF_FORCECOL 2
static int uiColorHelp=0;
void UI_DrawString(int,int,int,int,int,const char *,int,int,int,int){}
#include "nano-menu-layout.h"
struct CMenuYesNoMessageBox:CMenuBaseItem {
 CMenuBaseItem dlgMessage1,yes,no;bool m_bIsAlert=false;int nanoMessageScroll=0;char nanoMessage[8192];void NanoArrangeDialog();
};
"""+actual+r"""
int main(){
 CMenuYesNoMessageBox box;std::string longText;for(int i=0;i<150;i++)longText+="Readable dialog words. ";
 box.dlgMessage1.szName=longText.c_str();box.NanoArrangeDialog();
 assert(box.dlgMessage1.pixels==14 && box.yes.pixels==14 && box.no.pixels==14);
 auto bottom=[](CMenuBaseItem &i){return (i.pos.y+i.size.h)*uiStatic.scaleY;};
 float top=box.pos.y*uiStatic.scaleY,height=box.size.h*uiStatic.scaleY;
 assert(top>=9 && top+height<=231);
 assert(bottom(box.dlgMessage1)+11<=box.yes.pos.y*uiStatic.scaleY);
 assert(bottom(box.yes)<=height-10 && bottom(box.no)<=height-10);
 assert(box.no.pos.x<box.yes.pos.x);
 std::string wrapped=box.nanoMessage;box.nanoMessageScroll=100000;box.NanoArrangeDialog();
 assert(box.nanoMessageScroll>0 && std::string(box.nanoMessage)==wrapped);
 assert(box.dlgMessage1.szName>box.nanoMessage && box.dlgMessage1.szName<box.nanoMessage+sizeof(box.nanoMessage));
 box.m_bIsAlert=true;box.NanoArrangeDialog();assert(box.yes.pos.x*uiStatic.scaleX>=63);
 box.dlgMessage1.szName="Short message";box.NanoArrangeDialog();assert(box.nanoMessageScroll==0 && !strcmp(box.nanoMessage,"Short message"));
 assert(box.size.h*uiStatic.scaleY<114 && box.pos.y*uiStatic.scaleY>=63);
}
"""
 p=root/'build/ui-profile-v2'/('dialog-test-'+game+'.cpp');p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(root/'src'),str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
 print(game+': actual shared confirmation wrapping, overflow scrolling, stable source and native buttons passed')
