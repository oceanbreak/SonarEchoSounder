# Visualize sonar data

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
from sonarcom import ComPortData
from serial_list import serial_ports
import time
from sonardatabuffer import GenerateBuffer

import tkinter as tk
from tkinter import ttk

LARGE_FONT = ("Verdana", 12)
AXIS_LENGTH = 100
MINIMUM_DEPTH = 9500
style.use("ggplot")

#Create matplotlib graph
f = Figure(figsize=(5,4), dpi=100)
a = f.add_subplot(111)

# Helper functions
def generateFileName(prefix = 'log'):
    cur_time = time.gmtime()
    date_str = '{:0>2}'.format(cur_time.tm_mday) +  '{:0>2}'.format(cur_time.tm_mon)  + '{:0>2}'.format(cur_time.tm_year)[-2:]
    time_str = '{:0>2}'.format(cur_time.tm_hour) + '{:0>2}'.format(cur_time.tm_min)  + '{:0>2}'.format(cur_time.tm_sec)
    return prefix + '_' + date_str + '_' + time_str


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
    gps_settings = [None, 4800, 10, 'GPGGA']
    available_ports = serial_ports()
    sonar_keywords = ['SDDBT']
    gps_keywords = ['GPGGA', 'GPGGL', 'GPRMC']

    is_running = False
    com_port_valid = False

    gps_data = None
    depth_data = None

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
            SonarEchoSounder.gps_settings[0] = self.choose_box_gps.get()
            global com_data
            global gps_data
            try:
                com_data = ComPortData(*SonarEchoSounder.com_settings)
                gps_data = GenerateBuffer(*SonarEchoSounder.gps_settings)
                gps_data.repeat_writing_buffer()
                SonarEchoSounder.is_running = True
                self.start_button['text'] = 'Stop'
            except ValueError:
                pass
        else:
            SonarEchoSounder.is_running = False
            com_data.closePort()
            gps_data.stop_writing_buffer()
            self.start_button['text'] = 'Start'

    def updateDataText(self):
        degree_sign = u'\N{DEGREE SIGN}'
        depth = SonarEchoSounder.depth_data
        latdeg = SonarEchoSounder.gps_data[1]
        latmin = SonarEchoSounder.gps_data[2]
        lat = SonarEchoSounder.gps_data[3]
        londeg = SonarEchoSounder.gps_data[4]
        lonmin = SonarEchoSounder.gps_data[5]
        lon = SonarEchoSounder.gps_data[6]

        new_text = 'Depth: %f m\n' \
                   'GPS:\n'\
                   '%f %f %s\n' \
                   '%f %f %s' % (depth, latdeg, latmin, lat, londeg, lonmin, lon)

        self.data_label['text'] = new_text
        print(new_text)

    def __init__(self, parent, controller):

        # Custom settings
        labelfont = ('arial', 12)
        label_bg = 'white'
        label_fg = 'black'
        padding_y = 5

        tk.Frame.__init__(self, parent)

        echogram_frame = tk.Frame(self)
        echogram_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        settings_frame = tk.Frame(self)
        settings_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=20, padx=20)

        # Echogram window
        canvas = FigureCanvasTkAgg(f, echogram_frame)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Settings window
        label_head = ttk.Label(settings_frame, text='Settings\n', font = LARGE_FONT)
        label_head.grid(row=0, sticky='W', pady=padding_y)

        label_com = ttk.Label(settings_frame, text='Sonar port  ')
        label_com.grid(row=1, column=0, pady=padding_y)

        label_gps = ttk.Label(settings_frame, text='GPS port    ')
        label_gps.grid(row=2, column=0, pady=padding_y)

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
        self.choose_box_com.grid(row=1, column=1, pady=padding_y)

        self.choose_box_gps = ttk.Combobox(settings_frame, textvariable=var2, values=SonarEchoSounder.available_ports)
        self.choose_box_gps.grid(row=2, column=1, pady=padding_y)

        self.start_button = tk.Button(settings_frame, text='Start', command=self.run)
        self.start_button.grid(row=3, sticky='W', pady=padding_y)

        self.data_label = tk.Label(settings_frame)
        self.data_label["text"] = 'Text'
        self.data_label.config(font=labelfont, bg=label_bg, fg=label_fg)
        self.data_label.grid(row=4, pady=padding_y, sticky='W')


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

            # Calculate limits
            y_sum_list = [y for y in y_list if y != MINIMUM_DEPTH]
            average_value = sum(y_sum_list) / len(y_sum_list)
            upper_limit = min(y_sum_list) - average_value/4
            lower_limit = max(y_sum_list) + average_value/4

            # Draw plot
            a.fill_between(x_list, lower_limit, y_list, color='#31AFD7')
            a.set_xlim([0,AXIS_LENGTH])
            a.set_ylim([lower_limit, upper_limit])
            cur_gps = gps_data.getData()

            SonarEchoSounder.gps_data = cur_gps
            SonarEchoSounder.depth_data = cur_value
            StartPage.data_label['text'] = 'Fuck you'

        except:
            pass
    a.plot(0,0)


# Start the application

app = SonarEchoSounder()
ani = animation.FuncAnimation(f,animate, interval=500)
app.mainloop()

