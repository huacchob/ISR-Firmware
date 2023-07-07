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
    IPs = [IP for IP in devices.read().splitlines()]

def create_device_params(IPs):
    all_devices_params = {}
    for IP in IPs:
        IP = IP.rstrip('\n')
        all_devices_params[IP] = {
            'device_type': 'cisco_ios',
            'ip': IP,
            'username': 'EID/VID',
            'password': 'pass',
            'secret': 'pass'
        }

def Display_firmware_per_device():
    each_device = create_device_params()
    for key, value in each_device:
        try:
            with ConnectHandler(**value) as conn:
                flag = False
                for type, firmware in Cisco_devices:
                    image = conn.send_command(f'sh ver | i {firmware}')
                    if firmware in image:
                        print(image)
                        flag = True
                        break
                    else:
                        continue
                if flag is not True:
                    print(f'{key} does not have the desired image')
                    raise ValueError
        except ValueError:
            with open('Error.txt', 'w') as no_firmware:
                no_firmware.write(f'{key} does not have desired firmware\n')
        except Auth:
            with open('Error.txt', 'w') as wrong_creds:
                wrong_creds.write(f'{key} wrong credentials are being used\n')
        except Timeout:
            with open('Error.txt', 'w') as no_connection:
                no_connection.write(f'{key} has timedout\n')
        else:
            with open('Error.txt', 'w') as other_error:
                other_error.write(f'{key} has an other error\n')

def main():
    with cf.ProcessPoolExecutor as executor:
        executor.submit(Display_firmware_per_device)
