Test Procedure
**************

Prerequisites:
==============

    a. Clear cookies before start.
    b. Make sure database folder is empty (database files are non existent).
    c. Make sure all the nodes are powered off.
    d. Start gate manually and keep ssh session window open (TeraTerm, Putty, etc),
       so you can monitor any "behind the scenes" errors on server side. (python errors)
    e. If using google chrome, press F12 once gate started and
       appropriate page selected to monitor "behind the scenes" errors on client side. (javascript errors)

1. Testing basic page functionality
===================================

    * Without login in click on other pages and verify that there is no crashes
    * Login, click on all pages and subpages and verify that there is no crashes
    * Go through pages one more but this time click on every radio button you can
      find and verify there is no errors.
    * Log out and login again

2. Testing inactive nodes functionality
=======================================

    * Power up first node. Verify it appeared under inactive group.
    * Select Inactive group, select inactive node, rename node, save.
      Verify that process executed successfully and name has been changed
    * Unplug node, wait around 5 timeouts, verify that inactive group disappears
    * Plug node back again

3. Testing network functionality
================================

    * Change inactive node channel to 5. Verify that it has been performed with no errors.
      And that inactive node disappeared from current channel number 4.
    * Using setup menu, select default RF Network. Change channel to 5,
      verify that changes are executed successfully. Also verify that inactive node eventually appears on channel 5.
    * Repeat process using combination of channel, data rate and aes enable. Verify that it functions properly.
    * Create new group and verify there is no errors
    * Rename group, verify there is no errors.
    * Click create new group again, verify that verification script is working.
      (If you see group name hints, it is working)
    * Try creating another new group with the same name. Verify that system does not allow such action.
    * Select RF network again. Turn off autofill timeout parameters. Change wake and sleep period and save.
      Verify that that has been executed successfully. **Bug**: Page does not reload correctly here!
    * Turn autofill timeout parameters on this time. Change wake and sleep period and save.
      Verify that there is no errors.
    * Move inactive node to test group. Make sure that there is no errors.
    * Repeat 2 steps that are responsible for changing sleep/wake cycles. Verify that there is no errors.
    * Change RF network settings such as channel, data rate, aes with node attached.
      Verify that there is no errors in the transition.
      Also, make sure that the node is also active after network changes.

4. Testing log and live functionality
=====================================

    * Plug in 2 nodes.
    * Create 2 groups. Assign one node to one group and second node to the other group.
    * Verify that subpage links were created under Live and Logs.
      (Might have to refresh page or click on one of the pages to refresh the index).
    * Set constants for both of those nodes. Set all enables.
    * Verify that the data is displayed on live and logs pages.
    * Verify that it is possible to export and remove logs.
    * Verify that alarm functionality is working properly.

5. Testing multiple platform/multiple group functionality
=========================================================

    * Add node with another platform, such as 'jowa-102-4430'. Observe that node has appeared in the list.
    * Create new group, try renaming it. Move node from inactive to newly created group. Make sure there is no errors.
    * Select newly created group. Remove it. Verify that nodes has been moved to inactive group.
      And the group has been deleted properly with no errors.
    * Once again create new group. Move node from inactive group to newly created group.
      Select node and remove the node. Verify that node has been moved to inactive group.
      And the group itself still exists.
    * Select node in inactive group. Take a note of the modbus address. Remove node once again.
      Verify that node has been removed, rediscovered and reassigned with 'None' modbus address.
    * Move node from inactive group to a different group. Verify that new modbus has been assigned.
      Different from the old one.
    * Create another group. Verify that is possible to use up and down buttons to rearrange groups with no errors.
    * Add another node with the same platform. Move node from inactive group to the group with another node.
      Verify that is possible to rearrange nodes in the group.
    * Select platform once again, try renaming platform. Make sure there is no errors.
    * Select this newly created platform. And click 'Restore to Defaults'.
      Verify that restore process has been executed properly.

6. Testing users functionality
==============================

    * Logout once again. Try login in with a wrong password
    * Go to admin page and click create users
    * Start typing username, make sure that username validation works properly by typing username
      that is available and typing username that is taken.
    * Create 4 additional accounts. Use same words for username and password for simplicity. Create guest, read,
      write and admin. Use appropriate security check marks. Verify that those has been created properly.
    * Try changing user order. Verify that it is working successful.
    * Change admin properties to none. Verify that it works properly.
    * Try changing wireless user properties to none. Verify that such action is not possible.
    * Change admin back to admin. Change current user to write power. Verify that transition is ok.
    * Click on other tabs. Verify everything works properly.
    * Log out. Login as each user that you have created. Click on all the pages and verify everything is ok.
    * Try changing your password or name as one of the non admin users. Verify that is working correctly.
    * Try changing your username to already existing user name. Verify that such action is not possible.
    * Login using default login. Remove all the users that you've created. Verify that remove works properly.

7. Testing basic database functionality
=======================================

    * Manually stop gate by pressing CTRL+C in ssh window.
    * Make sure that database files(networks.db, system.db, users.db and platforms.db) and
      folders(networks, nodes) under /root/gate_data/database/ are created
    * Restart gate by running python run_gate.py.
    * Make sure all the settings loaded properly and system functions as if manual stop never happened.

8. Testing database export/remove/import functionality
======================================================

    * Make sure you have system setup up and working properly (you can see data on live page)
    * Navigate to setup -> system -> export/import database and click "export" button. Make sure you get ``dea`` file back from the browser.
    * Next, remove database. Go back to live page and make sure there is no data anymore. Navigate to setup -> field units and verify that units are part of the inactive group now.
    * Navigate to "export/import database" page and click import. Select earlier saved file. Once procedure is done, verify that live page has data again. Also, you groups are back under field units setup.
    * Change RF network settings to a different channel and different sleep period.
    * Perform export procedure, remove database, make sure nodes are part of the inactive group. Verify that RF network settings has been reset.
    * Perform import procedure. Make sure live page has data. Verify that RF network settings has been changed to proper ones.

9. Testing Wireless Metritape Router Reset Functionality
========================================================

    * Make sure you have live data and nodes active.
    * Unplug USB plug from E10(power plug as well). You web server will go down.
    * Plug power cable back in while holding the only button on E10. Hold button until Led 'B' starts circuling between green, red, yellow colors.
    * Release button. Wait couple or so minutes. Your web server should be reset.
    * You might have to run IP Addressing utility to set IP address to a known one. Otherwise try default one (192.168.0.111), might not work if you LAN network has different IP or network mask is different.
    * Open web interface once IP addressing is resolved you should observe your nodes in inactive group

10. Testing software upload functionality
=========================================

    * Acquire necessary upload files. (Files with extensions: ``spy``, ``zip``, ``vol`` and ``pea``)
    * Select Setup, RF Network. Select network. Click on update base software. Start upload without selecting file.
      Observe that there is a proper response to that. Try using file with bad name
      (any name other that starting with ``BASE_``).
      Try using false extension (any other than spy). Observe and confirm that validation works properly.
    * Finally, provide proper file. Confirm that the process has been executed successfully. And base version number
      has been incremented (if applies)
    * Try uploading base file with nodes present on the network and nodes absent on the network.
    * Test cancel function at various times. Before upload starts, during upload, right after upload. Verify that cancel executes successfully and overlay disappears.
      Cancel might wipe node software and node might become a virgin. That is normal.
    * Repeat whole procedure for node update (and virgin update if applies). Minus nodes present/nodes absent part since it does not really make sense in this case.
    * Try selecting multiple nodes and uploading files to multiple nodes at once.
    * Select Setup, System. Select system. Click on update gate software. Perform same procedure with providing false
      software upload data. Finally test that systems performs proper update if you provide software in a ``zip``,
      ``vol`` and ``pea`` formats. Note that ``vol`` format is obsolete and may take up to 20 minutes.

11. Testing SNMP functionality
==============================

    * Connect SNMP Relay to the same local network. Power up relay. Open up relay web page in the browser using it's IP address.
      (Use your network router to figure out relay IP address if needed)
    * Under Setup -> System select current system. Click on SNMP Settings.
    * Open "Edit SNMP Agents" page. Edit Default Test Agent or create new one. Click "Save" and "Test".
      Verify that save procedure works properly. As well as test procedure. You will get SNMP relay device description string if test
      works properly.
    * Press "Back" and navigate to SNMP commands page. Edit commands if needed. Test couple commands, such as relay 1 on and off commands.
    * Open SNMP relay web page. Navigate to SNMP settings. Enable traps. Enter IP address of Wireless Metritate router as trap destination.
    * Go back to web interface of the Wireless Metritape Router. Navigate to SNMP traps page. Connect digital input of the SNMP relay to Vdd.
      Observe SNMP traps appearing on the SNMP Trap debugging screen.
    * Connect potentiometer to the level input of one of the active nodes. Set enables and sensor constants so the data is displayed on the live page.
    * Test the ranges of your potentiometer. Select good (reachable) min and max points. Go back to the field units setup page and set minimum and maximum alarms.
      Verify that alarms are triggered when those values are exceeded. Go back to the normal operational state without alarms triggered.
    * Navigate to "SNMP Alerts and Acks Settings". Select appropriate test group and node. Under Alarm warnings, set your SNMP relay under SNMP Agent column for both
      level minimum and maximum alarms. For the minimum alarm, set relay 1 on for the set condition, relay 2 off for clear condition. And digital input 1 trap as an ack trap.
      Perform similar procedure for the maximum alarm using relay 2 and digital input 2 trap.
    * Navigate to live page. Trigger minimum alaram using potentiometer. Verify that relay 1 is on. Move potentiometer back to normal operating range. Verify that relay 1 went off.
      Move potentiometer back to minimum, verify that you can set relay off using ack on the Wireless Metritape router web interface. Set ack off next, verify that relay 1 went on.
      Connect Vdd to digital input 1 on your relay, verify that relay 1 went off, also verify that ack state changed to set on the Wireless Metrilink web page.
    * Repeat whole procedure for the maximum range using relay 2 and digital input 2 on your SNMP relay this time.
