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

with open('IP.txt', 'r') as devices, open('Results.txt', 'a') as results, \
open('reload_list.txt', 'a') as reload, open('device_type.txt', 'a') as firmware_type:
    global IPs
    IPs = [IP for IP in devices.read().splitlines()]

def Display_firmware_per_device():
    # with open('Results.txt', 'a') as results, open('reload_list.txt', 'a') as reload, open('device_type.txt', 'a') as firmware_type:
    for IP in IPs:
        try:
            IP = IP.rstrip('\n')
            device = {
                'device_type': 'cisco_ios',
                'ip': IP,
                'username': '',
                'password': '',
                'secret': ''
            }
            user_and_pass = [
                ('EID', 'EID-Pass'),
                ('Local-user', 'Local-pass')
            ]
            for username, password in user_and_pass:
                device['username'] = username
                device['password'] = password
                device['secret'] = password
                try:
                    with ConnectHandler(**device) as conn:
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
                                        image = line
                                        if 'isr' or 'c1100' == key:
                                            boot_command = [f'boot system flash bootflash:{firmware}']
                                            wrong_boot_command1 = f'boot system flash:{firmware}'
                                            wrong_boot_command2 = f'boot system flash bootflash:/{firmware}'
                                            check_boot_command = conn.send_command_timing('sh run | i boot system').splitlines()
                                            check_current_firmware = conn.send_command_timing(f'sh ver | i image')
                                            print(f' ^   ^   ^ {check_boot_command}')
                                            if 'isr' in firmware:
                                                if device['username'] == 'V459663':
                                                    firmware_type.write(f'{IP} is an ISR, tacacs\n')
                                                    print(' ^   ^   ^ ISR, tacacs')
                                                elif device['username'] == 'MSOD_Admin':
                                                    firmware_type.write(f'{IP} is an ISR, local login\n')
                                                    print(' ^   ^   ^ ISR, local login')
                                            elif 'c1100' in firmware:
                                                if device['username'] == 'V459663':
                                                    firmware_type.write(f'{IP} is a c1100, tacacs\n')
                                                    print(' ^   ^   ^ c1100, tacacs')
                                                elif device['username'] == 'MSOD_Admin':
                                                    firmware_type.write(f'{IP} is a c1100, local login\n')
                                                    print(' ^   ^   ^ c1100, local login')
                                        elif 'c2900' or 'c3900' == key:
                                            boot_command = [f'boot system flash0 {firmware}']
                                            check_boot_command = conn.send_command_timing('sh run | i boot system').splitlines()
                                            check_current_firmware = conn.send_command_timing(f'sh ver | i image')
                                            print(f' ^   ^   ^ {check_boot_command}')
                                            if 'c2900' in firmware:
                                                if device['username'] == 'V459663':
                                                    firmware_type.write(f'{IP} is a c2900, tacacs\n')
                                                    print(' ^   ^   ^ ISR, tacacs')
                                                elif device['username'] == 'MSOD_Admin':
                                                    firmware_type.write(f'{IP} is an c2900, local login\n')
                                                    print(' ^   ^   ^ c2900, local login')
                                            elif 'c3900' in firmware:
                                                if device['username'] == 'V459663':
                                                    firmware_type.write(f'{IP} is a c3900, tacacs\n')
                                                    print(' ^   ^   ^ c2900, tacacs')
                                                elif device['username'] == 'MSOD_Admin':
                                                    firmware_type.write(f'{IP} is an c3900, local login\n')
                                                    print(' ^   ^   ^ ISR, local login')
                                        elif 'c800' or 'c880' == key:
                                            boot_command = [f'boot system flash:{firmware}']
                                            check_boot_command = conn.send_command_timing('sh run | i boot system').splitlines()
                                            check_current_firmware = conn.send_command_timing(f'sh ver | i image')
                                            print(f' ^   ^   ^ {check_boot_command}')
                                            if 'c800' in firmware:
                                                if device['username'] == 'V459663':
                                                    firmware_type.write(f'{IP} is a c800, tacacs\n')
                                                    print(' ^   ^   ^ c800, tacacs')
                                                elif device['username'] == 'MSOD_Admin':
                                                    firmware_type.write(f'{IP} is an c800, local login\n')
                                                    print(' ^   ^   ^ c800, local login')
                                            elif 'c880' in firmware:
                                                if device['username'] == 'V459663':
                                                    firmware_type.write(f'{IP} is a c880, tacacs\n')
                                                    print(' ^   ^   ^ c880, tacacs')
                                                elif device['username'] == 'MSOD_Admin':
                                                    firmware_type.write(f'{IP} is an c880, local login\n')
                                                    print(' ^   ^   ^ c880, local login')
                                        if firmware in check_current_firmware:
                                            with open('complete.txt', 'a') as done:
                                                done.write(f'{IP}\n{check_current_firmware}\n')
                                                print(' ^   ^   ^ running on latest firmware')
                                            results.wirte(f'{IP} complete\n')
                                            continue
                                        if not check_boot_command:
                                            results.write(f'{IP}: firmware is present, boot command not present, added new boot command\n')
                                            reload.write(f'{IP}\n')
                                            conn.send_config_set(boot_command)
                                            conn.save_config()
                                            print(' ^   ^   ^ boot command not found, added new boot command')
                                            continue
                                        elif firmware not in check_boot_command[0]:
                                            remove_boot_command = []
                                            for command in check_boot_command:
                                                remove_boot_command.append(f'no {command}')
                                            conn.send_config_set(remove_boot_command)
                                            conn.send_config_set(boot_command)
                                            conn.save_config()
                                            results.write(f'{IP}: frimware is present, boot command is not correct, now corrected\n')
                                            print(' ^   ^   ^ removed old boot commands, added new boot command, reload ready')
                                            reload.write(f'{IP}\n')
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
                                                    results.write(f'{IP}: flash:firmware was changed to bootflash:firmware\n')
                                                    reload.write(f'{IP}\n')
                                                    continue
                                                elif check_boot_command[0] == wrong_boot_command2:
                                                    remove_wrong_boot = []
                                                    remove_wrong_boot.append(f'no {wrong_boot_command2}')
                                                    conn.send_config_set(remove_wrong_boot)
                                                    conn.send_config_set(boot_command)
                                                    conn.save_config()
                                                    print(' ^   ^   ^ bootflash:\\ has been removed')
                                                    results.write(f'{IP}: bootflash:\\firmware was changed to bootflash:firmware\n')
                                                    reload.write(f'{IP}\n')
                                                    continue
                                            results.write(f'{IP}: {image}\n{check_boot_command}\nreload ready\n\n')
                                            print(' ^   ^   ^ is reload ready')
                                            continue
                                    elif filesize not in line:
                                        print(' ^   ^   ^ Firmware has wrong filesize, it is corrupted')
                                        conn.send_command_timing(f'delete flash:{firmware}')
                                        conn.send_command_timing('\n')
                                        conn.send_command_timing('\n')
                                        results.write(f'{IP} has a corrupted filesize, removed the firmware, push it out again')
                                        continue
                                elif firmware not in line:
                                    continue
                        if not flag:
                            print(f'{IP} does not have the desired image')
                            results.write(f'{IP}: Does not have the firmware uploaded\n')
                            with open('firmware_needed.txt', 'a') as needed:
                                needed.write(f'{IP}\n')
                            raise ValueError
                except Auth:
                    continue
        except ValueError:
            with open('Error.txt', 'w') as no_firmware:
                no_firmware.write(f'{IP} does not have desired firmware\n')
                print(' ^   ^   ^ except ValueError rose')
            continue
        except Auth:
            with open('Error.txt', 'w') as wrong_creds:
                wrong_creds.write(f'{IP} wrong credentials are being used\n')
                print(' ^   ^   ^ except Auth rose')
            continue
        except Timeout:
            with open('Error.txt', 'w') as no_connection:
                no_connection.write(f'{IP} has timedout\n')
                print(' ^   ^   ^ except Timeout rose')
            continue
        except:
            with open('Error.txt', 'w') as other_error:
                other_error.write(f'{IP} has an other error\n')
                print(' ^   ^   ^ except catch all rose')
            continue

# def reload(IP):
#     device = {
#         'device_type': 'cisco_ios',
#         'ip': IP,
#         'username': '',
#         'password': '',
#         'secret': ''}
#     user_and_pass = [
#         ('V459663','M@rBe11a0612')
#         ('MSOD_Admin','Sh@D0wR3@Lm22')
#     ]
#     for username, password in user_and_pass:
#         device['username'] = username
#         device['password'] = password
#         device['secret'] = password
#         try:
#             with ConnectHandler(**device) as conn:
#                 conn.send_command_timing('reload')
#                 conn.send_command('\n')
#         except Auth:
#             continue

def main():
    with cf.ProcessPoolExecutor() as executor:
        executor.submit(Display_firmware_per_device)
    # Uncomment this if you want to reload
    ######################################
    ######################################
    ######################################
    ######################################
    # with open('reload_list.txt', 'r') as reboot:
    #     reboot = reboot.read().splitlines()
    #     for IP in reboot:
    #         IP = IP.rstrip('\n')
    #         executor.submit(reload, IP)

if __name__ == '__main__':
    main()
