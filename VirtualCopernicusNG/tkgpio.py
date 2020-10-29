import os

from .base import TkDevice, SingletonMeta
from .base import PreciseMockTriggerPin, PreciseMockFactory, PreciseMockChargingPin
from gpiozero import Device
from gpiozero.pins.mock import MockPWMPin
from PIL import ImageEnhance, Image, ImageTk
from sounddevice import play, stop
import numpy
import scipy.signal
from tkinter import Tk, Frame, Label, Button, Scale, HORIZONTAL, VERTICAL, CENTER, Canvas
from threading import Thread, Timer
from sys import path, exit
from pathlib import Path
from math import sqrt, cos, sin


class TkCircuit(metaclass=SingletonMeta):
    def __init__(self, setup):
        Device.pin_factory = PreciseMockFactory(pin_class=MockPWMPin)
        
        path.insert(0, str(Path(__file__).parent.absolute()))
        
        default_setup = {
            "name": "Virtual GPIO",
            "width": 500, "height": 500,
            "leds":[], "buzzers":[], "buttons":[],
            "servos":[]
        }
        
        default_setup.update(setup)
        setup = default_setup
                
        self._root = Tk()
        self._root.title(setup["name"])
        self._root.geometry("%dx%d" % (setup["width"], setup["height"]))
        self._root.resizable(False, False)
        self._root["background"] = "white"

        self._root.protocol("WM_DELETE_WINDOW", self._on_closing)

        background_label = Canvas(self._root)
        if "sheet" in setup.keys():
            current_folder = str(Path(__file__).parent.absolute())
            file_path = current_folder + "/images_copernicus/" + setup['sheet']
            background_image = ImageTk.PhotoImage(file=file_path)
            background_label.create_image(0,0,image = background_image, anchor="nw")
            #dirty hack
            self._bk_image = background_image
        background_label.pack()
        self._bg_canvas = background_label

        self._outputs = []
        self._outputs += [self.add_device(TkLED, parameters) for parameters in setup["leds"]]
        self._outputs += [self.add_device(TkBuzzer, parameters) for parameters in setup["buzzers"]]

        for parameters in setup["servos"]:
            parameters.update({"bg_canvas": self._bg_canvas})
            self._outputs += [self.add_device(TkServo, parameters)]

        for parameters in setup["buttons"]:
            self.add_device(TkButton, parameters)


    def add_device(self, device_class, parameters):
        return device_class(self._root, **parameters)
        
    def run(self, function):
        thread = Thread(target=function, daemon=True)
        thread.start()
        
        self._root.after(10, self._update_outputs)
        self._root.mainloop()
        
    def _update_outputs(self):
        for output in self._outputs:
            output.update()
            
        self._root.after(10, self._update_outputs)
        
    def update_lcds(self, pins, text):
        for lcds in self._lcds:
            lcds.update_text(pins, text)
            
    def _on_closing(self):
        exit()


class TkBuzzer(TkDevice):
    SAMPLE_RATE = 44000
    PEAK = 0.1
    DUTY_CICLE = 0.5
    
    def __init__(self, root, x, y, name, pin, frequency=440):
        super().__init__(root, x, y, name)
        
        self._pin = Device.pin_factory.pin(pin)
        self._previous_state = None
        
        self._set_image_for_state("buzzer_on.png", "on", (50, 33))
        self._set_image_for_state("buzzer_off.png", "off", (50, 33))
        self._create_main_widget(Label, "off")
        
        if frequency != None:
            n_samples = self.SAMPLE_RATE
            t = numpy.linspace(0, 1, int(500 * 440/frequency), endpoint=False)
            wave = scipy.signal.square(2 * numpy.pi * 5 * t, duty=self.DUTY_CICLE)
            wave = numpy.resize(wave, (n_samples,))
            self._sample_wave = (self.PEAK / 2 * wave.astype(numpy.int16))
        else:
            self._sample_wave = numpy.empty(0)
        
    def update(self):
        if self._previous_state != self._pin.state:
            if self._pin.state == True:
                self._change_widget_image("on")
                if len(self._sample_wave) > 0:
                    play(self._sample_wave, self.SAMPLE_RATE, loop=True)
            else:
                self._change_widget_image("off")
                if len(self._sample_wave) > 0:
                    stop()
            
            self._previous_state = self._pin.state
            
            self._redraw()
    

class TkLED(TkDevice):
    on_image = None
    
    def __init__(self, root, x, y, name, pin):
        super().__init__(root, x, y, name)
        
        self._pin = Device.pin_factory.pin(pin)
        
        self._previous_state = None
        
        TkLED.on_image = self._set_image_for_state("led_on.png", "on")
        self._set_image_for_state("led_off.png", "off")

        self._create_main_widget(Label, "off")

        self._widget.config(borderwidth=0, highlightthickness=0, background="white")
        
    def update(self):
        #print("LED updated!")
        if self._previous_state != self._pin.state:
            if isinstance(self._pin.state, float):
                converter = ImageEnhance.Color(TkLED.on_image)
                desaturated_image = converter.enhance(self._pin.state)
                self._change_widget_image(desaturated_image)
            elif self._pin.state == True:
                self._change_widget_image("on")
            else:
                self._change_widget_image("off")
             
            self._previous_state = self._pin.state
            
            self._redraw()
        
        
class TkButton(TkDevice):
    def __init__(self, root, x, y, name, pin):
        super().__init__(root, x, y, name)
        
        self._pin = Device.pin_factory.pin(pin)
        
        self._set_image_for_state("button_pressed.png", "on", (15, 15))
        self._set_image_for_state("button_released.png", "off", (15, 15))
        self._create_main_widget(Button, "off")
        self._widget.config(borderwidth=0,highlightthickness = 0,background="white")
        self._widget.bind("<ButtonPress>", self._on_press)
        self._widget.bind("<ButtonRelease>", self._on_release)
        
    def _on_press(self, botao):
        self._change_widget_image("on")
        
        thread = Thread(target=self._change_pin, daemon=True, args=(True,))
        thread.start()

    def _on_release(self, botao):
        self._change_widget_image("off")
        
        thread = Thread(target=self._change_pin, daemon=True, args=(False,))
        thread.start()
        
    def _change_pin(self, is_press):
        if is_press:
            self._pin.drive_low()
        else:
            self._pin.drive_high()


class TkServo(TkDevice):
    on_image = None

    def __init__(self, root, x, y, name, pin, bg_canvas, length):
        super().__init__(root, x, y, name)

        self._pin = Device.pin_factory.pin(pin)
        self._bg_canvas = bg_canvas
        self._length = length

    def update(self):

        angle = ((self._pin.state-0.05) / 0.05) * 180
        angle = angle/180 * 3.14

        self._bg_canvas.delete("my_tag")
        self._bg_canvas.create_line(self._x, self._y, cos(angle)*self._length*-1 + self._x, sin(angle)*self._length*-1 + self._y, tags='my_tag', fill="red", width=3)

        self._redraw()