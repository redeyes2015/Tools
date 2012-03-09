#! bash

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
ENCODE=`echo -n "$USER:$PASSWD" | base64`

COOKIE=`curl -s -D - --cookie /dev/null -d "encode=$ENCODE&mode=liveview" http://$IP/fcgi-bin/system.login \
	-o /dev/null | grep Set-Cookie | awk -F' ' '{ORS="" ; print $2}'`

if [ -z "$COOKIE" ] ; then 
	echo "Cannot get cookies..."
	exit 0
fi
#curl -v --cookie $COOKIE -F "send_file=@$IMG" http://$IP/fcgi-bin/system.upgrade
curl --cookie $COOKIE -d 'path=/system/software/meteor/encoder' http://$IP/fcgi-bin/dbusproxy.gconf_query
