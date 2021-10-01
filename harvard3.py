import serial
total_pumps = 5

#
# %.2d forces two integers as needed for daisy chained pumps
# \x0D

serial_port = 'COM4'
baud_rate   = '9600'

def find_pumps(tot_range=total_pumps):
    pumps = []
    ser = open_serial() #diff
    ser.flushInput()
    for i in range(total_pumps):
        cmd = '%.2dSTP\x0D'%i
        ser.write(str.encode(cmd))
        read1=ser.read(10)
        if any(str(c).isdigit() for c in read1):
            #print read1
            pumps.append(i)
        ser.flushInput()          
        print(pumps)
    return pumps

   
def run_all(rates):
    ser = open_serial()
    for pump in rates.keys():
        #print '-------- run pump %i -----------' %pump
        rate = int(rates[pump])
        if rate ==0:
            #print 'stop'
            cmd = '%.2dSTP\x0D' %(pump)
        elif rate >0:
            #print 'run +'
            cmd = '%.2dRUN\x0D' %(pump)
        elif rate <0:
            #print 'run -'
            cmd = '%.2dRUNW\x0D' %(pump)
        ser.write(str.encode(cmd))
        msg, status = read_serial(ser)
        #print msg, status
    ser.close()


def set_diameter(pump,dia):
    ser = open_serial()
    #print '-------- setting diameter %i as %s -----------' %(pump,dia)
    cmd = '%.2dMMD %s\x0D'%(pump,dia) # harvard
    ser.write(str.encode(cmd))
    msg, status = read_serial(ser)
    #print msg, status
    ser.close()
    
def get_diameter(pump):
    ser = open_serial()
    #print '-------- getting diameter %i -----------' %pump
    cmd = '%.2dDIA\x0D'%(pump) # harvard
    ser.write(str.encode(cmd))
    msg, status = read_serial(ser)
    #print msg, status
    # dia = msg.split('\r')[0].strip()
    dia = msg.split('\r')[0].strip()
    ser.close()
    #print dia
    return(dia)
    
def read_serial(ser):
    #print 'reading serial'
    special = {b'<':'back',b'>':'fwd',b':':'stopped',b'*':'stalled'}
    
    ser.readline()
    # print(ser.readline())
    line = ser.read()
    # print(line)
    if line==b'?' or line==b'O' or line==b'E':
        print(ser.readline().strip())
        
    msg=b''
    # while(1):
    #     print(ser.read())
        
    while(1):
        output = ser.read()
        for c in output:
            c = c.to_bytes(1, 'little')
            # print(c)
            line+=c
            # print(line)
            # line+=str.encode(c,encoding='ASCII') #KJ
            if c==b'\n':
                #print(line)
                msg = line
                # line = ''
                line = b' '
                break    
            if c in special.keys():
                #print(msg,line)
                return msg.decode('utf-8'), line.decode('utf-8')
#
def open_serial():
    ser = serial.Serial(serial_port,
                        baud_rate,
                        stopbits=serial.STOPBITS_TWO,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        timeout=1)
    #print ser.is_open
    ser.flushInput()
    ser.flushOutput()
    return ser

def get_rates(rates):
    rates = dict((p,get_rate(p,rates).split('.')[0]) for p,r in iter(rates.items()))
    return(rates)

def get_rate(pump, old_rates):
    ser = open_serial()
    #print '-------- get pump %i rate -----------' %pump
    rate = int(old_rates[pump])
    if rate >0:
        #print 'get +'
        cmd = '%.2dRAT\x0D'%(pump)
        #print cmd
        ser.write(str.encode(cmd))
        output, status = read_serial(ser)
        #print status
    elif rate <0:
        #print 'get -'
        cmd = '%.2dRATW\x0D'%(pump)
        #print cmd
        ser.write(str.encode(cmd))
        output, status = read_serial(ser)
        #print status
    else:
        #print 'pump stopped'
        ser.close()
        return '0'
    
    units = output[-6:-2]
    #print(units)
    
    if units ==' ul/h':
        rate = float(output[:-7].strip())
    if units==' ml/h':
        rate = float(output[:-7].strip()) * 1000 # convert to ul/h
    ser.close()     
    #print("output: is " + str(rate) + units)
    return(str(rate))

#Added logic for flow rates above 10k
def set_rates(rates):
    ser = open_serial()
    for pump in rates.keys():
        #print '-------- set pump %i -----------' %pump
        rate = int(rates[pump])
        #print(rate)
        if rate < 0:
            #print("set - flow")
            if rate < -9999:
                rate = rate/1000
                cmd = '%.2dMLHW %i\x0D' %(pump, abs(rate)) # Reverse, above 10k                
            else:
                cmd = '%.2dULHW %i\x0D' %(pump, abs(rate)) # Reverse
            ser.write(str.encode(cmd))
        elif rate > 0:
            #print("set + flow")
            if rate > 9999:
                rate = rate/1000
                cmd = '%.2dMLH %i\x0D' %(pump, abs(rate)) #above 10k                
            else:
                cmd = '%.2dULH %i\x0D' %(pump, rate) # Forward 
            ser.write(str.encode(cmd))
        elif rate ==0:
            #print("set stop condition")
            cmd = '%.2dSTP\x0D' %(pump)
            ser.write(str.encode(cmd))
        #print cmd
        msg, status = read_serial(ser)
        #print msg, status
    ser.close()

def stop_pump(pump):
    ser = open_serial()
    #print("stopping pump %i" %pump)
    cmd = '%.2dSTP\x0D' %(pump)
    ser.write(str.encode(cmd))
    msg, status = read_serial(ser)
    #print msg, status
    ser.close()

def prime(pump):
    ser = open_serial()
    # set rate
    #cmd = '%.2dMLH 10\x0D' %(pump)  # 10ml/hr?
    cmd = '%.2dULH %i\x0D' %(pump, 5000) # Forward
    ser.write(str.encode(cmd))
    msg, status = read_serial(ser)
    #print msg, status

    # run
    cmd = '%.2dRUN\x0D'%(pump)
    ser.write(str.encode(cmd))
    msg, status = read_serial(ser)
    #print msg, status
    ser.close()
    





#ser = serial.Serial('COM3',19200)
#print ser.name       # check which port was really used
#print ser.isOpen()
#ser.close()
#pumps = find_pumps(ser)
#rates = get_rates(ser,pumps)
