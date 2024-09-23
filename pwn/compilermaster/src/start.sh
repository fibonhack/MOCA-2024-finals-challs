#!/usr/bin/env bash

ulimit -n 4096

echo "
service ctf
{
	disable = no
	socket_type = stream
	protocol    = tcp
	wait        = no
	user        = root
	bind        = 0.0.0.0
	per_source  = 32
	cps         = 100 5
	server      = /run.sh
	port        = 6000
}" | tee /etc/xinetd.d/ctf

echo "
ctf 6000/tcp
" >> /etc/services

/etc/init.d/xinetd start
sleep infinity
