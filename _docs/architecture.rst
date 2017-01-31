Rough Software Architecture
***************************

Introduction
============
.. note::
	* This is rough draft and still in progress...
	* Don't take anything for granted
	* Suggestions and improvements are welcome!
	* Let me know if you see any typos
	* Enjoy!

Product Definition
__________________

Every endeavour should have a purpose. This is overall Sleepy Mesh as a product purpose:

**Highly flexible & customizable low power wireless mesh network system**

Requirements
____________

	* Web Interface
	* Constants change
	* Live and Logging pages
	* Import/Export Parameters
	* Import/Export Logs
	
Design Approach
_______________

We've used multiple approaches during design as well as agile manifesto in mind. Here they are:

1. Evolutionary Approach
2. Highly Informal Approach
3. Cowboy Programming

Major Architecture Components
_____________________________

We can split architecture in 3 parts:
	* Gate Portion
	* Node Portion
	* Communication Portion: Gate to Node/Node to Gate 

Those parts are definitely not equal in content. It is just logical to split those in 3.
Where, the heaviest one is the gate portion. Node portion is pretty light.
And communication portion should be the lightest out of all.

Gate Package, :doc:`gate`
=========================

I've generated couple images for you, hope they will clarify any questions your might have.

.. figure :: images/packages_gate.png
	:align: center
	
	Package modules and their interconnections
	
.. figure :: images/classes_gate.png
	:align: center
	
	Package classes
	
Pretty clear, right? Next, you have questions just RTFM. (I'm joking of course)

Lets break it down a bit more

Database/File System Module, :mod:`gate.file_system`
____________________________________________________

* Responsible for saving system state to hard drive as well as loading it
* Responsible for import/export system parameters

System Settings Module, :mod:`gate.system`
__________________________________________

* Responsible for network addressing
* System title
* System timing
* System language
* Internally responsible for system logo, strings, etc
* Parsing Command line arguments with default settings at system startup
* Disable/Enable user engine
* Enable/Disable Modbus
* Virgins Enable/Disable

Modbus Module, :mod:`gate.modbus`
_________________________________

* Responsible for outputting processed & formatted data onto Modbus interface

Mesh Network Package, :mod:`gate.sleepy_mesh`
=============================================

* Talking to nodes

	* Short Logs
		
		* Raw Data
		* Enables
		* Link Quality
		* Node Errors
	
	* Long Logs

* Directing sleep/wake cycles
* Changing network parameters
* Changing node parameters

.. figure :: images/packages_gate.sleepy_mesh.png
	:align: center
	
	Package modules and their interconnections
	
.. figure :: images/classes_gate.sleepy_mesh.png
	:align: center
	
	Package classes

Platforms Module, :mod:`gate.sleepy_mesh.platforms`
___________________________________________________

* Responsible for converting raw data to usable user friendly output depending on platform
* Grouping nodes
* Rearranging nodes
* Removing nodes, groups, etc
    
Web Package, :mod:`gate.web`
============================

* Works as a GUI Engine
* Responsible for outputting data

We can subdivide this to following 3 components:

* Frontend: html, tpl, javascript
* Backend: web methods in python
* Web Socket/Long Polling: communication b/w frontend and backend

.. figure :: images/packages_gate.web.png
	:align: center
	
	Package modules and their interconnections
	
.. figure :: images/classes_gate.web.png
	:align: center
	
	Package classes

Users Module, :mod:`gate.web.users`
___________________________________

* Responsible for managing different users & their permissions, roles, etc
* Guest User
* Disable User Engine
* User Cookies

Node Portion
============

Communication Portion
=====================

Important Design Considerations
===============================

Class Guidelines
________________

1. System blocks should be as independent as possible!
2. Define each block inputs/outputs/methods
3. Define communication rules for each building block
4. The architecture should describe relation between building blocks. E.g. which building block it can use directly, indirectly, which it can not use at all.

Data Design
___________

Data should be accessed directly by **only one** subsystem or class, except through access classes
or routines that allow access to the data in controlled & abstract ways

User Interface
______________

**Very important!** 
* Need to format css
* Separate UI from functional elements. Allow changing UI if needed.

Resource Management
___________________

* Disk Space
* Memory management(log export problem)

Security
________

* Handling buffers (??)
* Untrusted data - input from users, cookies, config data and other external interfaces
* Encryption
* Etc?

Performance
___________

* Log Export
* Time Changing
* Etc

Scalability (If applies)
________________________

How system will handle growth of users, nodes, database records?

Interoperability
________________

Share data or resources with other software/hardware

* Modbus
* SMNP

Internationalization/Localization
_________________________________

* Handle different languages
* Separate class/Handling all strings
* Need to resolve **ALL** Unicode problems

.. note:: 
	Keep strings in a class, reference them through the class interface, or store the strings
	in a resource file

Error Processing
________________

Use python logging module for

* Errors
* Exceptions
* Warnings

Errors can be *corrective* (attempt to recover) and *detective* (proceed like nothing happened or quit)
Active/passive error anticipation. Active - check user input!
