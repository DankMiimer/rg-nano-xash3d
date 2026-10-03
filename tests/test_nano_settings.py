# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise actual settings layout/font methods, focus scrolling and legacy gating."""
from pathlib import Path
import os,subprocess
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
#include <cmath>
#include <vector>
#define QMF_INACTIVE 1
#define QMF_HIDDENBYPARENT 2
#define QMF_GRAYED 4
#define QMF_NOTIFY 8
#define Q_max(a,b) ((a)>(b)?(a):(b))
#define bound(lo,x,hi) ((x)<(lo)?(lo):((x)>(hi)?(hi):(x)))
static int ScreenWidth=240,ScreenHeight=240;
static struct { float scaleX,scaleY; } uiStatic={240.0f/1024,240.0f/1024};
static float profile=1;
struct EngFuncs { static float GetCvarFloat(const char *) { return profile; } };
struct Point { int x,y; Point(int a=0,int b=0):x(a),y(b){} };
struct Size { int w,h; Size(int a=0,int b=0):w(a),h(b){} };
typedef int HFont;
struct CBaseFont {};
static int created=0;
struct Fonts { CBaseFont objects[16];bool live[16]={false}; CBaseFont *GetIFontFromHandle(int n) { return n>0 && n<16 && live[n]?&objects[n]:NULL; } } fonts,*g_FontMgr=&fonts;
struct CFontBuilder { CFontBuilder(const char *,int tall,int) { assert(tall==12); } int Create() { ++created;assert(created<16);fonts.live[created]=true;return created; } };
class CMenuBaseItem {
public:
    enum NanoRowKind { NANO_ROW_NONE,NANO_ROW_BUTTON,NANO_ROW_SLIDER,NANO_ROW_SPIN,NANO_ROW_CHECK,NANO_ROW_TABLE,NANO_ROW_ACTION };
    NanoRowKind kind;
    Point pos;Size size;int iFlags=0,charSize=26,font=0;bool visible=true;
    CMenuBaseItem(NanoRowKind k=NANO_ROW_NONE):kind(k){}
    virtual ~CMenuBaseItem(){}
    virtual NanoRowKind NanoRowType() const { return kind; }
    void SetNanoFont();
    bool IsVisible() const { return visible; }
    void Hide(){visible=false;}
    void SetCoord(int x,int y){pos=Point(x,y);}
    void SetSize(int w,int h){size=Size(w,h);}
    void CalcPosition(){} void CalcSizes(){}
    virtual void VidInit(){}
};
class CMenuFramework:public CMenuBaseItem {
public:
    bool nanoSettings=true;int nanoScroll=0;CMenuBaseItem banner;
    std::vector<CMenuBaseItem *> items;CMenuBaseItem *focus=NULL;
    int ItemCount() const { return items.size(); }
    CMenuBaseItem *GetItemByIndex(int i){return items[i];}
    CMenuBaseItem *ItemAtCursor(){return focus;}
    void SetCursorToItem(CMenuBaseItem &item){focus=&item;}
    void DisableTransition(){}
    bool NanoSettingsActive() const;void NanoArrangeSettings();
};
'''
    code+=function((base/'controls/BaseItem.cpp').read_text(encoding='utf-8'),'void CMenuBaseItem::SetNanoFont(')
    framework=(base/'controls/Framework.cpp').read_text(encoding='utf-8')
    code+=function(framework,'bool CMenuFramework::NanoSettingsActive(')
    code+=function(framework,'void CMenuFramework::NanoArrangeSettings(')
    code+=r'''
int main(){
    CMenuFramework menu;
    CMenuBaseItem done(CMenuBaseItem::NANO_ROW_BUTTON), volume(CMenuBaseItem::NANO_ROW_SLIDER),
        gamma(CMenuBaseItem::NANO_ROW_SPIN), table(CMenuBaseItem::NANO_ROW_TABLE), decoration;
    CMenuBaseItem checks[8];for(auto &check:checks)check.kind=CMenuBaseItem::NANO_ROW_CHECK;
    checks[3].iFlags=QMF_GRAYED;
    volume.iFlags=QMF_NOTIFY;
    decoration.iFlags=QMF_INACTIVE;
    menu.items={&menu.banner,&done,&volume,&gamma};
    for(auto &check:checks)menu.items.push_back(&check);
    menu.items.push_back(&table);menu.items.push_back(&decoration);
    menu.focus=&menu.banner;menu.NanoArrangeSettings();assert(menu.focus==&done);
    // Every focusable row, including the final large table, is fully visible on selection.
    for(auto item:menu.items){
        if(item==&menu.banner || item==&decoration)continue;
        menu.focus=item;menu.NanoArrangeSettings();
        assert(!(item->iFlags&QMF_HIDDENBYPARENT));
        float top=item->pos.y*uiStatic.scaleY;
        float bottom=top+item->size.h*uiStatic.scaleY;
        assert(top>=8 && bottom<=219);
        assert(item->charSize*uiStatic.scaleY>=12 && item->font>0);
        assert(menu.pos.x==0 && menu.pos.y==0);
    }
    assert(menu.nanoScroll>0 && created==1);
    assert(checks[3].iFlags&QMF_GRAYED);
    assert(!(volume.iFlags&QMF_NOTIFY)); // no narrow-screen side-help overlap
    assert(decoration.iFlags&QMF_HIDDENBYPARENT);
    // Wrap to the top, hide/show a row and retain keyboard navigation membership.
    menu.focus=&done;menu.NanoArrangeSettings();assert(menu.nanoScroll==0);
    checks[2].visible=false;menu.focus=&table;menu.NanoArrangeSettings();
    checks[2].visible=true;menu.NanoArrangeSettings();
    for(int i=0;i<1000;i++) menu.NanoArrangeSettings();
    assert(created==1);
    fonts.live[1]=false;menu.NanoArrangeSettings();assert(created==2);
    profile=0;int oldScroll=menu.nanoScroll;menu.NanoArrangeSettings();assert(menu.nanoScroll==oldScroll);
    profile=1;ScreenWidth=640;assert(!menu.NanoSettingsActive());
    return 0;
}
'''
    path=root/'build'/('test-settings-'+name+'.cpp');path.write_text(code,encoding='utf-8');exe=path.with_suffix('')
    subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-fno-rtti','-fsanitize=address,undefined',str(path),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
    print(name+': actual settings font cache, focus scrolling, all-row bounds and legacy gating passed')
