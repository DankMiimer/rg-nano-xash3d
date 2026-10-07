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
#include <cstring>
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
struct Fonts { CBaseFont objects[16];bool live[16]={false}; CBaseFont *GetIFontFromHandle(int n) { return n>0 && n<16 && live[n]?&objects[n]:NULL; } int GetTextWideScaled(int,const char *text,int,int=-1){return strlen(text)*6;} } fonts,*g_FontMgr=&fonts;
struct CFontBuilder { CFontBuilder(const char *,int tall,int) { assert(tall==12 || tall==14); } int Create() { ++created;assert(created<16);fonts.live[created]=true;return created; } };
class CMenuBaseItem {
 public: int nanoFontPixels=12;
public:
    enum NanoRowKind { NANO_ROW_NONE,NANO_ROW_BUTTON,NANO_ROW_SLIDER,NANO_ROW_SPIN,NANO_ROW_CHECK,NANO_ROW_TABLE,NANO_ROW_ACTION,NANO_ROW_FIELD,NANO_ROW_DROP,NANO_ROW_TABS,NANO_ROW_PREVIEW,NANO_ROW_GROUP };
    NanoRowKind kind;
    Point pos,renderPos;Size size;int parentOffset=0,iFlags=0,charSize=26,font=0;bool visible=true; const char *szName=nullptr,*nanoLabelSource=nullptr;char nanoLabel[256];
    CMenuBaseItem(NanoRowKind k=NANO_ROW_NONE):kind(k){}
    virtual ~CMenuBaseItem(){}
    virtual NanoRowKind NanoRowType() const { return kind; }
    void SetNanoFont(int pixels=12);
    bool IsVisible() const { return visible; }
    void Hide(){visible=false;}
    void SetCoord(int x,int y){pos=Point(x,y);}
    void SetSize(int w,int h){size=Size(w,h);}
    void CalcPosition(){renderPos=Point(pos.x,pos.y+parentOffset);} void CalcSizes(){}
    virtual void VidInit(){CalcPosition();CalcSizes();}
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
    code+='#define Q_min(a,b) ((a)<(b)?(a):(b))\n#define QM_LEFT 0\n#define ETF_SHADOW 1\n#define ETF_FORCECOL 2\nstatic int uiColorHelp=0;\nvoid UI_DrawString(int,int,int,int,int,const char *,int,int,int,int){}\n'
    code+='#include "nano-menu-layout.h"\n'
    code+=function((base/'controls/BaseItem.cpp').read_text(encoding='utf-8'),'void CMenuBaseItem::SetNanoFont(')
    framework=(base/'controls/Framework.cpp').read_text(encoding='utf-8')
    code+=function(framework,'bool CMenuFramework::NanoSettingsActive(')
    code+=function(framework,'void CMenuFramework::NanoArrangeSettings(')
    code+=r'''
int main(){
    // A parent moving into the native viewport must invalidate its child's cached position.
    CMenuBaseItem cachedButton(CMenuBaseItem::NANO_ROW_BUTTON);
    cachedButton.parentOffset=128;NanoMenuRect(cachedButton,10,36,220,20);
    cachedButton.parentOffset=0;NanoMenuRect(cachedButton,10,36,220,20);
    assert(cachedButton.renderPos.y==cachedButton.pos.y);
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
        assert(top>=36 && bottom<=233);
        assert(item->charSize*uiStatic.scaleY>=12 && item->font>0);
        assert(menu.pos.x==0 && menu.pos.y==0);
    }
    assert(menu.nanoScroll>0 && created==1);
    CMenuBaseItem tabs(CMenuBaseItem::NANO_ROW_TABS);menu.items.push_back(&tabs);
    menu.focus=&tabs;menu.NanoArrangeSettings();
    assert(!(tabs.iFlags&QMF_HIDDENBYPARENT));
    assert(tabs.pos.y*uiStatic.scaleY>=36 && (tabs.pos.y+tabs.size.h)*uiStatic.scaleY<=233);
    // A nested group uses its own viewport, retaining focus visibility through all children.
    CMenuFramework group;group.items={&volume,&gamma,&table};group.focus=&gamma;
    int groupScroll=0;NanoMenuArrangeRows(group,220,152,groupScroll,2);
    assert(!(gamma.iFlags&QMF_HIDDENBYPARENT));assert(gamma.size.w*uiStatic.scaleX>=200);
    CMenuBaseItem preview(CMenuBaseItem::NANO_ROW_PREVIEW);menu.items.push_back(&preview);
    menu.focus=&preview;menu.NanoArrangeSettings();assert(!(preview.iFlags&QMF_HIDDENBYPARENT));
    Point pos(10,100);Size sz(220,60);
    {NanoMenuPreviewFrame frame(pos,sz,Size(64,32),done.font,"Spray image");
        assert(pos.y==116 && sz.w==88 && sz.h==44);assert(pos.x==76);}
    assert(pos.x==10 && pos.y==100 && sz.w==220 && sz.h==60);
    menu.focus=&table;menu.NanoArrangeSettings();
    assert(checks[3].iFlags&QMF_GRAYED);
    assert(!(volume.iFlags&QMF_NOTIFY)); // no narrow-screen side-help overlap
    assert(decoration.pos.x==0 && decoration.pos.y==0);
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
    subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-fno-rtti','-fsanitize=address,undefined','-I'+str(root/'src'),str(path),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
    print(name+': actual settings font cache, focus scrolling, all-row bounds and legacy gating passed')
