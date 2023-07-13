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
                        if line.find(firmware) >= 0:
                            image = line
                            boot_command = [f'boot system flash:{firmware}']
                            check_boot_command = conn.send_command('sh run | i boot system').splitlines()
                            print(f'{IP} {check_boot_command}')
                            flag = True
                            if check_boot_command[0].find(firmware) >= 0:
                                results.write(f'{IP}:\n{image}\n{check_boot_command}\n\n')
                            # elif check_boot_command[0] == '':
                            #     results.write(f'{IP}:\nfrimware is present, but boot command is not configured\n\n')
                            #     conn.send_config_set(boot_command)
                            #     print('added new boot command')
                            elif firmware not in check_boot_command:
                                if check_boot_command == []:
                                    results.write(f'{IP}:\nfrimware is present, but boot command is not present\n\n')
                                    conn.send_config_set(boot_command)
                                    print('added new boot command')
                                elif check_boot_command[0] != firmware:
                                    results.write(f'{IP}:\nfrimware is present, but boot command is not correct\n\n')
                                    remove_boot_command = []
                                    for command in check_boot_command:
                                        remove_boot_command.append(f'no {command}')
                                    conn.send_config_set(remove_boot_command)
                                    print('removed old boot commands')
                                    conn.send_config_set(boot_command)
                                    print('added new boot command')
                        elif line.find(firmware) == -1:
                            continue
                        if flag is not True:
                            print(f'{IP} does not have the desired image')
                            results.write(f'{IP}: Does not have the firmware uploaded\n')
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
