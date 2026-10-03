# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the real menu row arrangement and font cache without the engine."""
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
def function(source,signature):
    start=source.index(signature);brace=source.index('{',start);depth=1;end=brace+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]
for name,base in [('hl',native/'xash3d/3rdparty/mainui'),('cs',root/'upstream/cs16-client/3rdparty/mainui_cpp')]:
    code=r'''
#include <cassert>
#include <cstddef>
#include <cmath>
struct Size { int w,h; Size(int x=0,int y=0):w(x),h(y){} };
struct Point { int x,y; };
static float ScreenWidth=240, ScreenHeight=240;
static struct { float scaleY,yOffset; Size buttons_draw_size; } uiStatic={240.0f/1024,128,Size(256,32)};
static struct { int developer; } globals={1},*gpGlobals=&globals;
struct EngFuncs { static float GetCvarFloat(const char *) { return 1; } };
typedef int HFont;
struct CBaseFont {};
static int created;
struct MockFonts {
    CBaseFont objects[32]; bool live[32]={false};
    CBaseFont *GetIFontFromHandle(int handle) { return handle>0 && handle<32 && live[handle]?&objects[handle]:NULL; }
} fonts,*g_FontMgr=&fonts;
struct CFontBuilder {
    CFontBuilder(const char *,int,int){}
    int Create(){ ++created; assert(created<32); fonts.live[created]=true;return created; }
};
#define QM_DEFAULTFONT 0
struct CMenuPicButton {
    int charSize=26; HFont font=0; Size size; Point pos={0,0}; bool visible=true; void *parent=NULL;
    void SetCharSize(int){charSize=26;font=1;}
    void SetNanoScale(float);
    bool IsVisible(){return visible;}
    void SetVisibility(bool v){visible=v;}
    void *Parent(){return parent;}
    void SetCoord(int x,int y){pos.x=x;pos.y=y;}
    void CalcPosition(){}
    void CalcSizes(){}
};
struct CMenuMain {
    bool nanoLayout=false;
    CMenuPicButton banner,movieBanner,animatedBanner;
    CMenuPicButton console,disconnect,resumeGame,newGame,hazardCourse,configuration,saveRestore,multiPlayer,customGame,readme,previews,quit;
    void NanoArrange(bool);
};
'''
    code+=function((base/'controls/PicButton.cpp').read_text(),'void CMenuPicButton::SetNanoScale(')
    code+=function((base/'menus/Main.cpp').read_text(),'void CMenuMain::NanoArrange(')
    code+=r'''
int main(){
    CMenuPicButton button;
    button.SetNanoScale(2); assert(created==1 && button.charSize==52);
    button.SetNanoScale(2); assert(created==1 && button.charSize==52);
    fonts.live[1]=false;button.SetNanoScale(2);assert(created==2);
    CMenuMain menu;
    CMenuPicButton *rows[]={&menu.console,&menu.disconnect,&menu.resumeGame,&menu.newGame,&menu.hazardCourse,
        &menu.configuration,&menu.saveRestore,&menu.multiPlayer,&menu.customGame,
'''
    if name=='cs':code+='&menu.readme,'
    code+=r'''&menu.previews,&menu.quit};
    for(auto row:rows)row->parent=&menu;
    menu.NanoArrange(true);assert(created==2); // font reused across all buttons
    float previous=-1;
    for(auto row:rows){
        if(!row->visible)continue;
        float top=(row->pos.y+uiStatic.yOffset)*uiStatic.scaleY;
        float height=row->size.h*uiStatic.scaleY;
        assert(top>=7 && top+height<=240 && top>previous);
        previous=top+height;
        assert(row->charSize==52);
    }
    globals.developer=0;menu.NanoArrange(false);assert(!menu.console.visible);
    globals.developer=1;menu.NanoArrange(false);assert(!menu.console.visible && created==2);
    menu.newGame.visible=false;menu.NanoArrange(false);
    menu.newGame.visible=true;menu.NanoArrange(false);
    assert(menu.newGame.pos.y<menu.hazardCourse.pos.y);
    return 0;
}
'''
    path=root/'build'/('test-menu-'+name+'.cpp');path.write_text(code)
    exe=path.with_suffix('')
    subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(path),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
    print(name+': actual menu font reuse, font reset, visible row spacing and all-screen bounds passed')
