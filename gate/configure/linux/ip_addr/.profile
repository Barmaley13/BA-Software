# .bash_profile

export PATH=\
/bin:\
/sbin:\
/usr/bin:\
/usr/sbin:\
/usr/bin/X11:\
/usr/local/bin

umask 022

python /root/ip_addr_utility.py

if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

exit
