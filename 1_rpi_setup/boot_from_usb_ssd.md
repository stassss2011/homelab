# Boot from USB SSD

On the CM4-IO-BASE board there is a switch or a jumper (depending on hardware revision) for switching the Pi to RPI Boot Mode. Set a jumper on this pin or turn the switch to “ON”. Connect the CM4 to the Programmer Device with a USB-A to USB-C cable. From the programmer device, you will need to replicate a GitHub repository that has all of the code that you need. Open a terminal on the Programmer Device, navigate to a folder in which you want to replicate the code, and use the following commands to clone and build the code.

```bash
git clone https://github.com/raspberrypi/usbboot --depth=1
cd usbboot
make
```

The code is now downloaded or built. Enter the recovery folder and edit the file named boot.conf to change the boot order.

```bash
cd recovery
nano boot.conf
```

In

```toml
[all]
BOOT_UART=0
WAKE_ON_GPIO=1
POWER_OFF_ON_HALT=0
 
# Try SD first (1), followed by, USB PCIe, NVMe PCIe, USB SoC XHCI then network
BOOT_ORDER=0xf25641
 
# Set to 0 to prevent bootloader updates from USB/Network boot
# For remote units EEPROM hardware write protection should be used.
ENABLE_SELF_UPDATE=1
```

Change

```toml
BOOT_ORDER=0xf25641
```

To

```toml
BOOT_ORDER=0xf21654
```

To ensure that the CM4 has the latest firmware check [docks](https://www.raspberrypi.com/documentation/computers/compute-module.html#update-the-compute-module-bootloader)

Then do

```bash
./update-pieeprom.sh
cd ..
sudo ./rpiboot -d recovery
```

## References

- <https://blog.j2i.net/2022/04/12/booting-a-pi-cm4-on-nvme/>
- <https://www.waveshare.com/wiki/Write_Image_for_Compute_Module_Boards_eMMC_version>
