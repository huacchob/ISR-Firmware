import concurrent.futures as cf
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException as Auth
from netmiko.exceptions import NetmikoTimeoutException as Timeout

Cisco_devices = {
    'c800': "c800-universalk9-mz.SPA.158-3.M9.bin",
    'c1100': "c1100-universalk9.17.06.03a.SPA.bin",
    'isr': "isr4400-universalk9.17.06.03a.SPA.bin",
    'c2900': "c2900-universalk9-mz.SPA.157-3.M8.bin",
    'c880': "c880data-universalk9_npe-mz.154-3.M10.bin"}

with open('IP.txt', 'r') as devices:
    global IPs
    IPs = [IP for IP in devices.read().splitlines()]

def create_device_params():
    all_devices_params = {}
    for IP in IPs:
        IP = IP.rstrip('\n')
        all_devices_params[IP] = {
            'device_type': 'cisco_ios',
            'ip': IP,
            'username': 'user',
            'password': 'pass',
            'secret': 'pass'
        }
    return all_devices_params

def Display_firmware_per_device(device):
    try:
        IP = device['ip']
        with open('Results.txt', 'a') as results:
            with ConnectHandler(**device) as conn:
                flag = False
                image = conn.send_command('dir').splitlines()
                for firmware in Cisco_devices.values():
                    for line in image:
                        if firmware in line:
                            image = line
                            boot_command = [f'boot system flash:{firmware}']
                            wrong_boot_command1 = f'boot system flash bootflash:{firmware}'
                            wrong_boot_command2 = f'boot system flash bootflash:/{firmware}'
                            check_boot_command = conn.send_command('sh run | i boot system').splitlines()
                            print(f'{IP} {check_boot_command}')
                            flag = True
                            if not check_boot_command:
                                results.write(f'{IP}: firmware is present, but boot command is not present, added boot command\n')
                                conn.send_config_set(boot_command)
                                print('boot command not found, added new boot command')
                                break
                            if firmware not in check_boot_command[0]:
                                results.write(f'{IP}: frimware is present, but boot command is not correct\n')
                                remove_boot_command = []
                                for command in check_boot_command:
                                    remove_boot_command.append(f'no {command}')
                                conn.send_config_set(remove_boot_command)
                                print('removed old boot commands')
                                conn.send_config_set(boot_command)
                                print('added new boot command')
                                break
                            if firmware in check_boot_command[0]:
                                if check_boot_command[0] == wrong_boot_command1:
                                    remove_wrong_boot = []
                                    remove_wrong_boot.append(f'no {wrong_boot_command1}')
                                    conn.send_config_set(remove_wrong_boot)
                                    conn.send_config_set(boot_command)
                                    print('bootflash has been removed')
                                    results.write(f'{IP}: bootflash:firmware was changed to flash:firmware\n')
                                    break
                                if check_boot_command[0] == wrong_boot_command2:
                                    remove_wrong_boot = []
                                    remove_wrong_boot.append(f'no {wrong_boot_command2}')
                                    conn.send_config_set(remove_wrong_boot)
                                    conn.send_config_set(boot_command)
                                    print('bootflash:\ has been removed')
                                    results.write(f'{IP}: bootflash:\\firmware was changed to flash:firmware\n')
                                    break
                                if check_boot_command == boot_command[0]:
                                    results.write(f'{IP}: {image}\n{check_boot_command}\n\n')
                                    print('no changes made')
                                    break
                                break
                        elif firmware not in line:
                            continue
                        if flag == False:
                            print(f'{IP} does not have the desired image')
                            results.write(f'{IP}: Does not have the firmware uploaded\n\n')
                            with open('firmware_needed.txt', 'a') as needed:
                                needed.write(f'{IP}\n')
                            raise ValueError
    except ValueError:
        with open('Error.txt', 'w') as no_firmware:
            no_firmware.write(f'{IP} does not have desired firmware\n')
    except Auth:
        with open('Error.txt', 'w') as wrong_creds:
            wrong_creds.write(f'{IP} wrong credentials are being used\n')
    except Timeout:
        with open('Error.txt', 'w') as no_connection:
            no_connection.write(f'{IP} has timedout\n')
    else:
        with open('Error.txt', 'w') as other_error:
            other_error.write(f'{IP} has an other error\n')

def main():
    all_devices_params = create_device_params()
    with cf.ProcessPoolExecutor() as executor:
        for device in all_devices_params.values():
            executor.submit(Display_firmware_per_device, device)

if __name__ == '__main__':
    main()
