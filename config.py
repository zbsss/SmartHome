from VirtualCopernicusNG import TkCircuit
from gpiozero import LED, Button
import socket
import struct
from threading import Lock

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
