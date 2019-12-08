#!/usr/bin/env bash
for i in `ps -ef|grep competition_v3.wsgi|grep -v grep|awk '{print $2}'`
do
kill -9 $i
done
