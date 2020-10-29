from VirtualCopernicusNG import TkCircuit
from gpiozero import LED, Button
from time import sleep
import socket
import struct
from threading import Thread, Lock

configuration = {
    "name": "CopernicusNG SmartHouse",
    "sheet": "sheet_smarthouse.png",
    "width": 332,
    "height": 300,
    "leds": [
        {"x": 112, "y": 70, "name": "LED 1", "pin": 21},
        {"x": 71, "y": 141, "name": "LED 2", "pin": 22}
    ],
    "buttons": [
        {"x": 242, "y": 146, "name": "Button 1", "pin": 11},
        {"x": 200, "y": 217, "name": "Button 2", "pin": 12},
    ],
    "buzzers": [
        {"x": 277, "y": 9, "name": "Buzzer", "pin": 16, "frequency": 440},
    ]
}

MCAST_GRP = "236.0.0.0"
MCAST_PORT = 3456

# Socket for sending messages to devices
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

# Socket for receiving messages from other controllers
rcv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
rcv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
rcv_sock.bind(('', MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
rcv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# lock for concurrency
lock = Lock()

# create the circuit
circuit = TkCircuit(configuration)
led1 = LED(21)
led2 = LED(22)
button1 = Button(11)
button2 = Button(12)

# configuration of all the devices and rooms in this circuits range/territory
my_range = {"name": "c2", # name of the circuit
            "floor": "f1",
            "rooms": [
                {
                    "name": "living room",
                    "devices": [
                        {"id": '1', "type": "lamp", "local": False}
                    ]
                },
                {
                    "name": "kitchen",
                    "devices": [
                         {"id": '1', "type": "lamp", "local": True}
                    ]
                }
            ]}


def send(msg):
    """
    Sending messages to other devices
    """
    print('SENT: "%s"' % msg)
    send_sock.sendto(msg.encode('utf-8'), (MCAST_GRP, MCAST_PORT))


def local(operation='toggle'):
    """
    Button function for the local device
    """
    lock.acquire()

    print("Button 2 pressed")

    if operation == 'toggle':
        led2.toggle()
    elif operation == 'on':
        led2.on()
    elif operation == 'off':
        led2.off()
    else:
        raise ValueError("Wrong operation!")

    # we have to notify that the state of the light changed so that other devices can update it
    send(f"{my_range['name']};f1;kitchen;lamp;1;{'on' if led2.is_active else 'off'}")

    lock.release()


def non_local(operation='toggle'):
    """
    Button function for the nonlocal device
    """
    lock.acquire()

    print("Button 1 pressed")

    """
    If the device is not local we send the request and wait for the response with on/off message
    only then do we change the state of the local LED
    """

    if operation == 'on':
        led1.on()
    elif operation == 'off':
        led1.off()
    else:
        send(f"{my_range['name']};f1;living room;lamp;1;toggle")

    lock.release()


def run_command(command):
    """
    Checks if the received command applies to this device, if so runs the command
    """
    if command[0] in [my_range['floor'], '*']:
        for room in my_range['rooms']:
            if command[1] in [room['name'], '*']:
                for device in room['devices']:
                    if command[2] in [device['type'], '*'] and command[3] in [device['id'], '*']:
                        if device['local']:
                            local(command[4])
                        # if this device is not local ignore the command
                        else:
                            non_local(command[4])


def receiver():
    """
    When receiving messages we need  to check it the message is not coming from
    ourselves because that can couse a loop. Thats why to every message I attach the sender name
    :return:
    """
    while True:
        command = rcv_sock.recv(10240)
        command = command.decode("utf-8").split(';')
        print('RECEIVED: ', command)
        if command[0] != my_range['name']:
            run_command(command[1:])


@circuit.run
def main():
    button1.when_pressed = non_local
    button2.when_pressed = local

    # start rcv in thread
    thread = Thread(target=receiver, daemon=True)
    thread.start()

    while True:
        sleep(0.1)


if __name__ == '__main__':
    main()