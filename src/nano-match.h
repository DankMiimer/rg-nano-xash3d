// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef NANO_MATCH_H
#define NANO_MATCH_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct NanoMatchSettings {
    char map[64];
    int bots, difficulty, team, weapons, roundMinutes, freezeSeconds, money;
    int friendlyFire, walk, analyze;
};
static inline bool NanoMatchMapName(const char *name)
{
    if (!name || !*name || strlen(name) >= 64) return false;
    for (const char *p=name; *p; ++p)
        if (!((*p>='a' && *p<='z') || (*p>='A' && *p<='Z') ||
              (*p>='0' && *p<='9') || *p=='_' || *p=='-')) return false;
    return true;
}
static inline NanoMatchSettings NanoMatchDefaults()
{
    NanoMatchSettings s={"de_dust",2,0,0,0,3,1,16000,0,0,0}; return s;
}
static inline int NanoMatchBound(int value,int low,int high)
{ return value<low?low:value>high?high:value; }
static inline NanoMatchSettings NanoMatchSanitize(NanoMatchSettings s)
{
    s.map[63]=0;
    if (!NanoMatchMapName(s.map)) strcpy(s.map,"de_dust");
    s.bots=NanoMatchBound(s.bots,0,7);s.difficulty=NanoMatchBound(s.difficulty,0,3);
    s.team=NanoMatchBound(s.team,0,2);s.weapons=NanoMatchBound(s.weapons,0,3);
    s.roundMinutes=NanoMatchBound(s.roundMinutes,1,9);s.freezeSeconds=NanoMatchBound(s.freezeSeconds,0,10);
    s.money=NanoMatchBound(s.money,800,16000);
    s.friendlyFire=!!s.friendlyFire;s.walk=!!s.walk;s.analyze=!!s.analyze;
    return s;
}
static inline int NanoMatchSerialize(char *out,size_t size,NanoMatchSettings s)
{
    s=NanoMatchSanitize(s);
    int n=snprintf(out,size,"// Nano match preferences; read as data, never executed.\n"
        "version 2\nmap %s\nbots %d\ndifficulty %d\nteam %d\nweapons %d\nround %d\nfreeze %d\nmoney %d\n"
        "friendlyfire %d\nwalk %d\nanalyze %d\n",s.map,s.bots,s.difficulty,s.team,s.weapons,
        s.roundMinutes,s.freezeSeconds,s.money,s.friendlyFire,s.walk,s.analyze);
    return n>=0 && (size_t)n<size?n:-1;
}
static inline NanoMatchSettings NanoMatchParse(const char *text,size_t length)
{
    NanoMatchSettings s=NanoMatchDefaults();
    size_t pos=0;bool currentFormat=false;
    while (pos<length) {
        char line[160],key[32],value[80],extra[2];size_t start=pos;
        while(pos<length && text[pos]!='\n') ++pos;
        size_t n=pos-start;if(pos<length)++pos;
        if(n>=sizeof(line))continue;
        memcpy(line,text+start,n);line[n]=0;
        if(sscanf(line,"%31s %79s %1s",key,value,extra)!=2)continue;
        if(!strcmp(key,"version")) {currentFormat=!strcmp(value,"2");continue;}
        if(!strcmp(key,"map")) {if(NanoMatchMapName(value))strcpy(s.map,value);continue;}
        char *end;long number=strtol(value,&end,10);
        if(*end || number < -100000 || number > 100000)continue;
        const char *names[]={"bots","difficulty","team","weapons","round","freeze","money","friendlyfire","walk","analyze"};
        int *values[]={&s.bots,&s.difficulty,&s.team,&s.weapons,&s.roundMinutes,&s.freezeSeconds,&s.money,&s.friendlyFire,&s.walk,&s.analyze};
        for(unsigned i=0;i<sizeof(values)/sizeof(values[0]);++i)if(!strcmp(key,names[i]))*values[i]=(int)number;
    }
    // Older files numbered the four added modes before the stock levels.
    if(!currentFormat)s.difficulty=s.difficulty>=4?s.difficulty-4:0;
    return NanoMatchSanitize(s);
}
static inline int NanoMatchServerConfig(char *out,size_t size,NanoMatchSettings s)
{
    s=NanoMatchSanitize(s);
    const char *teams[]={"any","T","CT"};
    bool restricted=s.weapons!=0, knife=s.weapons==3;
    int n=snprintf(out,size,"// Generated offline match.\nsv_lan 1\nsv_aim 0\nsv_cheats 0\n"
        "nano_nav_analyze %d\nbot_quota %d\nbot_quota_mode normal\nbot_join_after_player 1\nbot_auto_vacate 1\n"
        "bot_difficulty %d\nbot_zombie 0\nbot_stop 0\nbot_walk %d\n"
        "bot_join_team %s\nbot_chatter minimal\nbot_allow_pistols %d\nbot_allow_shotguns %d\n"
        "bot_allow_sub_machine_guns %d\nbot_allow_rifles %d\nbot_allow_machine_guns %d\n"
        "bot_allow_snipers %d\nbot_allow_grenades %d\nbot_allow_shield %d\n"
        "mp_autoteambalance %d\nmp_limitteams 0\nmp_friendlyfire %d\nmp_startmoney %d\n"
        "mp_freezetime %d\nmp_roundtime %d\nmp_timelimit 0\nmp_winlimit 0\nmp_maxrounds 0\n",
        s.analyze,s.bots,s.difficulty,s.walk,teams[s.team],
        !knife,!restricted,s.weapons==0 || s.weapons==2,!restricted,!restricted,
        !restricted,!restricted,!restricted,
        s.team==0,s.friendlyFire,s.money,s.freezeSeconds,s.roundMinutes);
    return n>=0 && (size_t)n<size?n:-1;
}
static inline int NanoMatchStartCommand(char *out,size_t size,const char *map)
{
    if(!NanoMatchMapName(map))return -1;
    // Fixed capacity leaves room for a human team change even with seven bots.
    int n=snprintf(out,size,"disconnect;menu_connectionprogress localserver;wait;wait;wait;"
        "exec listenserver.cfg;maxplayers 8;map %s\n",map);
    return n>=0 && (size_t)n<size?n:-1;
}
#endif
