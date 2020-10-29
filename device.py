import time

class Device:
    def __init__(self, floor, room, type, id, local, button, led, send, lock):
        self.lock = lock
        self.send = send
        self.led = led
        self.button = button
        self.local = local
        self.id = id
        self.type = type
        self.room = room
        self.floor = floor

    def is_addressed(self, msg):
        return msg[0] in [self.floor, '*'] and \
                msg[1] in [self.room, '*'] and \
                msg[2] in [self.type, '*'] and \
                msg[3] in [self.id, '*']

    def exec_command(self, command='toggle'):
        self.lock.acquire()

        before = self.led.is_active

        if command == 'on':
            self.led.on()
        elif command == 'off':
            self.led.off()
        if command == 'toggle':
            if self.local:
                self.led.toggle()
            else:
                # if you want to toggle a non local device you need to send a request
                self.send(f"{self.floor};{self.room};{self.type};{self.id};toggle")

        if self.local and self.led.is_active != before:
            # after changing state of the local device, you need to notify all the other circuits of it's new state
            self.send(f"{self.floor};{self.room};{self.type};{self.id};{'on' if self.led.is_active else 'off'}")

        self.lock.release()
