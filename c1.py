from time import sleep
from threading import Thread
from device import Device
from config import *


def send(msg):
    """
    Sending messages to other devices
    """
    print('SENT: "%s"' % msg)
    send_sock.sendto(msg.encode('utf-8'), (MCAST_GRP, MCAST_PORT))


# Create devices
DEVICES = [
    Device('f1', 'living room', 'lamp', '1', True,  button1, led1, send, lock),
    Device('f1', 'kitchen', 'lamp', '1', False,  button2, led2, send, lock)
]


def receiver():
    while True:
        command = rcv_sock.recv(10240)
        command = command.decode("utf-8").split(';')
        print('RECEIVED: ', command)
        for device in DEVICES:
            if device.is_addressed(command):
                if not device.local and command[-1] == 'toggle':
                    continue
                device.exec_command(command[-1])


@circuit.run
def main():
    button1.when_pressed = DEVICES[0].exec_command
    button2.when_pressed = DEVICES[1].exec_command

    # start rcv in thread
    thread = Thread(target=receiver, daemon=True)
    thread.start()

    while True:
        sleep(0.1)


if __name__ == '__main__':
    main()
