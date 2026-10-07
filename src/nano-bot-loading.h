// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef NANO_BOT_LOADING_H
#define NANO_BOT_LOADING_H
#include <cstring>
// Exploration has no known total. Analysis has a known total; never invent an exploration percentage.
struct NanoBotLoading {
    bool active=false; int stage=0; float progress=0;
    void Reset(){active=false;stage=0;progress=0;}
    void Message(int flag,int percent,const char *title){
        if(flag==2){Reset();return;}
        if(flag!=0 && flag!=1)return;
        int next=title && strstr(title,"LearningMap")?1:title && strstr(title,"ApproachPoints")?3:2;
        if(!active || (flag==1 && next==1)){progress=0;stage=next;}
        active=true;if(next>stage)stage=next;
        if(stage>1 && flag==0){float value=1.0f/3.0f+2.0f/3.0f*(percent<0?0:percent>100?100:percent)/100.0f;if(value>progress)progress=value;}
        if(stage>1 && progress<1.0f/3.0f)progress=1.0f/3.0f;
    }
};
#endif
