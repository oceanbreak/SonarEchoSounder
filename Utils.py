import sys, glob, serial, sonarcom, threading, time

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def generateFileName(prefix = 'log'):
    cur_time = time.gmtime()
    date_str = '{:0>2}'.format(cur_time.tm_mday) +  '{:0>2}'.format(cur_time.tm_mon)  + '{:0>2}'.format(cur_time.tm_year)[-2:]
    time_str = '{:0>2}'.format(cur_time.tm_hour) + '{:0>2}'.format(cur_time.tm_min)  + '{:0>2}'.format(cur_time.tm_sec)
    return prefix + '_' + date_str + '_' + time_str

class SonarThread(threading.Thread):
    """
    The class takes user defined function as an argument and creates thread that executes it repeatedly after .start()
    while stop() method is not applied.
    """
    def __init__(self, custom_func):
        super(SonarThread, self).__init__()
        self._stop = threading.Event()
        self.customFunc = custom_func

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        while not self.stopped():
            self.customFunc()

class GenerateBuffer:
    def __init__(self, com_port, rate, timeout, message):
        self._com_port = com_port
        self._rate = rate
        self._message = message
        self._cur_data = None
        try:
            self._data_line = sonarcom.ComPortData(com_port, rate, timeout, message) #CHANGE
        except:
            print("ERROR Sonardatabufer: Cannot generate buffer with %s message" % message)

    def write_buffer_entry(self):
        try:
           cur_string = self._data_line.getOutputData()
        except AttributeError:
            cur_string = False
        if cur_string:
            print(time.asctime() + ':\t' + str(cur_string))
            self._cur_data = cur_string

    def repeat_writing_buffer(self):
        self.proc_buffer = SonarThread(self.write_buffer_entry)
        self.proc_buffer.start()

    def stop_writing_buffer(self):
        self.proc_buffer.stop()

    def getData(self):
        return self._cur_data




if __name__ == '__main__':
    print(serial_ports())
    data = {'Depth' : None, 'Coord' : None}
    coord_data = GenerateBuffer('COM6', 4800, 10, 'GPGGA')
    depth_data = GenerateBuffer('COM3', 57600, 10, 'SDDBT')
    coord_data.repeat_writing_buffer()
    depth_data.repeat_writing_buffer()
    for i in range(20):
        data['Coord'] = coord_data.getData()
        data['Depth'] = depth_data.getData()
        if data['Depth'] and data['Coord']:
            # print(';'.join(data['Depth']) + ';' + ';'.join(data['Coord']))
            line = ';'.join(data['Depth']) + ';' + ';'.join(data['Coord'])

        time.sleep(1)

    coord_data.stop_writing_buffer()
    depth_data.stop_writing_buffer()
