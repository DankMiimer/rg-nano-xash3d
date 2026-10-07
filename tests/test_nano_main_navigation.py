# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise actual cursor traversal using main-menu registration and display order."""
from pathlib import Path
import os,re,subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
def function(source,signature):
    start=source.index(signature);end=source.index('{',start)+1;depth=1
    while depth:depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]
for game,base in [('hl',native/'xash3d/3rdparty/mainui'),('cs',root/'upstream/cs16-client/3rdparty/mainui_cpp')]:
    main=(base/'menus/Main.cpp').read_text()
    registrations=re.findall(r'\bAddItem\(\s*(\w+)\s*\);',function(main,'void CMenuMain::_Init('))
    display=re.findall(r'&([A-Za-z]+)',re.search(r'CMenuPicButton \*rows\[\] = \{(.*?)\};',main,re.S).group(1))
    code=r"""
#include <cassert>
#include <vector>
#define QMF_INACTIVE 1
#define QMF_MOUSEONLY 2
struct CMenuBaseItem {int rank=-1,iFlags=0;bool visible=false;bool IsVisible(){return visible;}};
struct Items {std::vector<CMenuBaseItem*> list;int Count(){return list.size();}CMenuBaseItem*operator[](int i){return list[i];}};
struct CMenuItemsHolder {Items m_pItems;int m_iCursor=0,m_iCursorPrev=0;bool m_bWrapCursor=true;bool AdjustCursor(int);};
"""+function((base/'controls/ItemsHolder.cpp').read_text(),'bool CMenuItemsHolder::AdjustCursor(')
    code+='\nint main(){\n'
    for name in set(registrations):code+='CMenuBaseItem '+name+';\n'
    for i,name in enumerate(display):code+=name+'.rank='+str(i)+';\n'
    code+='CMenuItemsHolder menu;\n'
    for name in registrations:code+='menu.m_pItems.list.push_back(&'+name+');\n'
    active=['resumeGame','newGame','hazardCourse','configuration','saveRestore','multiPlayer','quit'] if game=='hl' else ['disconnect','resumeGame','newGame','configuration','quit']
    for name in active:code+=name+'.visible=true;\n'
    code+=r"""
 auto walk=[&](){
  menu.m_iCursor=0;assert(menu.AdjustCursor(1));int first=menu.m_iCursor,lastRank=-1,count=0;
  do {
   auto item=menu.m_pItems[menu.m_iCursor];assert(item->rank>lastRank);lastRank=item->rank;++count;
   menu.m_iCursorPrev=menu.m_iCursor;++menu.m_iCursor;assert(menu.AdjustCursor(1));
  }while(menu.m_iCursor!=first);
  assert(count>=5);
  menu.m_iCursorPrev=first;--menu.m_iCursor;assert(menu.AdjustCursor(-1));
  assert(menu.m_pItems[menu.m_iCursor]==&quit);lastRank=quit.rank;
  for(int i=1;i<count;++i){menu.m_iCursorPrev=menu.m_iCursor;--menu.m_iCursor;assert(menu.AdjustCursor(-1));auto item=menu.m_pItems[menu.m_iCursor];assert(item->rank<lastRank);lastRank=item->rank;}
  assert(menu.m_iCursor==first);
 };
 walk();
"""
    if game=='cs':code+='nanoSpectator.visible=true;walk();nanoSpectator.visible=false;walk();\n'
    code+='}\n'
    p=root/'build'/('main-navigation-'+game+'.cpp');p.write_text(code);exe=p.with_suffix('')
    subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(p),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
    print(game+': actual Up/Down cursor traversal follows display order, including spectator appearance/disappearance and wrap.')
