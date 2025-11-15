import serial.tools.list_ports
import serial
from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import *
from tkinter import ttk
from threading import Thread
import os
import signal

ENCODING = 'UTF-8'


class Board(Thread):
    def __init__(self, port, speed, parent, callback):
        super().__init__()
        self.callback = callback

        self.running = False
        if port:
            self.s = serial.Serial(port, speed)
            self.running = True

        self.port = port
        self.speed = speed
        self.name = str(self.port) + ' - ' + str(speed)
        self.n_bin = 0

        self.frame = ttk.Frame(parent)
        self.frame.columnconfigure(3, weight = 1)
        self.frame.rowconfigure(1, weight = 1)
        self.frame.rowconfigure(3, weight = 1)

        lmsg = Label(self.frame, text = "Message")
        lmsg.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = 'e')

        ldts = Label(self.frame, text = "Données")
        ldts.grid(row = 2, column = 0, padx = 5, pady = 5, sticky = 'e')

        self.msg = ttk.Entry(self.frame)
        self.msg.grid(row = 0, column = 1, padx = 5, pady = 5, sticky = 'nswe')
        self.msg.bind('<Return>', self.rtn_msg)
        self.msg.focus()
        self.dts = ttk.Entry(self.frame)
        self.dts.grid(row = 2, column = 1, padx = 5, pady = 5, sticky = 'nswe')
        self.dts.bind('<Return>', self.rtn_dts)

        Nsent = 4 * 6 - 1
        self.sent_bin = Text(self.frame, width = Nsent, height = 4)
        self.sent_bin.grid(row = 3, column = 0, padx = 5, pady = 5, sticky = 'nswe', columnspan = 2)
        self.sent_bin.config(stat = 'disabled')
        self.sent_bin.bind('<Button-3>', self.clkright_sent)
        self.sent_bin.bind('<Double-Button-1>', self.send_data)

        self.sent_str = Text(self.frame, width = Nsent, height = 4)
        self.sent_str.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = 'nswe', columnspan = 2)
        self.sent_str.config(stat = 'disabled')
        self.sent_str.bind('<Button-3>', self.clkright_sent)
        self.sent_str.bind('<Double-Button-1>', self.send_data)

        self.code = Text(self.frame, width = 80, font = ('Consolas', 8), wrap = 'none')
        self.code.grid(row = 0, column = 3, padx = 5, pady = 5, sticky = 'nswe', rowspan = 5)
        self.code.config(stat = 'disabled')
        self.code.bind('<Double-Button-1>', self.open_code)

        Nrecv = 3 * 16 - 1
        self.outstr = Text(self.frame, height = 10, width = Nrecv)
        self.outstr.grid(row = 0, column = 2, padx = 5, pady = 5, sticky = 'nswe', rowspan = 2)
        self.outstr.config(stat = 'disabled')
        self.outstr.bind('<Button-3>', self.clkright_out)

        self.outbin = Text(self.frame, height = 10, width = Nrecv)
        self.outbin.grid(row = 2, column = 2, padx = 5, pady = 5, sticky = 'nswe', rowspan = 2)
        self.outbin.config(stat = 'disabled')
        self.outbin.bind('<Button-3>', self.clkright_out)

        close = ttk.Button(self.frame, text = 'Fermer', command = self.close)
        close.grid(row = 4, column = 0, columnspan = 3, padx = 5, pady = 5, sticky = 'nswe')

        self.start()

    def clkright_out(self, evt):
        popup = Menu(evt.widget, tearoff = 0)
        popup.add_command(label = 'Exporter', command = self._save_data)
        popup.add_command(label = 'Exporter et effacer', command = self.save_data_clear)
        popup.tk_popup(evt.x_root, evt.y_root)

    def clkright_sent(self, evt):
        popup = Menu(evt.widget, tearoff = 0)
        popup.add_command(label = 'Importer', command = self.send_data)
        popup.tk_popup(evt.x_root, evt.y_root)

    def _save_data(self, evt = None):
        path = asksaveasfilename(title = 'Enregistrer les données', filetypes = [('Fichiers données', '*.bin')])
        if not path:
            return True

        data = self.outstr.get('0.0', 'end')
        data = data.rstrip('\n')
        f = open(path, 'w', encoding = ENCODING)
        f.write(data)
        f.close()

    save_data_nocleaer = _save_data

    def save_data_clear(self, evt = None):
        if self._save_data():
            return

        self.outbin.config(stat = 'normal')
        self.outstr.config(stat = 'normal')
        self.outbin.delete('0.0', 'end')
        self.outstr.delete('0.0', 'end')
        self.outbin.config(stat = 'disabled')
        self.outstr.config(stat = 'disabled')

    def send_data(self, evt = None):
        path = askopenfilename(title = 'Ouvrir et envoyer un fichier', filetypes = [('Fichiers données', '*.bin')])
        if not path:
            return

        f = open(path, 'rb')
        r = f.read()
        f.close()
        self.write(r)

    def open_code(self, evt = None):
        path = askopenfilename(title = "Ouvrir un code assicoé", filetypes = [('Fichiers Arduino', '*.ino *.h'), ('Tous les fichiers', '*.*')])
        if path:
            f = open(path, 'r', encoding = ENCODING)
            r = f.read()
            f.close()
            self.code.config(stat = 'normal')
            self.code.delete('0.0', 'end')
            self.code.insert('end', r)
            self.code.config(stat = 'disabled')

    def close(self):
        self.running = False
        try:
            self.s.close()
        except:
            pass

        self.outbin.config(stat = 'normal')
        self.outstr.config(stat = 'normal')
        self.outbin.delete('0.0', 'end')
        self.outstr.delete('0.0', 'end')
        self.outbin.config(fg = 'red')
        self.outstr.config(fg = 'red')
        self.outbin.insert('end', 'Fermeture du port COM...')
        self.outstr.insert('end', 'Fermeture du port COM...')
        self.join()
        self.frame.destroy()
        self.callback()

    def rtn_dts(self, evt = None):
        data = self.dts.get()
        self.dts.delete('0', 'end')
        data = data.split(' ')
        data = list(map(lambda v: int(v), data))
        self.write(bytes(data))
        self.sent_bin.config(stat = 'normal')
        self.sent_str.config(stat = 'normal')
        for c in data:
            self.n_bin += 1
            self.sent_bin.insert('end', self.format_name(c, hx = False, leng = 3))
            self.sent_str.insert('end', chr(c))
            if self.n_bin % 6 == 0:
                self.sent_bin.insert('end', '\n')
            else:
                self.sent_bin.insert('end', ' ')
        
        self.sent_bin.config(stat = 'disabled')
        self.sent_str.config(stat = 'disabled')

    def rtn_msg(self, evt = None):
        data = self.msg.get()
        self.msg.delete('0', 'end')
        self.write(data.encode(ENCODING))
        self.sent_bin.config(stat = 'normal')
        self.sent_str.config(stat = 'normal')
        self.sent_str.insert('end', data + '\n')
        for c in data:
            self.n_bin += 1
            self.sent_bin.insert('end', self.format_name(ord(c), hx = False, leng = 3))
            if self.n_bin % 6 == 0:
                self.sent_bin.insert('end', '\n')
            else:
                self.sent_bin.insert('end', ' ')

        self.sent_str.config(stat = 'disabled')
        self.sent_bin.config(stat = 'disabled')

    def write(self, content):
        try:
            self.s.write(content)
        except:
            pass

    def format_name(self, data, hx = True, leng = 2):
        if hx:
            data = hex(data)

        data = str(data).replace('0x', '')
        while len(data) != leng:
            data = '0' + data

        return data.upper()

    def run(self):
        n = 0
        while self.running:
            if self.s.in_waiting:
                n += 1
                data = self.s.read()
                self.outstr.config(stat = 'normal')
                self.outbin.config(stat = 'normal')
                try:
                    self.outstr.insert('end', data.decode(ENCODING))
                except:
                    self.outstr.insert('end', '?')

                self.outbin.insert('end', self.format_name(data[0]))
                if n % 16 == 0:
                    self.outbin.insert('end', '\n')
                else:
                    self.outbin.insert('end', ' ')

                self.outstr.config(stat = 'disabled')
                self.outbin.config(stat = 'disabled')


class AskNewPort:
    def __init__(self, parent, frames, callback):
        self.callback = callback
        self.frames = frames
        self._port = None
        self._speed = None

        self.tk = Toplevel(parent)
        self.tk.transient(parent)
        self.tk.title("Ouverture d'un port")
        self.tk.columnconfigure(1, weight = 1)
        self.tk.focus()

        lbp = Label(self.tk, text = 'Port')
        lbp.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = 'e')

        lbs = Label(self.tk, text = 'Vitesse')
        lbs.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = 'e')

        self.port = ttk.Combobox(self.tk)
        self.port.grid(row = 0, column = 1, padx = 5, pady = 5, sticky = 'nswe')

        self.speed = ttk.Combobox(self.tk, values = [4800, 9600, 31150, 115200])
        self.speed.grid(row = 1, column = 1, padx = 5, pady = 5, sticky = 'nswe')
        self.speed.current(1)

        btn = ttk.Button(self.tk, text = "Ouvrir", command = self.valider)
        btn.grid(row = 2, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = 'nswe')
        btn.focus()

        self.update_port()

    def valider(self):
        self._port = self.port.get()
        self._speed = self.speed.get()
        self.tk.destroy()

    def update_port(self):
        boards = list(map(lambda l: l[0], serial.tools.list_ports.comports()))
        self.port.config(values = boards)
        if len(boards) != 0:
            self.port.current(0)

    def show(self):
        self.tk.wait_window()
        self.board = Board(self._port, self._speed, self.frames, self.callback)

class Application:
    def __init__(self):
        self.master = Tk()
        self.master.title("COM port opener")
        self.master.protocol('WM_DELETE_WINDOW', self.Quitter)
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.master.minsize(300, 200)

        self.frames = ttk.Notebook(self.master)
        self.frames.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = 'nswe')
        self.number = 0

        self.open_port()

    def close_callback(self):
        self.number -= 1
        if self.number == 0:
            self.Quitter()

    def open_port(self):
        gui = AskNewPort(self.master, self.frames, self.close_callback)
        gui.show()
        board = gui.board
        self.frames.add(text = board.name, child = board.frame)
        self.number += 1
        self.master.deiconify()

    def Generate(self):
        self.master.mainloop()

    def Quitter(self):
        self.master.destroy()
        os.kill(os.getpid(), signal.SIGTERM)

if __name__ == '__main__':
    app = Application()
    app.Generate()
