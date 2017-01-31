Distribution Installation
=========================

Introduction
------------

Installation script will not be able to configure DHCP and FTP servers as well as automatic start
unless you are running this script on a supported system.

`Gate` package is not designed to work on a stand alone computer such as PC/Linux/MAC. 
However it will work on Windows or Linux if you have Synapse daughter node installed.
We are strongly recommend using supported system.

Supported Systems:
 
 * Bolder Automation Router
 * Raspberry Pi 3 with Bolder Automation Daughter Card
 * Synapse E10 (some of the functionality might be limited)
 

Installation Procedure
----------------------

To install `gate` package on supported system follow this procedure:

1. Connect to the supported system using SSH via TeraTerm or Putty.

2. Copy zip distribution archive. You may use TFTP/FTP server or following command::

    `sydo git clone http://github.com/Barmaley13/BA-Software.git`

3. Unzip distribution::

	`unzip gate-03.01.01.zip`

4. Enter archive directory::

	`cd gate-03.01.01`

5. Modify any install options if needed (*OPTIONAL*)::
	
	`dos2unix setup.py`
	
	`vi setup.py`
	
   Open ``setup.py`` using vi/nano or similar and modify installation options.
   Assign ``True`` or ``False`` to enable/disable particular option respectively.

   * ``REMOVE_DATABASE`` - Removes database files during installation.
     Which forces user to start with brand new setup.
   * ``REMOVE_LOGS`` - Removes log files during installation.
   
   * ``DEFAULT_CONFIGURE_OPTIONS`` - Modify this python dictionary according to your configure wishes.
     **Internet connection is required.**

6. Install python package using following command::

	`sudo python setup.py install`

7. Clean up(if needed)::

	`rm gate-03.01.01.zip`
	
	`rm -rf gate-03.01.01`

8. Start script by restarting your system or by entering `/root` and running::

	`sudo python run_gate.py`


Further Information
-------------------
Please refer to documentation if you have any additional questions.
It should be included as part of the distribution. Look under ``/root/gate_data/docs/index.html``
