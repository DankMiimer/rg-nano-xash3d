# SPDX-License-Identifier: GPL-3.0-or-later
"""Run actual save actions and drawing against a texture/command test engine."""
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
source=(native/'xash3d/3rdparty/mainui/menus/LoadGame.cpp').read_text()
def function(signature):
    start=source.index(signature);end=source.index('{',start)+1;depth=1
    while depth:depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]
code=r'''
#include <cassert>
#include <cstring>
#include <strings.h>
#include <cstdio>
#include <vector>
#include <string>
#include <map>
#include <functional>
#include "keydefs.h"
#include "nano-save-browser.h"
#define Q_min(a,b) ((a)<(b)?(a):(b))
#define Q_max(a,b) ((a)>(b)?(a):(b))
#define bound(a,x,b) Q_min(Q_max(x,a),b)
#define stricmp strcasecmp
void Q_strncpy(char*d,const char*s,size_t n){snprintf(d,n,"%s",s);}
static bool active=true,nativeMenu=true;bool CL_IsActive(){return active;}bool NanoMenuEnabled(){return nativeMenu;}
static int ScreenWidth=240,ScreenHeight=240;
static struct {int maxClients;} globals={1},*gpGlobals=&globals;
enum{QM_LEFT,QM_RIGHT,QM_CENTER,ETF_FORCECOL=2,ETF_SHADOW=1,SND_MOVE=0};
static int uiPromptTextColor=1,uiPromptFocusColor=2,uiColorHelp=3,uiColorWhite=4;
static struct {const char *sounds[1];} uiStatic={{"move"}};
void PlayLocalSound(const char*){}
namespace UI {struct Key{
 static bool IsEscape(int k){return k==K_ESCAPE;}static bool IsEnter(int k){return k==K_ENTER;}
 static bool IsUpArrow(int k){return k==K_UPARROW;}static bool IsDownArrow(int k){return k==K_DOWNARROW;}
};}
static std::map<std::string,int> textures;static int nextTexture=1,peakTextures=0;
struct CImage{
 std::string path;int id=0;
 void ForceUnload(){if(!path.empty())textures.erase(path);id=0;}
 void Reset(){path.clear();id=0;}
 void Load(const char *name){path=name;if(!textures.count(path))textures[path]=nextTexture++;id=textures[path];peakTextures=Q_max(peakTextures,(int)textures.size());}
 bool IsValid(){return id!=0;}int Handle(){return id;}
};
static std::vector<std::string> commands;static bool closed=false;
struct EngFuncs{
 static void ClientCmd(bool now,const char *s){commands.emplace_back(s);if(now && !strncmp(s,"killsave",8))deletePending=true;}
 static bool deletePending;
 static bool FileExists(const char*,bool){return true;}
 static int PIC_Width(int){return 160;}static int PIC_Height(int){return 100;}
 static void StopBackgroundTrack(){}
};bool EngFuncs::deletePending=false;
void UI_CloseMenu(){closed=true;}
struct save_t{char name[32],comment[256],date[32],elapsed_time[32];};
struct Model:std::vector<save_t>{
 int Count(){return size();}bool IsValidIndex(int i){return i>=0 && i<Count();}
 void Update(){if(EngFuncs::deletePending && size()>1){erase(begin()+1);EngFuncs::deletePending=false;}}
};
struct Table{int selected=0;int GetCurrentIndex(){return selected;}void SetCurrentIndex(int i){selected=i;}};
struct Dialog{
 bool visible=false;std::function<void()> onPositive;std::string message;
 void SetMessage(const char*s){message=s;}void Show(){visible=true;}bool IsVisible(){return visible;}
 bool KeyDown(int key){if(key==K_ESCAPE || key==K_SPACE)visible=false;return true;}
};
struct Base{bool hidden=false;bool KeyDown(int){return false;}bool KeyUp(int){return false;}void Draw(){}void Hide(){hidden=true;}};
static int draws=0;
void rectangle(int x,int y,int w,int h){assert(x>=0 && y>=0 && w>=0 && h>=0 && x+w<=240 && y+h<=240);}
void NanoThemeBevel(int x,int y,int w,int h,int,bool=false){rectangle(x,y,w,h);}
int NanoThemePanel(){return 0;}int NanoThemeField(){return 0;}int NanoThemeDark(){return 0;}
void UI_FillRect(int x,int y,int w,int h,int){rectangle(x,y,w,h);}
void UI_DrawRectangleExt(int x,int y,int w,int h,int,int){rectangle(x,y,w,h);}
void UI_DrawPic(int x,int y,int w,int h,int,CImage &i){rectangle(x,y,w,h);assert(textures.count(i.path) && textures[i.path]==i.id);++draws;}
void UI_DrawString(int,int x,int y,int w,int h,const char*,int,int,int,int){rectangle(x,y,w,h);}
void NanoMenuFit(int,const char*s,char*d,size_t n,int,int){Q_strncpy(d,s,n);}
struct CMenuLoadGame:Base{
 using BaseClass=Base;
 Model savesListModel;Table savesList;Dialog msgBox;
 int font=0,nanoSaveStart=0;CImage nanoThumb[3];char nanoThumbName[3][32]={},nanoThumbPath[3][128]={},nanoTarget[32]={},nanoPrompt[256]={};
 void SetNanoFont(int){}void DisableTransition(){}
 std::function<void()> VoidCb(void(CMenuLoadGame::*method)()){return [=]{(this->*method)();};}
 void NanoUnloadPreviews();void Hide();void NanoRequestSave();void NanoCommitSave();void NanoRequestDelete();void NanoCommitDelete();
 bool KeyDown(int);bool KeyUp(int);void LoadGame();void Draw();
};
'''
for name in ('void CMenuLoadGame::NanoUnloadPreviews(', 'void CMenuLoadGame::Hide(',
             'void CMenuLoadGame::NanoRequestSave(', 'void CMenuLoadGame::NanoCommitSave(',
             'void CMenuLoadGame::NanoRequestDelete(', 'void CMenuLoadGame::NanoCommitDelete(',
             'bool CMenuLoadGame::KeyDown(', 'bool CMenuLoadGame::KeyUp(',
             'void CMenuLoadGame::LoadGame(', 'void CMenuLoadGame::Draw('):code+=function(name)+'\n'
code+=r'''
int main(){
 for(int count=1;count<100;++count)for(int selected=0;selected<count;++selected)for(int start=0;start<count;++start){
  int window=NanoSaveWindow(selected,count,start);assert(window>=0 && window<=Q_max(0,count-3));assert(selected>=window && selected<window+3);
 }
 assert(NanoSaveNameValid("save01") && NanoSaveNameValid("saved game"));
 for(const char*s:{"","a/b","a\\b","a\";quit","a;quit","a\nquit","a\rquit"})assert(!NanoSaveNameValid(s));
 CMenuLoadGame m;for(const char*s:{"new","save01","save02","quick","autosave","save05"}){
  save_t row={};Q_strncpy(row.name,s,sizeof(row.name));Q_strncpy(row.comment,"A real saved game",sizeof(row.comment));m.savesListModel.push_back(row);
 }
 m.Draw();assert(draws==2 && textures.size()==2);
 for(int key=0;key<30;++key){m.KeyDown(key<15?K_DOWNARROW:K_UPARROW);m.Draw();assert(peakTextures<=3);}
 m.savesList.selected=0;commands.clear();active=false;m.KeyDown(K_F8);assert(commands.empty() && !m.msgBox.visible);
 active=true;globals.maxClients=2;m.KeyDown(K_F8);assert(commands.empty());globals.maxClients=1;
 m.KeyDown(K_ENTER);m.KeyDown(K_F9);assert(commands.empty() && !m.msgBox.visible);
 m.KeyDown(K_F8);assert(commands.back()=="save \"new\"\n" && closed && textures.empty());
 closed=false;commands.clear();m.savesList.selected=1;m.KeyDown(K_F8);assert(m.msgBox.visible && commands.empty());
 m.KeyDown(K_SPACE);assert(commands.empty() && !m.msgBox.visible);
 m.KeyDown(K_F8);m.savesList.selected=3;m.msgBox.visible=false;m.msgBox.onPositive();
 assert(commands.back()=="save \"save01\"\n"); // callback target survives selection change
 commands.clear();m.savesList.selected=1;m.KeyDown(K_F9);assert(m.msgBox.visible && commands.empty());
 m.KeyDown(K_ESCAPE);assert(commands.empty());m.KeyDown(K_F9);m.savesList.selected=5;m.msgBox.visible=false;m.msgBox.onPositive();
 assert(commands.back()=="killsave \"save01\"\n" && m.savesList.selected==4);
 commands.clear();m.savesList.selected=1;m.KeyDown(K_ENTER);assert(commands.back()=="load \"save02\"\n" && textures.empty());
 m.Draw();m.KeyDown(K_SPACE);assert(m.hidden && textures.empty());
 commands.clear();Q_strncpy(m.savesListModel[1].name,"bad;quit",32);m.savesList.selected=1;
 m.KeyDown(K_ENTER);m.KeyDown(K_F8);m.KeyDown(K_F9);assert(commands.empty() && !m.msgBox.visible);
 nativeMenu=false;assert(!m.KeyDown(K_F8) && !m.KeyUp(K_F8));
}
'''
p=root/'build/ui-visual/save-browser-test.cpp';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(code);exe=p.with_suffix('')
subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(root/'src'),'-I'+str(native/'xash3d/engine'),str(p),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
print('Actual save browser: 3-row scrolling/texture ownership, A/X/Y/B, cancel, fixed confirmation targets, new-slot guards, deletion refresh and command validation passed.')
