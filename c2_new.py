from time import sleep
from threading import Thread
from device import Device
from config import *


# configuration of this circuit
#Todo
NAME = 'c2'
FLOOR = 'f1'
ROOM = 'kitchen'


def send(msg):
    """
    Sending messages to other devices
    """
    msg = NAME + ';' + msg
    print('SENT: "%s"' % msg)
    send_sock.sendto(msg.encode('utf-8'), (MCAST_GRP, MCAST_PORT))

# Todo
DEVICES = [
    Device('f1', 'living room', 'lamp', '1', False,  button1, led1, send, lock),
    Device('f1', 'kitchen', 'lamp', '1', True,  button2, led2, send, lock)
]


def receiver():
    """
    When receiving messages we need  to check it the message is not coming from
    ourselves because that can couse a loop. Thats why to every message I attach the sender name
    """
    while True:
        command = rcv_sock.recv(10240)
        command = command.decode("utf-8").split(';')
        print('RECEIVED: ', command)
        if command[0] != NAME:
            command = command[1:]
            for device in DEVICES:
                if device.is_addressed(command):
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
