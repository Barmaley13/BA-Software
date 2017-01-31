Modbus API and Register Structure
*********************************

Introduction
============

All the node related data is stored inside of Modbus ``Holding Register Bank``.
Each register is 16 bit wide. All non specified addresses will return 0. This functionality can
be potentially changed to return Modbus TCP error messages instead.
Every node on the network has modbus base address assigned. You would have to 
refer to web interface in order to find base address for base node.
Click on ``Setup`` > ``Field Units``, select appropriate group and
Modbus Address should be displayed in one of the columns.
Once modbus base address has been assigned, it does not change throughout the lifetime of the system.

Node Data
=========

Each node has following data associated with it:
	* Network Address
	* Status/Error/Alarm Registers
	* Liquid Level
	* Volume
	* Temperature


1. Network Address of a node is 24 bit wide. Therefore, network address
   will be provided using 2 16-bit registers.
   High network address will be padded with 8 blank bits plus most
   significant 8 bits of the network address
   Low network address register will contain least significant 16 bits
   of the network address.

2. Status/Error/Alarm is spread across 2 16-bit registers. Each bit represents specific
   information for that particular node. Following tables will provided mask values for each bit.
   Bit with a logic "1" means that the condition is true, bit with a logic "0" means that condition is false.

   Status Register 1::

	0x0001 == Node HW error (level, volume, temperature readings can not be trusted and most likely are zeros anyway)
	0x0002 == Node is not present on the network (level, volume, temperature readings are obsolete)
	0x0004 == Reserved
	0x0008 == Reserved
	0x0010 == Reserved
	0x0020 == Reserved
	0x0040 == Reserved
	0x0080 == Reserved
	0x0100 == Level/Volume sensor circuit is shorted
	0x0200 == Level/Volume sensor circuit is open
	0x0400 == Temperature sensor circuit is shorted
	0x0800 == Temperature sensor circuit is open
	0x1000 == Reserved
	0x2000 == Reserved
	0x4000 == Reserved
	0x8000 == Reserved

   Status Register 2::

	0x0001 == Level Min Alarm is triggered
	0x0002 == Level Max Alarm is triggered
	0x0004 == Volume Min Alarm is triggered
	0x0008 == Volume Max Alarm is triggered
	0x0010 == Temperature Min Alarm is triggered
	0x0020 == Temperature Max Alarm is triggered
	0x0040 == Reserved
	0x0080 == Reserved
	0x0100 == Low Recent Sync Rate
	0x0200 == Reserved
	0x0400 == Low Battery
	0x0800 == Reserved
	0x1000 == Reserved
	0x2000 == Reserved
	0x4000 == Reserved
	0x8000 == Reserved

3. Liquid level, Volume and Temperature readings are represented as float32.
   Therefore, it takes 2 register per measurement.
   The byte order and units are set via web interface under ``Setup`` > ``System``.
   Look for ``Modbus Float Settings`` and ``Modbus Units`` headers.

Example Modbus Input Register Data
==================================

Please refer to output example below::

	base1 + 0000: network address of node1 (uint32 - high)
	base1 + 0001: network address of node1 (uint32 - low)
	base1 + 0002: status register 1 of node 1 (uint16)
	base1 + 0003: status register 2 of node 1 (uint16)
	base1 + 0004: liquid level in selected units of node1 (float32 - part 1)
	base1 + 0005: liquid level in selected units of node1 (float32 - part 2)
	base1 + 0006: volume in selected units of node1 (float32 - part 1)
	base1 + 0007: volume in selected units of node1 (float32 - part 2)
	base1 + 0008: temperature in selected units of node1 (float32 - part 1)
	base1 + 0009: temperature in selected units of node1 (float32 - part 2)

	base2 + 0000: network address of node2 (uint32 - high)
	base2 + 0001: network address of node2 (uint32 - low)
	base2 + 0002: status register 1 of node2 (uint16)
	base2 + 0003: status register 2 of node2(uint16)
	base2 + 0004: liquid level in selected units of node2 (float32 - part 1)
	base2 + 0005: liquid level in selected units of node2 (float32 - part 2)
	base2 + 0006: volume in selected units of node2 (float32 - part 1)
	base2 + 0007: volume in selected units of node2 (float32 - part 2)
	base2 + 0008: temperature in selected units of node2 (float32 - part 1)
	base2 + 0009: temperature in selected units of node2 (float32 - part 2)

	etc

