#!/bin/bash
 
## Place this script in system/scripts


case $1 in
gameStart)
 
    System=$2
    Romname=${5%.*} #romname
    Rom=${Romname##*/}

    MEDIA_PATH="/userdata/system/backglass/systems/$System/games/marquee/$Rom-marquee.gif"

    ## Send gif to second display
    if [ -f /tmp/dmd_mpv.pid ]; then
        kill "$(cat /tmp/dmd_mpv.pid)"
        rm /tmp/dmd_mpv.pid
    fi
    export DISPLAY=:0.0
    mpv \
        --no-border \
        --geometry=1920x1080+1920+0 \
        --loop=inf \
        "$MEDIA_PATH" > /dev/null 2>&1 & # Replace /dev/null by /tmp/mpv_debug.log for debugging purposes
    echo $! > /tmp/dmd_mpv.pid
;;
 
gameStop)
    if [ -f /tmp/dmd_mpv.pid ]; then
        kill "$(cat /tmp/dmd_mpv.pid)"
        rm /tmp/dmd_mpv.pid
    fi
    ;;
esac
