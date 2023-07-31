import concurrent.futures as cf
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException as Auth
from netmiko.exceptions import NetmikoTimeoutException as Timeout

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

total = set()
connected = set()
relaod_ready = set()
complete = set()
need_firmware = set()
wrong_filesize = set()
results = []
reload = []
firmware_type = []
done = []
needed = []
err = []

def conn_params_EID():
    all_devices = {}
    for ip in IPs:
        ip = ip.rstrip('\n')
        all_devices[ip] = {
            'device_type': 'cisco_ios',
            'ip': ip,
            'username': 'EID',
            'password': '',
            'secret': ''
            }
        # device = {
        #     'device_type': 'cisco_ios',
        #     'ip': ip,
        #     'username': 'local',
        #     'password': '',
        #     'secret': ''
        #     }
    return all_devices

def Display_firmware_per_device(conn_params):
    # with open('Results.txt', 'a') as results, open('reload_list.txt', 'a') as reload, \
    #     open('device_type.txt', 'a') as firmware_type, open('complete.txt', 'a') as done, \
    #     open('firmware_needed.txt', 'a') as needed, open('Error.txt', 'w') as err:
        IP = conn_params['ip']
        total.add(IP)
        try:
            with ConnectHandler(**conn_params) as conn:
                connected.add(IP)
                flag = False
                image = conn.send_command_timing('dir').splitlines()
                for key, value in Cisco_devices.items():
                    firmware = value[0]
                    for line in image:
                        if firmware in line:
                            flag = True
                            filesize = value[1]
                            print(f'{IP} firmware is present')
                            if filesize in line:
                                print(' ^   ^   ^ filesize is correct')
                                if 'isr' or 'c1100' == key:
                                    boot_command = [f'boot system flash bootflash:{firmware}']
                                    wrong_boot_command1 = f'boot system flash:{firmware}'
                                    wrong_boot_command2 = f'boot system flash bootflash:/{firmware}'
                                    check_boot_command = conn.send_command_timing('sh run | i boot system').splitlines()
                                    check_current_firmware = conn.send_command_timing(f'sh ver | i image')
                                    print(f' ^   ^   ^ {check_boot_command[0]}')
                                    if 'isr' in firmware:
                                        if conn_params['username'] == 'V459663':
                                            firmware_type.append(f'{IP} is an ISR, tacacs\n')
                                            print(' ^   ^   ^ ISR, tacacs')
                                        elif conn_params['username'] == 'MSOD_Admin':
                                            firmware_type.append(f'{IP} is an ISR, local login\n')
                                            print(' ^   ^   ^ ISR, local login')
                                    elif 'c1100' in firmware:
                                        if conn_params['username'] == 'V459663':
                                            firmware_type.append(f'{IP} is a c1100, tacacs\n')
                                            print(' ^   ^   ^ c1100, tacacs')
                                        elif conn_params['username'] == 'MSOD_Admin':
                                            firmware_type.append(f'{IP} is a c1100, local login\n')
                                            print(' ^   ^   ^ c1100, local login')
                                elif 'c2900' or 'c3900' == key:
                                    boot_command = [f'boot system flash0 {firmware}']
                                    check_boot_command = conn.send_command_timing('sh run | i boot system').splitlines()
                                    check_current_firmware = conn.send_command_timing(f'sh ver | i image')
                                    print(f' ^   ^   ^ {check_boot_command}')
                                    if 'c2900' in firmware:
                                        if conn_params['username'] == 'V459663':
                                            firmware_type.append(f'{IP} is a c2900, tacacs\n')
                                            print(' ^   ^   ^ ISR, tacacs')
                                        elif conn_params['username'] == 'MSOD_Admin':
                                            firmware_type.append(f'{IP} is an c2900, local login\n')
                                            print(' ^   ^   ^ c2900, local login')
                                    elif 'c3900' in firmware:
                                        if conn_params['username'] == 'V459663':
                                            firmware_type.append(f'{IP} is a c3900, tacacs\n')
                                            print(' ^   ^   ^ c2900, tacacs')
                                        elif conn_params['username'] == 'MSOD_Admin':
                                            firmware_type.append(f'{IP} is an c3900, local login\n')
                                            print(' ^   ^   ^ ISR, local login')
                                elif 'c800' or 'c880' == key:
                                    boot_command = [f'boot system flash:{firmware}']
                                    check_boot_command = conn.send_command_timing('sh run | i boot system').splitlines()
                                    check_current_firmware = conn.send_command_timing(f'sh ver | i image')
                                    print(f' ^   ^   ^ {check_boot_command}')
                                    if 'c800' in firmware:
                                        if conn_params['username'] == 'V459663':
                                            firmware_type.append(f'{IP} is a c800, tacacs\n')
                                            print(' ^   ^   ^ c800, tacacs')
                                        elif conn_params['username'] == 'MSOD_Admin':
                                            firmware_type.append(f'{IP} is an c800, local login\n')
                                            print(' ^   ^   ^ c800, local login')
                                    elif 'c880' in firmware:
                                        if conn_params['username'] == 'V459663':
                                            firmware_type.append(f'{IP} is a c880, tacacs\n')
                                            print(' ^   ^   ^ c880, tacacs')
                                        elif conn_params['username'] == 'MSOD_Admin':
                                            firmware_type.append(f'{IP} is an c880, local login\n')
                                            print(' ^   ^   ^ c880, local login')
                                if firmware in check_current_firmware:
                                    done.append(f'{IP} {check_current_firmware}\n')
                                    print(' ^   ^   ^ running on latest firmware')
                                    results.wirte(f'{IP} complete\n')
                                    complete.add(IP)
                                    continue
                                if not check_boot_command:
                                    results.append(f'{IP}: firmware is present, boot command not present, added new boot command\n')
                                    reload.append(f'{IP}\n')
                                    conn.send_config_set(boot_command)
                                    conn.save_config()
                                    print(' ^   ^   ^ boot command not found, added new boot command')
                                    relaod_ready.add(IP)
                                    continue
                                elif firmware not in check_boot_command[0]:
                                    remove_boot_command = []
                                    for command in check_boot_command:
                                        remove_boot_command.append(f'no {command}')
                                    conn.send_config_set(remove_boot_command)
                                    conn.send_config_set(boot_command)
                                    conn.save_config()
                                    results.append(f'{IP}: frimware is present, boot command is not correct, now corrected\n')
                                    print(' ^   ^   ^ removed old boot commands, added new boot command, reload ready')
                                    relaod_ready.add(IP)
                                    reload.append(f'{IP}\n')
                                    continue
                                elif firmware in check_boot_command[0]:
                                    if 'isr' or 'c1100' in firmware:
                                        if check_boot_command[0] == wrong_boot_command1:
                                            remove_wrong_boot = []
                                            remove_wrong_boot.append(f'no {wrong_boot_command1}')
                                            conn.send_config_set(remove_wrong_boot)
                                            conn.send_config_set(boot_command)
                                            conn.save_config()
                                            print(' ^   ^   ^ bootflash has been removed')
                                            results.append(f'{IP}: flash:firmware was changed to bootflash:firmware\n')
                                            reload.append(f'{IP}\n')
                                            relaod_ready.add(IP)
                                            continue
                                        elif check_boot_command[0] == wrong_boot_command2:
                                            remove_wrong_boot = []
                                            remove_wrong_boot.append(f'no {wrong_boot_command2}')
                                            conn.send_config_set(remove_wrong_boot)
                                            conn.send_config_set(boot_command)
                                            conn.save_config()
                                            print(' ^   ^   ^ bootflash:\\ has been removed')
                                            results.append(f'{IP}: bootflash:\\firmware was changed to bootflash:firmware\n')
                                            reload.append(f'{IP}\n')
                                            relaod_ready.add(IP)
                                            continue
                                    results.append(f'{IP} {check_boot_command} - reload ready\n')
                                    print(' ^   ^   ^ is reload ready')
                                    relaod_ready.add(IP)
                                    continue
                            elif filesize not in line:
                                print(' ^   ^   ^ Firmware has wrong filesize, it is corrupted')
                                conn.send_command_timing(f'delete flash:{firmware}')
                                conn.send_command_timing('\n')
                                conn.send_command_timing('\n')
                                results.append(f'{IP} has a corrupted filesize, removed the firmware, push it out again\n')
                                wrong_filesize.add(IP)
                                continue
                        elif firmware not in line:
                            continue
                if not flag:
                    print(f'{IP} does not have the desired image')
                    results.append(f'{IP}: Does not have the firmware uploaded\n')
                    needed.append(f'{IP}\n')
                    need_firmware.add(IP)
                    raise ValueError
        except ValueError:
            err.append(f'{IP} does not have desired firmware\n')
            print(' ^   ^   ^ except ValueError rose')
        except Auth:
            err.append(f'{IP} wrong credentials are being used\n')
            print(' ^   ^   ^ except Auth rose')
        except Timeout:
            err.append(f'{IP} has timedout\n')
            print(' ^   ^   ^ except Timeout rose')
        except:
            err.append(f'{IP} has an other error\n')
            print(' ^   ^   ^ except catch all rose')
        print(results)

def main():
    params = conn_params_EID()
    for param in params.values():
        with cf.ProcessPoolExecutor() as executor:
            executor.submit(Display_firmware_per_device, param)
            # executor.submit(Display_firmware_per_device, conn_params_local)
    print(f'Devices that need the new firmware pushed to it = {len(need_firmware)}')
    print(f'Devices with a corrupted firmware file = {len(wrong_filesize)}')
    print(f'Devices ready to be reloaded = {len(relaod_ready)}')
    print(f'Devices using the new firmware = {len(complete)}')
    print(f'Devices connected to and processed = {len(connected)}')
    print(f'Devices in the IP file = {len(total)}')

with open('Results.txt', 'a') as Results, open('reload_list.txt', 'a') as Reload, \
    open('device_type.txt', 'a') as Firmware_type, open('complete.txt', 'a') as Done, \
    open('firmware_needed.txt', 'a') as Needed, open('Error.txt', 'w') as Err:
    Results.write(results.split('\n'))
    Reload.write(reload.split('\n'))
    Firmware_type.write(firmware_type.split('\n'))
    Done.write(done.split('\n'))
    Needed.write(needed.split('\n'))
    Err.write(err.split('\n'))

if __name__ == '__main__':
    main()
