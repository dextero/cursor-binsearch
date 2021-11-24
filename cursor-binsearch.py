#!/usr/bin/env python3

import collections
from threading import Event

import pynput
from pynput.keyboard import Key, KeyCode
from screeninfo import get_monitors
import tkinter as tk


Point = collections.namedtuple('Point', ['x', 'y'])


class Rect(collections.namedtuple('RectBase', ['left', 'top', 'right', 'bottom'])):
    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def center_x(self) -> int:
        return (self.left + self.right) // 2

    @property
    def center_y(self) -> int:
        return (self.top + self.bottom) // 2

    @property
    def center(self) -> Point:
        return Point(self.center_x, self.center_y)

    @property
    def left_half(self) -> 'Rect':
        return Rect(self.left, self.top, self.center_x, self.bottom)

    @property
    def right_half(self) -> 'Rect':
        return Rect(self.center_x, self.top, self.right, self.bottom)

    @property
    def top_half(self) -> 'Rect':
        return Rect(self.left, self.top, self.right, self.center_y)

    @property
    def bottom_half(self) -> 'Rect':
        return Rect(self.left, self.center_y, self.right, self.bottom)


def screen_rect() -> Rect:
    monitor = get_monitors()[0]
    return Rect(0, 0, monitor.width, monitor.height)


running = Event()
running.set()
click = Event()
click.clear()

current_rect = screen_rect()
mouse = pynput.mouse.Controller()


class Overlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.wait_visibility(self.root)
        self.root.attributes('-alpha', 0.5)

        self.cells = [
            tk.Canvas(self.root, bg='#4285f4'),
            tk.Canvas(self.root, bg='#ea4335'),
            tk.Canvas(self.root, bg='#fbbc05'),
            tk.Canvas(self.root, bg='#34a853'),
        ]

        for idx, cell in enumerate(self.cells):
            row = idx // 2
            col = idx % 2

            self.root.columnconfigure(col, weight=1)
            self.root.rowconfigure(row, weight=1)
            cell.grid(row=row, column=col, sticky='nsew')

    def resize(self, rect: Rect):
        geometry = f'{rect.width}x{rect.height}+{rect.left}+{rect.top}'
        print(f'geometry: {geometry}')
        self.root.geometry(geometry)
        self.root.minsize(rect.width, rect.height)
        self.root.maxsize(rect.width, rect.height)
        self.update()

    def update(self):
        self.root.update_idletasks()
        self.root.update()

    def close(self):
        self.root.destroy()
        self.root.mainloop()
        import time
        time.sleep(0.1)

    def __enter__(self):
        self.resize(screen_rect())
        return self

    def __exit__(self, _exception_type, _exception_value, _exception_traceback):
        self.close()


def on_press(key):
    global current_rect

    if key == Key.space:
        current_rect = screen_rect()
        return

    if current_rect is None:
        return

    if key in (Key.left, KeyCode.from_char('a'), KeyCode.from_char('h')):
        current_rect = current_rect.left_half
    elif key in (Key.right, KeyCode.from_char('d'), KeyCode.from_char('l')):
        current_rect = current_rect.right_half
    elif key in (Key.up, KeyCode.from_char('w'), KeyCode.from_char('k')):
        current_rect = current_rect.top_half
    elif key in (Key.down, KeyCode.from_char('s'), KeyCode.from_char('j')):
        current_rect = current_rect.bottom_half
    elif key == Key.enter:
        pos = current_rect.center
        click.set()
        running.clear()
        raise pynput.keyboard.Listener.StopException
    elif key == Key.esc:
        click.clear()
        running.clear()
        raise pynput.keyboard.Listener.StopException

    mouse.position = current_rect.center


listener = pynput.keyboard.Listener(on_press=on_press)
listener.start()

try:
    with Overlay() as overlay:
        window_rect = None
        while running.is_set():
            if window_rect is None or window_rect != current_rect:
                window_rect = current_rect
                overlay.resize(window_rect)
        overlay.update()
except Exception as e:
    print(e)
finally:
    listener.stop()

if click.is_set():
    print('click')
    mouse.click(pynput.mouse.Button.left)
