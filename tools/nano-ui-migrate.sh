#!/bin/sh
# SPDX-License-Identifier: MIT
# Only HUD fields are migrated. Preserve all other settings and keep a v1 backup.
set -eu
[ "$#" -eq 2 ] || exit 2
settings=$1
game=$2
case "$game" in valve) scale=2;; cstrike) scale=0.8;; *) exit 2;; esac
[ -f "$settings" ] || exit 0
if awk '{key=$1;v=$2;if(key=="set"){key=$2;v=$3}gsub(/"/,"",v);if(key=="nano_ui_profile_version" && v+0>=3)found=1}END{exit !found}' "$settings"; then exit 0; fi
# Upgrade only the old default Half-Life group size. Custom sizes remain custom.
if awk '{key=$1;v=$2;if(key=="set"){key=$2;v=$3}gsub(/"/,"",v);if(key=="nano_ui_profile_version" && v+0==2)found=1}END{exit !found}' "$settings";then
    staged="$settings.ui-v3.new"
    trap 'rm -f "$staged"' EXIT HUP INT TERM
    awk -v game="$game" '{
        key=$1;v=$2;if(key=="set"){key=$2;v=$3}gsub(/"/,"",v)
        if(key=="nano_ui_profile_version")next
        if(game=="valve" && (key=="nano_hud_bottom" || key=="nano_hud_side") && v+0==1.5){printf "set %s \"2\"\n",key;next}
        print
    } END {print "set nano_ui_profile_version \"3\""}' "$settings" > "$staged"
    [ -f "$settings.ui-v2.bak" ] || cp "$settings" "$settings.ui-v2.bak"
    mv "$staged" "$settings"
    exit 0
fi
staged="$settings.ui-v2.new"
trap 'rm -f "$staged"' EXIT HUP INT TERM
awk -v size="$scale" '
function number(v) {gsub(/"/,"",v);return v~/^-?[0-9]+([.][0-9]+)?$/}
{
    name=$1;value=$2;if(name=="set"){name=$2;value=$3}
    gsub(/"/,"",value)
    if(name=="nano_hud_bottom" || name=="nano_hud_side") {
        if(number(value)) {converted=value/1.125*size;if(converted<0.6)converted=0.6;if(converted>2)converted=2;printf "set %s \"%.3f\"\n",name,converted;next}
    }
    if(name=="nano_hud_menu" && number(value)) {
        text=value/1.25*14;if(text<12)text=12;if(text>18)text=18;
        text=int((text-12)/2+0.5)*2+12;next
    }
    if(name=="nano_ui_profile_version" || name=="nano_hud_text_height")next
    print
}
END {
    if(!text)text=14;
    print "set nano_hud_menu \"1\"";
    printf "set nano_hud_text_height \"%.0f\"\n",text;
    print "hud_scale \"1\"";
    print "set nano_ui_profile_version \"3\"";
}' "$settings" > "$staged"
[ -f "$settings.ui-v1.bak" ] || cp "$settings" "$settings.ui-v1.bak"
mv "$staged" "$settings"
