from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException
from netmiko.exceptions import NetmikoTimeoutException

Cisco_devices = {
    'c800': "c800-universalk9-mz.SPA.158-3.M9.bin",
    'c1100': "c1100-universalk9.17.06.03a.SPA.bin",
    'isr': "isr4400-universalk9.17.06.03a.SPA.bin",
    'c2900': "c2900-universalk9-mz.SPA.157-3.M8.bin",
    'c880': "c880data-universalk9_npe-mz.154-3.M10.bin"}

with open('IP.txt', 'r') as devices:
    for IP in devices:
        IP = IP.rstrip('\n')
        try:
            device_params = {
                'device_type': 'cisco_ios',
                'ip': IP,
                'username': 'EID/VID'
                'password': 'pass'
                'secret': 'pass'
            }
            print(IP)
            with ConnectHandler(**device_params) as conn:
                for key, value in Cisco_devices.items():
                    global flag
                    flag = False
                    image = conn.send_command(f'sh ver | i {key}')
                    if key in image:
                        current_image = image.splitlines()
                        print(current_image[0])
                        flag = True
                        break
                    else:
                        continue
                if flag is not True:
                    print('The device does not have the image')
                    raise ValueError
                for key, value in Cisco_devices.items():
                    global flag2
                    flag2 = False
                    boot = conn.send_command(f'sh run | i boot system')
                    if key in boot:
                        flag2 = True
                        print(boot)
                        break
                    else:
                        continue
                if flag2 is not True:
                    print('The device does not have the boot command')
                    raise ValueError
                print('********************\n********************')
        except ValueError:
            print("Either firmware wasn't pushed, or boot from firmware not set")
            with open('Error.txt', 'a') as err:
                err.write(f"{IP} - Either firmware wasn't pushed, or boot from frimware not set\n")
            print('********************\n********************')
            continue
        except NetmikoAuthenticationException:
            with open('Error.txt', 'a') as auth:
                auth.write(f'{IP} - Auth error\n')
                print('Authentication error')
            print('********************\n********************')
            continue
        except  NetmikoTimeoutException:
            with open('Error.txt', 'a') as time:
                time.write(f'{IP} - Timedout\n')
                print('Timeout')
            print('********************\n********************')
            continue
        except:
            with open('Error.txt', 'a') as other:
                other.write(f'{IP} - Other error\n')
                print('Other error')
                continue
            print('********************\n********************')
