import concurrent.futures as cf
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException
from netmiko.exceptions import NetmikoTimeoutException as Timeout
from paramiko.ssh_exception import SSHException


filelist = r'devices.txt'
errorlist = r'error_ips.txt'
exportlist = r'Inventory_Results.csv'


def ClearErrorfile():
	file = open(errorlist,'w')
	file.close()

def FetchIPs():	
    ips = []
    with open(filelist, 'r') as devices:
        devices = devices.read().splitlines()
        ips = [ip for ip in devices if ip and ip not in ['0', 'None']]
    return ips

def ExportResults(ip, hostname, hw_version, fw_version, serial, note):
	with open(exportlist, 'a') as file:
		file.write(f'{ip}, {hostname}, {hw_version}, {fw_version}, {serial}, {note}\r')

def create_device_params(ips):
	all_devices_params = {}
	for ip in ips:
		all_devices_params[ip] = {
			'device_type': 'fortinet',
			'ip': ip,
			'username': 'user',
			'password': 'pass',
			'secret': 'pass'
			}
	return all_devices_params

def Get_Device_Info(device):
	hostname, hw_version, fw_version, serial, note = '','','','',''
	try:
		print('#'*10)
		with ConnectHandler(**device) as net_connect:
			output = net_connect.send_command('get system status | grep "Version:\|Hostname:\|Serial-Number:"',
			read_timeout=10, expect_string=r'#')
			ip = device['ip']
			print(f'Connected to {ip}: ')
			print(output)
			for line in output.splitlines():
				if 'Hostname:' in line:
					hostname = line.split(':')[1].strip()
				if 'Version:' in line:
					hw_version = line.split(':')[1].split()[0].strip()
					fw_version = line.split(':')[1].split()[1].split(',')[0].strip()
				if 'Serial-Number:' in line:
					serial = line.split(':')[1].strip()
			print('#'*10)
			ExportResults(ip, hostname, hw_version, fw_version, serial, note)
	except NetmikoAuthenticationException:
		ip = device['ip']
		note = 'Authentication failure'
		print(f'Authentication failure to {ip}')
		with open(errorlist, 'a') as file:
			file.write(f'{ip} wrong credentials are being used\n')
		ExportResults(ip, hostname, hw_version, fw_version, serial, note)
	except Timeout:
		ip = device['ip']
		note = 'Connection timed out'
		print(f'Connection timeout to {ip}')
		with open(errorlist, 'a') as file:
			file.write(f'{ip} has timeout\n')
		ExportResults(ip, hostname, hw_version, fw_version, serial, note)
	except SSHException:
		ip = device['ip']
		note = 'SSH not working'
		print(f'SSH not working to {ip}')
		with open(errorlist, 'a') as file:
			file.write(f'{ip} has timeout\n')
	except Exception as e:
		ip = device['ip']
		note = 'unknown error'
		if 'Pattern not detected' in note or 'Unexpected FortiOS' in note:
			note = 'non-Fortigate device'
		print(f'Other issue to {ip}')
		with open(errorlist, 'a') as file:
			file.write(f'{ip} has an other error\n')
		ExportResults(ip, hostname, hw_version, fw_version, serial, note)

def main():
	ClearErrorfile()
	ips = FetchIPs()
	with open(exportlist,'w') as file:
		file.write('Device IP' + ',' + 'Hostname' + ',' + 'Model' + ',' + 'Current Fimrware' + ',' + 'Serial' + ',' + 'Note' + '\n')
	all_devices_params = create_device_params(ips)
	with cf.ProcessPoolExecutor() as executor:
		for device in all_devices_params.values():
			executor.submit(Get_Device_Info, device)

if __name__ == '__main__':
    main()