E10 Linux Setup Instructions
****************************

Introduction
============

This part is kept for reference only. Installation script should take care of everything.

1. Establish serial connection to E10
=====================================

	Plug USB from your computer to E10.
	Open Tera Term using com port, set serial port using following settings:

		* 115200 bps
		* 8 data bits
		* no parity bit
		* 1 stop bit

2. Change Password
==================

	E10s ship from Synapse with a default username of root (and no password).
	Change your E10 password using the ``passwd`` command. Example::

		passwd
		Wireless13
		Wireless13

3. Connect E10 to LAN
=====================

	Figure out LAN address using your router or whatever.
	Open Tera Term and connect via SSH by entering username and password

4. Patch Python 2.6 on E10
==========================

	Use following code::
	
		mkdir /usr/include
		mkdir /usr/include/python2.6
		touch /usr/include/python2.6/pyconfig.h

5. Establish TFTP server
========================

	Establish TFTP server on your machine, point to E10 Setup folder
	Figure out IP address of the TFTP server. ``192.168.0.105`` is used as an example address in the steps below

6. Install python modules 
=========================

.. note:: Use Easy install. Manual install is kept mostly for reference purposes.
	
a. Easy Install
---------------

	Download ``site-packages.tar.gz`` archive and
	use following code to overwrite python's ``site-packages`` folder::

		cd /root/
		tftp -g -r site-packages.zip 192.168.0.105
		unzip site-packages.zip
		rm site-packages.zip
		rm -rf /usr/lib/python2.6/site-packages/
		mv site-packages /usr/lib/python2.6/

b. Manual Install
-----------------
	
	1. Download and install :download:`setuptools <../gate/configure/linux/setuptools-0.6c11.tar.gz>`.

		Use following code::

			cd /root/
			tftp -g -r setuptools-0.6c11.tar.gz 192.168.0.105
			gzip -d setuptools-0.6c11.tar.gz
			tar -xvf setuptools-0.6c11.tar
			rm setuptools-0.6c11.tar
			cd setuptools-0.6c11
			python setup.py build
			python setup.py install
			cd ..
			rm -rf setuptools-0.6c11

	2. Install pip, pyftpdlib, bottle, pymodbus, pyserial python modules

		Use following code::

			easy_install pip==1.4.1
			pip install pyftpdlib==0.7
			pip install bottle==0.11.6
			pip install --no-deps pymodbus==1.2.0
			pip install pyserial==2.7

	3. Install Tornado module

		a. Old Tornado install(Use this patched :download:`netutil.py <../gate/configure/linux/netutil.py>` file)::

			pip install tornado==2.4.1
			cd /usr/lib/python2.6/site-packages/tornado
			rm netutil.py netutil.pyc
			tftp -g -r netutil.py 192.168.0.105

		b. New Tornado::

			pip install tornado==3.0.1

		.. note::

			tornado3.0.1 does not need a patch!
			But I suspect that it throw exceptions at us. 
			Even though it seem to recover on its own I would not trust it.
			Most likely something to do with socket implementation

		.. warning:: **USE 3a, SKIP 3b! KEPT FOR FUTURE REFERENCE**
			
7. Configure DHCP server
========================

	Download :download:`S40network <../gate/configure/linux/init.d/S40network>` file and use following code::
	
		cd /etc/init.d/
		tftp -g -r S40network 192.168.0.105
		dos2unix S40network
		chmod 755 S40network

	.. note:: **MAKE SURE TO CHANGE DEFAULT IP ADDRESS IF NEEDED. (192.168.1.111 BY DEFAULT)**

8. Configure FTP server
=======================

	Download :download:`ftp <../gate/configure/linux/init.d/ftp>` file and use following code::

		tftp -g -r ftp 192.168.0.105
		dos2unix ftp
		chmod 755 ftp

9. Manually start FTP server
============================
	
	Use following code::

		/etc/init.d/ftp start

10. Test FTP
============

	Test FTP using FileZilla. Enter E10 IP address. Empty for user and password
	Upload gate folder. Make sure ``/gate/database/`` folder is empty.

11. Upload ``BASE.py``
======================

	Upload ``BASE.py`` to base node via Portal. (Rewrite E10example)

12. Install/Configure autostart script
======================================

	Download :download:`S999snap <../gate/configure/linux/init.d/S999snap>` file and use following code::

		cd /etc/init.d/
		rm S999snap
		tftp -g -r S999snap 192.168.0.105
		dos2unix S999snap
		chmod 755 S999snap
	
13. Start gate script
=====================

	a. Automatic Start
	
		Restart E10. Alternatively you may use following code::
	
			/etc/init.d/S999snap start

	b. Manual Start (If needed or desired)

		Stop default Snap Connect instance and start gate manually via following code::

			/etc/init.d/S999snap stop
			cd /root/
			python gate

14. Test via Web Browser
========================
	
	Have fun with it!
