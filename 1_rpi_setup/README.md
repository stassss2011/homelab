# RPI Setup

0. Enable boot from USB SSD via [instruction](.\boot_from_usb_ssd.md)
1. Download and install [rpi imager](https://github.com/raspberrypi/rpi-imager/releases)
2. Flash latest Other -> Pi Os Lite
    1. Set username and pass
    2. Configure WiFi
    3. You may need to login via Ethernet and enable wifi

        ```bash
        sudo raspi-config nonint do_wifi_country UA
        ```

3. Run to add docker support (`cmdline.txt`)

    ```bash
    sudo sed -i '$ s/$/ cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory/' /boot/firmware/cmdline.txt
    ```

4. Run to add  fan support and turn off LEDs (`config.txt`)

    ```bash
    sudo tee -a /boot/firmware/config.txt > /dev/null <<EOF

    # Enable I2C on the VideoCore
    dtparam=i2c_vc=on

    # Turn off PWR LED
    dtparam=pwr_led_trigger=none
    dtparam=pwr_led_activelow=off

    # Turn off ACT LED
    dtparam=act_led_trigger=none
    dtparam=act_led_activelow=off

    # Turn off Ethernet ACT LED
    dtparam=eth_led0=4

    # Turn off Ethernet LNK LED
    dtparam=eth_led1=4
    EOF
    ```

    ```bash
    sudo sed -i 's/^dtparam=audio=on/#dtparam=audio=on/' /boot/firmware/config.txt
    ```

    ```bash
    sudo sed -i 's/^#\(dtparam=i2c_arm=on\)/\1/' /boot/firmware/config.txt
    ```

5. Enable I2C in raspi-config:

    ```bash
    sudo raspi-config nonint do_i2c 0
    ```

6. Reboot

   ```bash
   sudo reboot
   ```

7. Update & upgrade:

    ```bash
    sudo apt update
    sudo apt upgrade -y
    ```

8. Install `smbus`

    ```bash
    sudo apt install python3-smbus -y
    ```

9. Copy `.fan_control` folder to `~`
10. Check that srcipt works by running:

    ```bash
    sudo /usr/bin/python3 /home/stas/.fan_control/exec/cli.py
    ```

11. Run to enable fan service

    ```bash
    sudo bash -c 'cat > /etc/systemd/system/fan_controller.service <<EOF
    [Unit]
    Description=Fan Controller Service
    After=network.target

    [Service]
    Type=simple
    ExecStart=/usr/bin/python3 /home/stas/.fan_control/exec/main.py
    Restart=always
    SyslogIdentifier=fan_controller
    User=root

    [Install]
    WantedBy=multi-user.target
    EOF'
    ```

    ```bash
    sudo chmod +x /home/stas/.fan_control/exec/main.py
    sudo systemctl daemon-reload
    sudo systemctl enable fan_controller.service
    sudo systemctl start fan_controller.service
    ```

12. Reboot

   ```bash
   sudo reboot
   ```

## References

- <https://www.waveshare.com/wiki/CM4-IO-BASE-B#Fan>
- <https://www.waveshare.com/wiki/CM4_RTC_FAN>

## TO Check

- nvme temp

```bash
sudo nvme smart-log /dev/nvme0n1
```
