# Visualize sonar data

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
from sonarcom import ComPortData
from serial_list import serial_ports

import tkinter as tk
from tkinter import ttk

LARGE_FONT = ("Verdana", 12)
AXIS_LENGTH = 100
MINIMUM_DEPTH = 9500
style.use("ggplot")

#Create matplotlib graph
f = Figure(figsize=(5,4), dpi=100)
a = f.add_subplot(111)

class DataBuffer:
    def __init__(self, length):
        self._data_buffer = [MINIMUM_DEPTH for i in range(length)]

    def get(self):
        return self._data_buffer

    def add(self, item):
        self._data_buffer.append(item)
        del(self._data_buffer[0])

def changeUpperLimits(value):
    SonarEchoSounder.upper_limit = value


# Main container for program
class SonarEchoSounder(tk.Tk):

    com_settings = [None, 57600, 10, 'SDDBT']
    available_ports = serial_ports()

    upper_limit = 0
    lower_limit = 50
    is_running = False
    com_port_valid = False

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        #Add icon and program name
        tk.Tk.iconbitmap(self, default='icon.ico')
        tk.Tk.wm_title(self, 'Sonar Echo Sounder')

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Initialize all pages
        self.frames = {}

        #List of all pages
        for F in [StartPage]:
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')
        self.show_frame(StartPage)

    #Go to specific page
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

# Main
class StartPage(tk.Frame):

    def run(self):
        if not SonarEchoSounder.is_running:
            SonarEchoSounder.com_settings[0] = self.choose_box_com.get()
            global com_data
            try:
                com_data = ComPortData(*SonarEchoSounder.com_settings)
                SonarEchoSounder.is_running = True
                self.start_button['text'] = 'Stop'
            except ValueError:
                pass
        else:
            SonarEchoSounder.is_running = False
            com_data.closePort()
            self.start_button['text'] = 'Start'

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        # Main window title
        #label = ttk.Label(self, text='Echogram', font=LARGE_FONT)
        #label.pack(pady=10, padx=10)

        echogram_frame = tk.Frame(self)
        echogram_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        settings_frame = tk.Frame(self)
        settings_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=20, padx=20)

        # Echogram window
        canvas = FigureCanvasTkAgg(f, echogram_frame)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Settings window
        label_head = ttk.Label(settings_frame, text='Settings\n', font = LARGE_FONT)
        label_head.grid(row=0, sticky='W')

        label_com = ttk.Label(settings_frame, text='Sonar port  ')
        label_com.grid(row=1, column=0)

        label_gps = ttk.Label(settings_frame, text='GPS port    ')
        label_gps.grid(row=2, column=0)

        # Choice of COM port
        var1 = tk.StringVar(self)
        var2 = tk.StringVar(self)
        try:
            var1.set(SonarEchoSounder.available_ports[0])
            var2.set(SonarEchoSounder.available_ports[0])
        except IndexError:
            var1.set('No ports available')
            var2.set('No ports available')
        self.choose_box_com = ttk.Combobox(settings_frame, textvariable=var1, values=SonarEchoSounder.available_ports)
        self.choose_box_com.grid(row=1, column=1)

        self.choose_box_gps = ttk.Combobox(settings_frame, textvariable=var2, values=SonarEchoSounder.available_ports)
        self.choose_box_gps.grid(row=2, column=1)

        label_upper =  ttk.Label(settings_frame, text='Upper limit  ')
        label_upper.grid(row=3, column=0)

        label_lower = ttk.Label(settings_frame, text='Lower limit  ')
        label_lower.grid(row=4, column=0)

        var = tk.StringVar(self)
        var.set(str(SonarEchoSounder.upper_limit))
        self.upper_limit = tk.Spinbox(settings_frame, from_=0, to=9000, textvariable=var)
        self.upper_limit.grid(row=3, column=1)

        var = tk.StringVar(self)
        var.set(str(SonarEchoSounder.lower_limit))
        self.lower_limit = tk.Spinbox(settings_frame, from_=0, to=9000,  textvariable=var)
        self.lower_limit.grid(row=4, column=1)

        self.start_button = tk.Button(settings_frame, text='Start', command=self.run)
        self.start_button.grid(row=5, sticky='W')


#Initiate data buffer process
data_buffer = DataBuffer(AXIS_LENGTH)
x_list = [i for i in range(AXIS_LENGTH)]

def animate(interval):
    a.clear()
    if SonarEchoSounder.is_running:
        try:
            cur_value = com_data.getOutputData()[1]
            if cur_value: data_buffer.add(float(cur_value))
            y_list = data_buffer.get()
            a.fill_between(x_list, SonarEchoSounder.lower_limit, y_list, color='#31AFD7')
            # SonarEchoSounder.upper_limit = StartPage.label_upper.get()
            # SonarEchoSounder.lower_limit = StartPage.label_lower.get()
            a.set_xlim([0,AXIS_LENGTH])
            a.set_ylim([SonarEchoSounder.lower_limit, SonarEchoSounder.upper_limit])
        except:
            pass

    a.plot(0,0)


# Start the application

app = SonarEchoSounder()
ani = animation.FuncAnimation(f,animate, interval=500)
app.mainloop()

