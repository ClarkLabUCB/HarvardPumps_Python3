###########
# Written by Phil Romero for use with New Era pumps
# 20141018 adjusted by Laurens Kraal for use with Harvard Apparatus pumps
# Also added 'Burst' funtionality
#removed burst
###########

import sys
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QShortcut,QLineEdit,QApplication, QWidget, QGridLayout, QPushButton, QLabel, QComboBox
import serial
import harvard3 as harvard
import time


serial_port = 'COM4'
baud_rate   = '9600'

"""
#Diameters from manual
syringes = {'1 ml BD':'4.78',
            '3 ml BD':'8.66',
            '5 ml BD': '12.06',
            '10 ml BD':'14.50',
            '30 ml BD':'21.70'}

#original diameters
"""
syringes = {'1 ml BD':'4.699',
            '3 ml BD':'8.585',
            '5 ml BD': '12.46',
            '10 ml BD':'14.60',
            '20 ml BD': '19.13',
            '30 ml BD':'21.59'}


class PumpControl(QWidget):

    def __init__(self):
        super(PumpControl, self).__init__()
        self.initUI()

    def initUI(self):
        
        # set grid layout
        grid = QGridLayout()
        grid.setSpacing(5)

        # setup two buttons along top
        self.runbtn = QPushButton('Run/Update',self)
        grid.addWidget(self.runbtn,1,2)
        self.runbtn.setCheckable(True)
        self.runbtn.clicked.connect(self.run_update)

        self.stopbtn = QPushButton('Stop',self)
        grid.addWidget(self.stopbtn,1,3)
        self.stopbtn.setCheckable(True)
        self.stopbtn.clicked.connect(self.stop_all)

        # optional column labels
        grid.addWidget(QLabel('Pump number'),2,0)
        grid.addWidget(QLabel('Syringe'),2,1)
        grid.addWidget(QLabel('Contents'),2,2)
        grid.addWidget(QLabel('Flow rate'),2,3)
        grid.addWidget(QLabel('Current flow rate'),2,4)

        # find pumps
        pumps = harvard.find_pumps()
        

        # interate over pumps, adding a row for each
        self.mapper = QtCore.QSignalMapper(self)
        self.primemapper = QtCore.QSignalMapper(self)
        self.currflow = dict()
        self.rates = dict()
        self.contents = dict()
        self.prime_btns = dict()
        for i,pump in enumerate(pumps):
            row = 3+i

            # add pump number
            pumplab = QLabel('Pump %i'%pump)
            pumplab.setAlignment(QtCore.Qt.AlignHCenter)
            grid.addWidget(pumplab,row,0)

            # add syringe pulldown
            combo = QComboBox(self)
            [combo.addItem(s) for s in sorted(syringes.keys(), key = lambda y: (float(syringes[y])))]
            self.mapper.setMapping(combo,pump)
            combo.activated.connect(self.mapper.map)
            grid.addWidget(combo,row,1)

            # add textbox to put syring contents
            self.contents[pump] = QLineEdit(self)
            grid.addWidget(self.contents[pump],row,2)

            # add textbox to enter flow rates
            self.rates[pump] = QLineEdit(self)
            grid.addWidget(self.rates[pump],row,3)

            # add label to show current flow rates
            self.currflow[pump] = QLabel(self)
            self.currflow[pump].setAlignment(QtCore.Qt.AlignHCenter)
            grid.addWidget(self.currflow[pump],row,4)

            # add prime button
            btn = QPushButton('Prime',self)
            btn.setCheckable(True)# makes the button toggleable
            self.primemapper.setMapping(btn,pump)
            btn.clicked.connect(self.primemapper.map)
            grid.addWidget(btn,row,5)
            self.prime_btns[pump] = btn

        # mapper thing
        self.mapper.mapped.connect(self.update_syringe)
        self.primemapper.mapped.connect(self.prime_pumps)

        # set up the status bar
        self.curr_state = 'Running'
        self.statusbar = QLabel(self)
        grid.addWidget(self.statusbar,1,4)
        self.statusbar.setText('Status: '+self.curr_state)

        # set up the last command bar
        self.commandbar = QLabel(self)
        grid.addWidget(self.commandbar,row+1,0,1,4)

        # make the prime state: a set containing the priming pumps
        self.prime_state = set()

        print("stopping all")
        self.stop_all()

        # keyboard shortcuts
        QShortcut(QtGui.QKeySequence('Space'),self,self.stop_all)

        
        # format the page
        self.setLayout(grid)
        self.setWindowTitle('Pump control')
        #self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint) # always on top

        self.starting_conditions()
        self.show()

    def stop_pumps(self):
        for pump in self.rates:
            harvard.stop_pump(pump)
        
    def stop_all(self):
        self.runbtn.setChecked(0)
        self.stopbtn.setChecked(1)
        self.stop_pumps()
        self.curr_state = 'Stopped'
        self.statusbar.setText('Status: '+self.curr_state)
        self.commandbar.setText('Last command: stop all pumps')
        [self.currflow[pump].setText('0 ul/hr') for pump in self.rates]
        self.prime_state = set()
        [self.prime_btns[p].setChecked(0) for p in self.rates]

    def run_update(self):
        #check if the flow rates are legit numbers, if not set to zero
        self.runbtn.setChecked(1)
        self.stopbtn.setChecked(0)
        rates = self.getRates()
        #print('rates:')
        #print(rates)
        if self.curr_state=='Running':
            #print("setting new rates")
            harvard.set_rates(rates) # pump : rate
            #print("running all")
            harvard.run_all(rates)
            #print("get rates")
            actual_rates = harvard.get_rates(rates) # get the rates of the pumps
            print("actual rates:")
            print(actual_rates)
            self.commandbar.setText('Last command: update '+', '.join(['p%i=%s'%(p,actual_rates[p]) for p in actual_rates]))
            [self.currflow[pump].setText(actual_rates[pump]+' ul/hr') for pump in actual_rates]

        if self.curr_state=='Stopped':
            #print("setting new rates")
            harvard.set_rates(rates)
            #print("running all")
            harvard.run_all(rates)
            self.curr_state = 'Running'
            self.statusbar.setText('Status: '+self.curr_state)
            #print("get rates")
            actual_rates = harvard.get_rates(rates)
            print("actual rates:")
            print(actual_rates)
            self.commandbar.setText('Last command: run '+', '.join(['p%i=%s'%(p,actual_rates[p]) for p in actual_rates]))
            [self.currflow[pump].setText(actual_rates[pump]+' ul/hr') for pump in actual_rates]

    def update_syringe(self,pump):
        if self.curr_state == 'Stopped':
            dia = syringes[str(self.mapper.mapping(pump).currentText())]
            #print("set dia: %s" %dia)
            harvard.set_diameter(pump,dia)
            dia = harvard.get_diameter(pump)
            print("actual dia: %s" %dia)
            self.commandbar.setText('Last command: pump %i set to %s (%s mm)'%(pump,self.mapper.mapping(pump).currentText(),dia))
        else:
            self.commandbar.setText("Can't change syringe while running")
      

    def starting_conditions(self):
        print("updating syringes")
        dias = {0:'3 ml BD',1:'20 ml BD',2:'10 ml BD',3:'3 ml BD',4:'20 ml BD'}
        text = {0:'DROPS',1:'BIAS',2: '',3:'SPACER', 4:'EXTRA'}

        for pump in self.rates:
            d = dias[pump]
            
            index = self.mapper.mapping(pump).findText(d, QtCore.Qt.MatchFixedString)
            self.mapper.mapping(pump).setCurrentIndex(index) 
            self.commandbar.setText('Last command: pump %i set to %s (%s mm)'%(pump,self.mapper.mapping(pump).currentText(),dias[pump]))

            # change diameter
            self.update_syringe(pump)
            
            # set starting contents
            self.contents[pump].setText(text[pump])



    def prime_pumps(self,pump):
        if self.curr_state == 'Stopped':
            if pump not in self.prime_state: # currently not priming
                harvard.prime(pump)
                self.commandbar.setText('Last command: priming pump %i'%pump)
                self.statusbar.setText('Status: Priming')
                self.prime_state.add(pump)# add to prime state
            else: # currently priming
                harvard.stop_pump(pump)
                self.commandbar.setText('Last command: stopped pump %i'%pump)
                self.prime_state.remove(pump)# remove prime state
                if len(self.prime_state)==0: self.statusbar.setText('Status: Stopped')# if this is the last one, show status=Stopped
            #print("Getting actual rates in prime")
            #time.sleep(1)
            
            not_primestate= {0,1,2,3} - self.prime_state
            dict_samp={i:10000 for i in self.prime_state}
            dict_b={j:0 for j in not_primestate}
            dict_samp.update(dict_b)
            #print dict_samp
            actual_rates = harvard.get_rates(dict_samp)
            print("actual prime rates:")
            print(actual_rates)
            self.currflow[pump].setText(actual_rates[pump]+' ul/hr')
        else:
            self.commandbar.setText("Can't prime pump while running")
            self.prime_btns[pump].setChecked(0)


    def getRates(self):
        rates = {}
        for pump in self.rates:
            if str(self.rates[pump].text()).strip()[1:].isdigit(): #kinda a hack to allow negative numbers
                rates[pump] = str(self.rates[pump].text()).strip()
            else:
                rates[pump] = '0'
                self.rates[pump].setText('0')
        return(rates)


    def shutdown(self):
        self.stop_all()

def main():
    app = QApplication(sys.argv)
    ex = PumpControl()
    ret = app.exec_()
    ex.shutdown()
    sys.exit(ret)


if __name__ == '__main__':
    main()
