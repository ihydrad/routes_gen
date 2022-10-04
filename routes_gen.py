import requests
import json
import argparse
from json import JSONDecodeError
from ipaddress import ip_address, ip_network, IPv4Interface
import sys


headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'PostmanRuntime/7.29.0',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br'
}

def post(target, endpoint: str, data: dict) -> dict:
    url = f'http://{target}:8080/hsm/api/copper/{endpoint}'
    return requests.post(url, headers=headers, data=json.dumps(data))

def get(target, endpoint: str) -> dict:
    url = f'http://{target}:8080/hsm/api/copper/{endpoint}'
    return requests.get(url)

def return_with_check_status(response):
    status = str(response.status_code)
    if status.startswith("4") or status.startswith("5"):
        raise Exception(f"status code: {response.status_code}\n{response.text}")
    try:
        res = json.loads(response.text)
        return res
    except JSONDecodeError:
        return response.text

def route_add(target, adapter, network_address, network_mask, gateway_address, metric):
    endpoint_route_add = "settings/network_route/"
    payload = {
        "network_address": network_address,
        "network_mask": network_mask,
        "gateway_address": gateway_address,
        "adapter": adapter,
        "metric": metric
    }
    res = post(target, endpoint_route_add, payload)
    return return_with_check_status(res)
 
def generate_routes(hsm, adapter, adapter_addr, start, count):
    ip = ip_address(start if start else "192.168.0.1")
    for i in range(count):
        print(f"route#{i+1}: ", end="")
        ip = ip + 4
        iface = IPv4Interface(ip.__str__() + "/30")
        network_address = iface.network.__str__()
        network_address = network_address.split("/")[0]
        gateway_address = ip_address(adapter_addr) + 1
        gateway_address = gateway_address.__str__()
        res = route_add(target=hsm, adapter=adapter, network_address=network_address, network_mask=30, gateway_address=gateway_address, metric=2)
        print(res)

def get_addr_for(target, adapter:int):
    endpoint_get_adapter = f"settings/network_adapter/{adapter}"
    res = get(target, endpoint_get_adapter)
    data =  return_with_check_status(res)
    return data["network_adapter"]["ipv4_addr"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Routes generator by @ihydrad')
    parser.add_argument('--target', type=str, required=True, help='IP-address HSM: [routes_gen.py --target 172.16.56.3 --adapter 1 --count 256]')
    parser.add_argument('--adapter', type=str, required=True, help='id адаптера через который будет проходить маршрут')
    parser.add_argument('--count', type=int, required=True, help='Количество добавляемых маршрутов')
    parser.add_argument('--start', type=str, help='с какого адреса начать')
    args = parser.parse_args()
    try:
        ip_address(args.target)
        if args.start:
            ip_address(args.start)
    except:
        print("Неверный ip-адрес")
        sys.exit(1)
    if not args.count or args.count > 256:
        print("Количество маршрутов можно указать от 1 до 256")
        sys.exit(1)
    adapters = ['0', '1', '2', '3', '10', '11', '12', '13']
    if args.adapter not in adapters:
        print("Введите адаптер из списка" + str(adapters))
        sys.exit(1)
    adapter_addr = get_addr_for(args.target, adapter=args.adapter)
    generate_routes(hsm=args.target, adapter=args.adapter, adapter_addr=adapter_addr, start=args.start, count=args.count)
