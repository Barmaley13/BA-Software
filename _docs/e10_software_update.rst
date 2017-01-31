E10 Software Update Guide
*************************

Update GATE
===========

1. Open your FTP client
2. Install gate using this procedure: :doc:`readme`
3. Do not start gate in order to avoid unnecessary Portal interference

Update BASE
===========

1. Open Portal
2. Upload new base code (e.g ``BASE_1.03.py``) onto base node

Update NODE
===========

1. Open Portal
2. Upload ``pcf2123.py``
3. Run ``NV_forceInit()`` under nv functions
4. Reboot node either manually or via Portal
5. Open NV parameters using Portal and set Platform to your hardware type. Example::

	Platform	JOWA-102-1.0

6. Check ``Reboot After Apply`` checkbox and press OK
7. Run ``PCF_init()`` function under ``pcf2123`` functions
8. Run ``PCF_read_time()`` function under ``pcf2123`` functions
9. Make sure proper messages received and get incremented if you run ``PCF_read_time()`` again. Example messages::

	Node4: Return Value = Mon,01JAN00,00:00:39
	Node4: Return Value = Mon,01JAN00,00:00:41

10. Upload new node code (e.g ``NODE_1.03.py``) onto node via Portal

Update Web Browser
==================

1. Clear cookies and any site data in your browser. (All browsers that are used with the system)

Final Step
==========

1. Start your gate and make sure system works properly.