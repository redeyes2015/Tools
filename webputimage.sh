#!/bin/bash

curl -V > /dev/null || \
	( echo "You don't have curl installed!" && exit 1 )

USER=admin
PASSWD=admin

while getopts "u:p:" option; do
	case "$option" in
	  u ) USER="$OPTARG"
		  ;;
	  p ) PASSWD="$OPTARG"
		  ;;
	esac
done

shift $(($OPTIND - 1))
IP=$1
IMG=$2

if [ -z "$IMG" ] ; then IMG=images/firmware.img ; fi

if [ ! -f "$IMG" ] ; then
	echo "$IMG not found!"
	exit 1
elif [ ! -s "$IMG" ] ; then
	echo "$IMG has zero size!?"
	exit 1
fi

ENCODE=`echo -n "$USER:$PASSWD" | base64`

COOKIE=`curl -s -D - --cookie /dev/null -d "encode=$ENCODE&mode=liveview" http://$IP/fcgi-bin/system.login \
	-o /dev/null | grep Set-Cookie | awk -F' ' '{ORS="" ; print $2}'`

if [ -z "$COOKIE" ] ; then 
	echo "Cannot get cookies..."
	exit 1
fi

if [ -t 1 ] ; then
	curl --cookie $COOKIE -F "send_file=@$IMG" http://$IP/fcgi-bin/system.upgrade > /dev/null
else
	curl -s --cookie $COOKIE -F "send_file=@$IMG" http://$IP/fcgi-bin/system.upgrade > /dev/null || \
		echo 'upload failed..!?'
fi
#curl --cookie $COOKIE -d 'path=/system/software/meteor/encoder' http://$IP/fcgi-bin/dbusproxy.gconf_query
