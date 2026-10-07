// SPDX-License-Identifier: GPL-3.0-or-later
// CS-only menu, compiled into its own menu module rather than the HL menu.
#ifndef NANO_MENU_MATCH_H
#define NANO_MENU_MATCH_H
#include "SpinControl.h"
#include "CheckBox.h"
#include "Action.h"
#include "YesNoMessageBox.h"
#include "nano-match.h"
#include <math.h>

class NanoMatchChoices : public CMenuBaseArrayModel {
public:
    NanoMatchChoices(const char *const *items,int count):items(items),count(count){}
    void Update() override {}
    int GetRows() const override {return count;}
    const char *GetText(int row) override {return row>=0 && row<count?items[row]:"";}
private:
    const char *const *items;int count;
};
class NanoMatchMaps : public CMenuBaseArrayModel {
public:
    NanoMatchMaps():count(0){}
    void Update() override {
        count=0;int files=0;
        char **list=EngFuncs::GetFilesList("maps/*.bsp",&files,true);
        for(int i=0;list && i<files && count<256;++i) {
            const char *leaf=strrchr(list[i],'/');leaf=leaf?leaf+1:list[i];
            const char *back=strrchr(leaf,'\\');if(back)leaf=back+1;
            size_t n=strlen(leaf);if(n<5 || n-4>=64 || stricmp(leaf+n-4,".bsp"))continue;
            char name[64];memcpy(name,leaf,n-4);name[n-4]=0;
            if(!NanoMatchMapName(name))continue;
            bool duplicate=false;for(int j=0;j<count;++j)if(!stricmp(names[j],name))duplicate=true;
            if(!duplicate)strcpy(names[count++],name);
        }
        // Stable names, independent of filesystem order or an outdated maps.lst.
        for(int i=1;i<count;++i)for(int j=i;j>0 && strcmp(names[j-1],names[j])>0;--j) {
            char temp[64];strcpy(temp,names[j]);strcpy(names[j],names[j-1]);strcpy(names[j-1],temp);
        }
    }
    int GetRows() const override {return count;}
    const char *GetText(int row) override {return row>=0 && row<count?names[row]:"";}
private:
    int count;char names[256][64];
};
static NanoMatchSettings nanoMatchSession=NanoMatchDefaults();
static bool nanoMatchLoaded=false,nanoMatchSessionSaved=true;
static const char *const nanoMatchDifficulties[]={"Easy","Normal","Hard","Expert"};
static const char *const nanoMatchTeams[]={"Both teams","Terrorists only","Counter-T only"};
static const char *const nanoMatchWeapons[]={"Mixed weapons","Pistols only","Pistols + SMGs","Knives only"};
void UI_NanoMatchAdvanced_Menu();
class NanoMatchConfirm : public CMenuYesNoMessageBox {};
class CMenuNanoMatch : public CMenuFramework {
public:
    explicit CMenuNanoMatch(bool advanced=false):CMenuFramework(advanced?"CMenuNanoMatchAdvanced":"CMenuNanoMatch"),advanced(advanced),loading(false),saved(true),
        difficultyModel(nanoMatchDifficulties,4),teamModel(nanoMatchTeams,3),weaponModel(nanoMatchWeapons,4){}
private:
    bool advanced,loading,saved;
    NanoMatchSettings settings;
    NanoMatchMaps maps;
    NanoMatchChoices difficultyModel,teamModel,weaponModel;
    CMenuSpinControl map,bots,difficulty,team,weapons,round,freeze,money;
    CMenuCheckBox friendlyFire,walk,analyze;
    CMenuAction status,help;
    NanoMatchConfirm confirm;
    bool HasNav() {
        char path[96];snprintf(path,sizeof(path),"maps/%s.nav",settings.map);
        return EngFuncs::FileExists(path,true);
    }
    void Status() {
        if(!saved || !nanoMatchSessionSaved)status.szName="Save failed; try again";
        else if(!maps.GetRows())status.szName="No installed maps found";
        else if(settings.bots && !HasNav())status.szName=settings.analyze?"NAV analysis: slow / high RAM":"No NAV: bots 0 or Advanced";
        else if(settings.bots>=4)status.szName="4+ bots: performance untested";
        else status.szName="Stock difficulty; choices saved";
    }
    bool Save() {
        char text[512];int length=NanoMatchSerialize(text,sizeof(text),settings);
        saved=length>=0 && EngFuncs::COM_SaveFile("nano-match.cfg",text,length);
        nanoMatchSessionSaved=saved;Status();return saved;
    }
    void ReadControls() {
        settings=nanoMatchSession;
        if(advanced) {
            settings.weapons=(int)weapons.GetCurrentValue();settings.roundMinutes=(int)round.GetCurrentValue();
            settings.freezeSeconds=(int)freeze.GetCurrentValue();settings.money=(int)money.GetCurrentValue();
            settings.friendlyFire=friendlyFire.bChecked;settings.walk=walk.bChecked;settings.analyze=analyze.bChecked;
        } else {
            const char *name=map.GetCurrentString();if(NanoMatchMapName(name))strcpy(settings.map,name);
            settings.bots=(int)bots.GetCurrentValue();settings.difficulty=(int)difficulty.GetCurrentValue();settings.team=(int)team.GetCurrentValue();
        }
        settings=NanoMatchSanitize(settings);nanoMatchSession=settings;
    }
    void Changed() {if(loading)return;ReadControls();Save();}
    void Think() override {
        // Returning from Advanced does not call the parent's VidInit.
        if(!advanced && (settings.weapons!=nanoMatchSession.weapons || settings.roundMinutes!=nanoMatchSession.roundMinutes ||
            settings.freezeSeconds!=nanoMatchSession.freezeSeconds || settings.money!=nanoMatchSession.money ||
            settings.friendlyFire!=nanoMatchSession.friendlyFire || settings.walk!=nanoMatchSession.walk || settings.analyze!=nanoMatchSession.analyze)) {
            ReadControls();Status();
        }
        CMenuFramework::Think();
    }
    bool Validate() {
        ReadControls();
        if(!maps.GetRows() || !EngFuncs::IsMapValid(settings.map)) {status.szName="Map is missing or invalid";return false;}
        if(settings.bots && !HasNav() && !settings.analyze) {status.szName="No NAV: bots 0 or Advanced";return false;}
        return true;
    }
    void StartNow() {
        if(!Validate() || !Save())return;
        char config[2048],command[256];int n=NanoMatchServerConfig(config,sizeof(config),settings);
        if(n<0 || !EngFuncs::COM_SaveFile("nano-offline.cfg",config,n)) {status.szName="Match config could not save";return;}
        if(NanoMatchStartCommand(command,sizeof(command),settings.map)<0)return;
        // listenserver.cfg executes the generated bot choices again on server spawn.
        EngFuncs::CvarSetValue("deathmatch",1);EngFuncs::CvarSetValue("sv_lan",1);
        EngFuncs::PlayBackgroundTrack(NULL,NULL);EngFuncs::ClientCmd(false,command);
    }
    void Start() {
        if(!Validate())return;
        if(EngFuncs::GetCvarFloat("host_serverstate")) {
            confirm.SetMessage("Start selected match?\nThe current round will end.");
            confirm.onPositive=VoidCb(&CMenuNanoMatch::StartNow);confirm.Show();
            confirm.HighlightChoice(CMenuYesNoMessageBox::HIGHLIGHT_NO);
            confirm.SetCursorToItem(confirm.no);
        } else StartNow();
    }
    void _Init() override {
        settings=NanoMatchDefaults();confirm.Link(this);
        map.szName="Map";bots.szName="Bots (total; 2 recommended)";difficulty.szName="Difficulty";team.szName="Bot teams";
        weapons.szName="Bot weapons";round.szName="Round minutes";freeze.szName="Freeze seconds";money.szName="Starting money";
        friendlyFire.szName="Friendly fire";walk.szName="Bots walk";analyze.szName="Allow slow NAV analysis";
        bots.Setup(0,7,1);difficulty.Setup(&difficultyModel);team.Setup(&teamModel);weapons.Setup(&weaponModel);
        round.Setup(1,9,1);freeze.Setup(0,10,1);money.Setup(800,16000,800);
        if(!advanced)AddButton("Start match",NULL,PC_DONE,VoidCb(&CMenuNanoMatch::Start));
        status.iFlags|=QMF_INACTIVE;AddItem(status);
        CMenuBaseItem *basic[]={&map,&bots,&difficulty,&team};
        CMenuBaseItem *extra[]={&weapons,&round,&freeze,&money,&friendlyFire,&walk,&analyze};
        CMenuBaseItem **rows=advanced?extra:basic;unsigned count=advanced?7:4;
        for(unsigned i=0;i<count;++i) {rows[i]->onChanged=VoidCb(&CMenuNanoMatch::Changed);AddItem(*rows[i]);}
        if(!advanced) {
            AddButton("Advanced",NULL,PC_CONFIG,UI_NanoMatchAdvanced_Menu);
            AddButton("Network play",NULL,PC_MULTIPLAYER,UI_MultiPlayer_Menu);
        }
        help.szName=advanced?"NAV missing? Try bots 0 first.":NULL;
        help.iFlags|=QMF_INACTIVE;if(advanced)AddItem(help);
        AddButton("Back",NULL,PC_DONE,VoidCb(&CMenuNanoMatch::Hide));
    }
    void _VidInit() override {
        loading=true;settings=nanoMatchSession;saved=nanoMatchSessionSaved;
        if(!nanoMatchLoaded) {
            int length=0;char *data=(char*)EngFuncs::COM_LoadFile("nano-match.cfg",&length);
            if(data) {if(length>=0 && length<=4096)settings=NanoMatchParse(data,(size_t)length);EngFuncs::COM_FreeFile(data);}
            nanoMatchLoaded=true;
        }
        maps.Update();map.Setup(&maps);
        int selected=0;for(int i=0;i<maps.GetRows();++i)if(!strcmp(maps.GetText(i),settings.map))selected=i;
        map.SetCurrentValue((float)selected);
        if(maps.GetRows())strcpy(settings.map,maps.GetText(selected));
        map.SetGrayed(!maps.GetRows());
        bots.SetCurrentValue((float)settings.bots);difficulty.SetCurrentValue((float)settings.difficulty);team.SetCurrentValue((float)settings.team);
        weapons.SetCurrentValue((float)settings.weapons);round.SetCurrentValue((float)settings.roundMinutes);
        freeze.SetCurrentValue((float)settings.freezeSeconds);money.SetCurrentValue((float)settings.money);
        friendlyFire.bChecked=settings.friendlyFire;walk.bChecked=settings.walk;analyze.bChecked=settings.analyze;
        nanoMatchSession=settings;loading=false;Status();
    }
};
class CMenuNanoMatchAdvanced : public CMenuNanoMatch {public:CMenuNanoMatchAdvanced():CMenuNanoMatch(true){}};
ADD_MENU(menu_nano_match,CMenuNanoMatch,UI_NanoMatch_Menu);
ADD_MENU(menu_nano_match_advanced,CMenuNanoMatchAdvanced,UI_NanoMatchAdvanced_Menu);
#endif
