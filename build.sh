#!/bin/sh
curl https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u -sLSo ./m3u/ipv6
cat ./m3u/ipv6 | grep "tvg-name" > tmp
while read -r line
do
  id=$(echo $line | awk '{printf $2}' | awk -F "\"" '{printf $2}')
  sed -i "s/tvg-name=\""${id}"\"/tvg-name=\""${id}"\" tvg-id=\""${id}"\"/g" ./m3u/ipv6
done < tmp
rm -f tmp
if ( ! cmp -s ./m3u/ipv6 ./m3u/ipv6.m3u ); then
  mv -f ./m3u/ipv6 ./m3u/ipv6.m3u
else
  rm -f ./m3u/ipv6
fi
