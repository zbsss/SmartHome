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
        if self.local:
            self._local_command(command)
        else:
            self._non_local_command(command)
        self.lock.release()

    def _non_local_command(self, operation='toggle'):
        """
        If the device is not local we send the request and wait for the response with on/off message
        only then do we change the state of the local LED
        """

        if operation == 'on':
            self.led.on()
        elif operation == 'off':
            self.led.off()
        else:
            self.send(f"{self.floor};{self.room};{self.type};{self.id};toggle")

    def _local_command(self, operation='toggle'):
        """
        Button function for the local device
        """

        if operation == 'toggle':
            self.led.toggle()
        elif operation == 'on':
            self.led.on()
        elif operation == 'off':
            self.led.off()
        else:
            raise ValueError(f"Wrong operation {operation}!")

        # we have to notify that the state of the light changed so that other devices can update it
        self.send(f"{self.floor};{self.room};{self.type};{self.id};{'on' if self.led.is_active else 'off'}")


