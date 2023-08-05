import concurrent.futures as cf
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException as Auth
from netmiko.exceptions import NetmikoTimeoutException as Timeout
from netmiko.exceptions import ReadTimeout

Cisco_devices = {
    'c800': ("c800-universalk9-mz.SPA.158-3.M9.bin", '97206388'),
    'c1100': ("c1100-universalk9.17.06.03a.SPA.bin", '706422748'),
    'isr': ("isr4400-universalk9.17.06.03a.SPA.bin", "794138635"),
    'c2900': ("c2900-universalk9-mz.SPA.157-3.M8.bin", '110493264'),
    'c880': ("c880data-universalk9_npe-mz.154-3.M10.bin", '44570068'),
    'c3900': ('c3900e-universalk9-mz.SPA.157-3.M8.bin', '118904036')}

with open('IP.txt', 'r') as devices:
    global IPs
    IPs = [IP for IP in devices.read().splitlines()]

# Tick trackers
total = set()
connected = set()
relaod_ready = set()
complete = set()
need_firmware = set()
wrong_filesize = set()
error = set()
processed = set()
remaining = set()

# Loggers
results = set()
reload = set()
firmware_type = set()
done = set()
needed = set()
err = set()

local_ips = []

def conn_params_EID():
    all_devices = {}
    for ip in IPs:
        ip = ip.rstrip('\n')
        all_devices[ip] = {
            'device_type': 'cisco_ios',
            'ip': ip,
            'username': 'EID/VID',
            'password': '',
            'secret': '',
            'banner_timeout': 30,
            'auth_timeout': 30,
            'global_delay_factor': 20
            }
    return all_devices

def conn_params_local():
    all_devices = {}
    for ip in IPs:
        ip = ip.rstrip('\n')
        all_devices[ip] = {
            'device_type': 'cisco_ios',
            'ip': ip,
            'username': 'local',
            'password': '',
            'secret': '',
            'banner_timeout': 30,
            'auth_timeout': 30,
            'global_delay_factor': 20
            }
    return all_devices

def Display_firmware_per_device(conn_params):
    IP = conn_params['ip']
    total.add(IP)
    user = conn_params['username'].lower()
    print(f'{IP} trying')
    try:
        with ConnectHandler(**conn_params) as conn:
            conn.enable()
            connected.add(IP)
            flag = False
            image = conn.send_command('dir', delay_factor=20).splitlines()
            for key, value in Cisco_devices.items():
                firmware = value[0]
                for line in image:
                    if firmware in line:
                        flag = True
                        filesize = value[1]
                        print(f'{IP} firmware is present')
                        if filesize in line:
                            print(f'{IP} filesize is correct')
                            if key.startswith('isr') or key.startswith('c1100'):
                                boot_command = [f'boot system flash bootflash:{firmware}']
                                wrong_boot_command1 = f'boot system flash:{firmware}'
                                wrong_boot_command2 = f'boot system flash bootflash:/{firmware}'
                                check_boot_command = conn.send_command('sh run | i boot system', delay_factor=50).splitlines()
                                check_current_firmware = conn.send_command(f'sh ver | i image', delay_factor=50)
                                if firmware.startswith('isr'):
                                    if user.startswith('e') or user.startswith('v'):
                                        firmware_type.add(f'{IP} is an ISR, tacacs\n')
                                        print(f'{IP} ISR, tacacs')
                                    elif user.startswith('m'):
                                        firmware_type.add(f'{IP} is an ISR, local login\n')
                                        print(f'{IP} ISR, local login')
                                elif firmware.startswith('c1100'):
                                    if user.startswith('e') or user.startswith('v'):
                                        firmware_type.add(f'{IP} is a c1100, tacacs\n')
                                        print(f'{IP} c1100, tacacs')
                                    elif user.startswith('m'):
                                        firmware_type.add(f'{IP} is a c1100, local login\n')
                                        print(f'{IP} c1100, local login')
                            elif key.startswith('c800') or key.startswith('c880') \
                                  or key.startswith('c2900') or key.startswith('c3900'):
                                boot_command = [f'boot system flash {firmware}']
                                check_boot_command = conn.send_command_timing('sh run | i boot system').splitlines()
                                check_current_firmware = conn.send_command_timing(f'sh ver | i image')
                                if firmware.startswith('c800'):
                                    if user.startswith('e') or user.startswith('v'):
                                        firmware_type.add(f'{IP} is a c800, tacacs\n')
                                        print(f'{IP} c800, tacacs')
                                    elif user.startswith('m'):
                                        firmware_type.add(f'{IP} is an c800, local login\n')
                                        print(f'{IP} c800, local login')
                                elif firmware.startswith('c880'):
                                    if user.startswith('e') or user.startswith('v'):
                                        firmware_type.add(f'{IP} is a c880, tacacs\n')
                                        print(f'{IP} c880, tacacs')
                                    elif user.startswith('m'):
                                        firmware_type.add(f'{IP} is an c880, local login\n')
                                        print(f'{IP} c880, local login')
                                elif firmware.startswith('c2900'):
                                    if user.startswith('e') or user.startswith('v'):
                                        firmware_type.add(f'{IP} is a c2900, tacacs\n')
                                        print(f'{IP} c2900, tacacs')
                                    elif user.startswith('m'):
                                        firmware_type.add(f'{IP} is an c2900, local login\n')
                                        print(f'{IP} c2900, local login')
                                elif firmware.startswith('c3900'):
                                    if user.startswith('e') or user.startswith('v'):
                                        firmware_type.add(f'{IP} is a c3900, tacacs\n')
                                        print(f'{IP} c2900, tacacs')
                                    elif user.startswith('m'):
                                        firmware_type.add(f'{IP} is an c3900, local login\n')
                                        print(f'{IP} c3900, local login')
                            if firmware in check_current_firmware:
                                done.add(f'{IP} {check_current_firmware}\n')
                                print(f'{IP} running on latest firmware')
                                results.add(f'{IP} complete\n')
                                complete.add(IP)
                            if not check_boot_command:
                                results.add(f'{IP}: firmware is present, boot command not present, added new boot command\n')
                                reload.add(f'{IP}\n')
                                conn.send_config_set(boot_command)
                                conn.save_config()
                                print(f'{IP} boot command not found, added new boot command')
                                current_boot_command = conn.send_command('sh run | i boot system', delay_factor=50).splitlines()
                                print(f'{IP} {current_boot_command[0]}')
                                if f'{IP} complete\n' not in results:
                                    relaod_ready.add(IP)
                                break
                            elif firmware not in check_boot_command[0]:
                                remove_boot_command = []
                                for command in check_boot_command:
                                    remove_boot_command.append(f'no {command}')
                                conn.send_config_set(remove_boot_command)
                                conn.send_config_set(boot_command)
                                conn.save_config()
                                current_boot_command = conn.send_command('sh run | i boot system', delay_factor=50).splitlines()
                                print(f'{IP} {current_boot_command[0]}')
                                results.add(f'{IP}: frimware is present, boot command is not correct, now corrected\n')
                                print(f'{IP} removed old boot commands, added new boot command, reload ready')
                                if f'{IP} complete\n' not in results:
                                    relaod_ready.add(IP)
                                reload.add(f'{IP}\n')
                                break
                            elif firmware in check_boot_command[0]:
                                if firmware.startswith('isr') or firmware.startswith('c1100'):
                                    if check_boot_command[0] == wrong_boot_command1:
                                        remove_wrong_boot = []
                                        remove_wrong_boot.append(f'no {wrong_boot_command1}')
                                        conn.send_config_set(remove_wrong_boot)
                                        conn.send_config_set(boot_command)
                                        conn.save_config()
                                        print(f'{IP} bootflash has been removed')
                                        results.add(f'{IP}: flash:firmware was changed to bootflash:firmware\n')
                                        reload.add(f'{IP}\n')
                                        current_boot_command = conn.send_command('sh run | i boot system', delay_factor=50).splitlines()
                                        print(f'{IP} {current_boot_command[0]}')
                                        if f'{IP} complete\n' not in results:
                                            relaod_ready.add(IP)
                                        break
                                    elif check_boot_command[0] == wrong_boot_command2:
                                        remove_wrong_boot = []
                                        remove_wrong_boot.append(f'no {wrong_boot_command2}')
                                        conn.send_config_set(remove_wrong_boot)
                                        conn.send_config_set(boot_command)
                                        conn.save_config()
                                        print(f'{IP} bootflash:\\ has been removed')
                                        results.add(f'{IP}: bootflash:\\firmware was changed to bootflash:firmware\n')
                                        reload.add(f'{IP}\n')
                                        current_boot_command = conn.send_command('sh run | i boot system', delay_factor=50).splitlines()
                                        print(f'{IP} {current_boot_command[0]}')
                                        if f'{IP} complete\n' not in results:
                                            relaod_ready.add(IP)
                                        break
                                elif not boot_command == check_boot_command[0]:
                                    remove_wrong_boot = []
                                    for line in check_boot_command:
                                        remove_wrong_boot.append(f'no {check_boot_command}')
                                    conn.send_config_set(remove_wrong_boot)
                                    conn.send_config_set(boot_command)
                                    conn.save_config()
                                    print(f'{IP} had wrong boot syntax')
                                    results.add(f'{IP} had wrong boot syntax, fixed')
                                    reload.add(f'{IP}\n')
                                    current_boot_command = conn.send_command('sh run | i boot system', delay_factor=50).splitlines()
                                    print(f'{IP} {current_boot_command[0]}')
                                    if f'{IP} complete\n' not in results:
                                        relaod_ready.add(IP)
                                    break
                                results.add(f'{IP} {check_boot_command[0]} - reload ready\n')
                                print(f'{IP} is reload ready')
                                if f'{IP} complete\n' not in results:
                                    relaod_ready.add(IP)
                                reload.add(f'{IP}\n')
                                break
                        elif filesize not in line:
                            print(f'{IP} Firmware has wrong filesize, it is corrupted')
                            conn.send_command(f'delete flash:{firmware}', delay_factor=50)
                            conn.send_command('\n', delay_factor=50)
                            conn.send_command('\n', delay_factor=50)
                            results.add(f'{IP} has a corrupted filesize, removed the firmware, push it out again\n')
                            wrong_filesize.add(IP)
                            break
                    elif firmware not in line:
                        continue
            if not flag:
                print(f'{IP} does not have the desired image')
                results.add(f'{IP}: Does not have the firmware uploaded\n')
                needed.add(f'{IP}\n')
                need_firmware.add(IP)
                raise ValueError
    except ValueError:
        error.add(IP)
        print(f'{IP} except ValueError rose')
        results.add(f'{IP} does not have desired firmware\n')
    except Auth:
        print(f'{IP} except Auth rose')
        local_ips.append(IP)
        if user.startswith('m'):
            error.add(IP)
            results.add(f'{IP} wrong credentials are being used\n')
    except Timeout:
        print(f'{IP} except Timeout rose')
        error.add(IP)
        results.add(f'{IP} has timedout\n')
    except ReadTimeout:
        print(f'{IP} except ReadTimeout rose')
        error.add(IP)
        results.add(f'{IP} takes too long to respond to command\n')
    except:
        print(f'{IP} except catch all rose')
        error.add(IP)
        results.add(f'{IP} has an other error\n')

def main():
    params_EID = conn_params_EID()
    param_local = conn_params_local()
    with cf.ThreadPoolExecutor(max_workers=30) as executor1:
        for param_eid in params_EID.values():
            executor1.submit(Display_firmware_per_device, param_eid)
    with cf.ThreadPoolExecutor(max_workers=25) as executor2:
        for ip in local_ips:
            executor2.submit(Display_firmware_per_device, param_local[ip])
    with open('Results.txt', 'a') as Results, open('reload_list.txt', 'a') as Reload, \
    open('device_type.txt', 'a') as Firmware_type, open('complete.txt', 'a') as Done, \
    open('firmware_needed.txt', 'a') as Needed, open('Error.txt', 'w') as Err, \
    open('logger.txt', 'a') as logger:
        logger.write(f'Devices that need the new firmware pushed to it = {len(need_firmware)}\n')
        logger.write(f'Devices with a corrupted firmware file = {len(wrong_filesize)}\n')
        logger.write(f'Devices ready to be reloaded = {len(relaod_ready)}\n')
        logger.write(f'Devices using the new firmware = {len(complete)}\n')
        logger.write(f'Devices connected to and processed = {len(connected)}\n')
        logger.write(f'Devices in the IP file = {len(total)}\n')
        processed.update(line for line in need_firmware if need_firmware is not None)
        processed.update(line for line in wrong_filesize if wrong_filesize is not None)
        processed.update(line for line in relaod_ready if relaod_ready is not None)
        processed.update(line for line in complete if complete is not None)
        for device in total:
            if device not in processed:
                remaining.add(device)
        logger.write(f'Devices that could not be logged in to = {len(remaining)}')
        Results.write(''.join(results))
        Reload.write(''.join(reload))
        Firmware_type.write(''.join(firmware_type))
        Done.write(''.join(done))
        Needed.write(''.join(needed))
        Err.write(''.join(line + '\n' for line in error if line not in processed))

if __name__ == '__main__':
    main()
