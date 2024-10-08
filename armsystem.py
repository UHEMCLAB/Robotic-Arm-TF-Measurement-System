# -*- coding: utf-8 -*-
# 
# The authors of this report or the Dept of Health and Human Services, shall not be held liable for any direct,
# indirect, consequential, special or other damages suffered by the manufacturer of the device 
# or product or by other parties, as a result of the use of the report results, data, or other 
# deliverables. The author of this work disclaim any liability for the acts of any physician, 
# individual, group, or entity acting independently or on behalf of any organization utilizing 
# this information for any medical procedure, activity, service, or other situation.

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt
import qwt
from qwt import QwtPlot

from xarm import version
from xarm.wrapper import XArmAPI

import math
import time
import datetime
import csv
import threading
import pyvisa

import numpy as np
import pandas as pd

class MainWindow(QtWidgets.QWidget):
    points_set = []
    VNAdata_list = []
    x_plotMag64 = []
    x_plotPhase64 = []
    x_plotMag128 = []
    x_plotPhase128 = []
    is_recording = False

    # initial window
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.setupPlot()
        self.setupWidget()
        self.setupArm()
        self.setupVNA()

    def setupUi(self):
        self.setObjectName("MainWindow")
        self.resize(1100, 700)
        self.setWindowTitle("Version2.5")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

    def setupPlot(self):
        self.plotMag64 = QwtPlot("64M Mag", self)
        self.plotMag64.setGeometry(QtCore.QRect(10, 50, 331, 251))
        #self.plotMag64.setAxisScale(self.plotMag64.xBottom, 0, 120)
        #self.plotMag64.setAxisScale(self.plotMag64.yLeft, 0, 1)
        self.plotMag64.setAxisAutoScale(self.plotMag64.xBottom)
        self.plotMag64.setAxisAutoScale(self.plotMag64.yLeft)

        self.plotPhase64 = QwtPlot("64M Phase", self)
        self.plotPhase64.setGeometry(QtCore.QRect(360, 50, 331, 251))
        #self.plotPhase64.setAxisScale(self.plotPhase64.xBottom, 0, 120)
        #self.plotPhase64.setAxisScale(self.plotPhase64.yLeft, -180, 180)
        self.plotPhase64.setAxisAutoScale(self.plotPhase64.xBottom)
        self.plotPhase64.setAxisAutoScale(self.plotPhase64.yLeft)

        self.plotMag128 = QwtPlot("128M Mag", self)
        self.plotMag128.setGeometry(QtCore.QRect(10, 370, 331, 251))
        #self.plotMag128.setAxisScale(self.plotMag128.xBottom, 0, 120)
        #self.plotMag128.setAxisScale(self.plotMag128.yLeft, 0, 1)
        self.plotMag128.setAxisAutoScale(self.plotMag128.xBottom)
        self.plotMag128.setAxisAutoScale(self.plotMag128.yLeft)

        self.plotPhase128 = QwtPlot("128M Phase", self)
        self.plotPhase128.setGeometry(QtCore.QRect(360, 370, 331, 251))
        #self.plotPhase128.setAxisScale(self.plotPhase128.xBottom, 0, 120)
        #self.plotPhase128.setAxisScale(self.plotPhase128.yLeft, -180, 180)
        self.plotPhase128.setAxisAutoScale(self.plotPhase128.xBottom)
        self.plotPhase128.setAxisAutoScale(self.plotPhase128.yLeft)

    def setupWidget(self):
        # button
        self.buttonCali = QtWidgets.QPushButton("Calibration", self)
        self.buttonCali.setGeometry(QtCore.QRect(920, 100, 91, 31))
        self.buttonCali.clicked.connect(self.calibrateVNA)

        self.buttonStopall = QtWidgets.QPushButton("STOP!!!", self)
        self.buttonStopall.setGeometry(QtCore.QRect(920, 200, 91, 31))
        self.buttonStopall.setStyleSheet("background-color:#fc7b6d;")
        self.buttonStopall.clicked.connect(self.emergencyStop)

        self.buttonS21 = QtWidgets.QPushButton("Save Data", self)
        self.buttonS21.setGeometry(QtCore.QRect(760, 200, 91, 31))
        self.buttonS21.clicked.connect(self.saveS21)

        self.buttonToroff = QtWidgets.QPushButton("Torque Off", self)
        self.buttonToroff.setGeometry(QtCore.QRect(920, 280, 91, 31))
        self.buttonToroff.clicked.connect(self.torqueOff)

        self.buttonToron = QtWidgets.QPushButton("Torque On", self)
        self.buttonToron.setGeometry(QtCore.QRect(920, 330, 91, 31))
        self.buttonToron.clicked.connect(self.torqueOn)

        self.buttonSavep = QtWidgets.QPushButton("Save Point", self)
        self.buttonSavep.setGeometry(QtCore.QRect(920, 380, 91, 31))
        self.buttonSavep.clicked.connect(self.getcurrentpoint)

        self.buttonPlanm = QtWidgets.QPushButton("Plan n Move", self)
        self.buttonPlanm.setGeometry(QtCore.QRect(920, 430, 91, 31))
        #self.buttonPlanm.clicked.connect(self.plannMove)
        self.buttonPlanm.clicked.connect(self.plannMoveThread)

        self.buttonFixedpoz = QtWidgets.QPushButton("Fixed", self)
        self.buttonFixedpoz.setGeometry(QtCore.QRect(920, 510, 91, 31))
        self.buttonFixedpoz.clicked.connect(self.gotofixedposition)

        self.buttonfixedmove = QtWidgets.QPushButton("Move", self)
        self.buttonfixedmove.setGeometry(QtCore.QRect(920, 560, 91, 31))
        #self.buttonfixedmove.clicked.connect(self.startMoveThread)
        #self.buttonfixedmove.clicked.connect(self.manualMeasure)
        #self.buttonfixedmove.clicked.connect(self.measureCurve)
        self.buttonfixedmove.clicked.connect(self.measuretrajectoryide)

        self.buttonHome = QtWidgets.QPushButton("Home Pose", self)
        self.buttonHome.setGeometry(QtCore.QRect(760, 620, 91, 31))
        self.buttonHome.clicked.connect(self.gotoHomepose)

        self.buttonClean = QtWidgets.QPushButton("Clear Data", self)
        self.buttonClean.setGeometry(QtCore.QRect(920, 620, 91, 31))
        self.buttonClean.clicked.connect(self.cleandata)


        # list
        self.listWidgetPoint = QtWidgets.QListWidget(self)
        self.listWidgetPoint.setGeometry(QtCore.QRect(760, 300, 131, 161))


        # label
        self.labelCali = QtWidgets.QLabel("Calibration: Set frequency range/MHz", self)
        self.labelCali.setGeometry(QtCore.QRect(760, 46, 261, 21))
        self.labelSavedata = QtWidgets.QLabel("Save Data both Magnitude and Phase", self)
        self.labelSavedata.setGeometry(QtCore.QRect(760, 166, 251, 21))
        self.labelMinf = QtWidgets.QLabel("MIN", self)
        self.labelMinf.setGeometry(QtCore.QRect(860, 80, 41, 31))
        self.labeMaxf = QtWidgets.QLabel("MAX", self)
        self.labeMaxf.setGeometry(QtCore.QRect(860, 120, 41, 31))

        self.labelPointl = QtWidgets.QLabel("Position List", self)
        self.labelPointl.setGeometry(QtCore.QRect(760, 276, 121, 21))

        self.labelStep = QtWidgets.QLabel("Step(cm)", self)
        self.labelStep.setGeometry(QtCore.QRect(830, 510, 91, 31))
        self.labelLeadLen = QtWidgets.QLabel("Length(cm)", self)
        self.labelLeadLen.setGeometry(QtCore.QRect(830, 560, 91, 31))
        #self.labelZ = QtWidgets.QLabel("Z", self)
        #self.labelZ.setGeometry(QtCore.QRect(760, 630, 16, 21))


        #spinbox
        self.spinBoxMinf = QtWidgets.QSpinBox(self)
        self.spinBoxMinf.setGeometry(QtCore.QRect(760, 80, 91, 31))
        self.spinBoxMinf.setValue(20)
        self.spinBoxMinf.setMinimum(20)
        self.spinBoxMinf.setMaximum(400)
        self.spinBoxMaxf = QtWidgets.QSpinBox(self)
        self.spinBoxMaxf.setGeometry(QtCore.QRect(760, 120, 91, 31))
        self.spinBoxMaxf.setValue(144)
        self.spinBoxMaxf.setMinimum(144)
        self.spinBoxMaxf.setMaximum(400)

        self.spinBoxStep = QtWidgets.QDoubleSpinBox(self)
        self.spinBoxStep.setGeometry(QtCore.QRect(760, 510, 61, 31))
        self.spinBoxStep.setDecimals(1)
        self.spinBoxStep.setSingleStep(0.1)
        self.spinBoxStep.setValue(0.5)
        self.spinBoxStep.setMinimum(0)
        self.spinBoxStep.setMaximum(2)
        
        self.spinBoxLeadLen = QtWidgets.QDoubleSpinBox(self)
        self.spinBoxLeadLen.setGeometry(QtCore.QRect(760, 560, 61, 31))
        self.spinBoxLeadLen.setDecimals(1)
        self.spinBoxLeadLen.setSingleStep(0.5)
        self.spinBoxLeadLen.setValue(0.0)
        self.spinBoxLeadLen.setMinimum(0)
        self.spinBoxLeadLen.setMaximum(100)


        # line
        self.lineVert = QtWidgets.QFrame(self)
        self.lineVert.setGeometry(QtCore.QRect(710, 20, 20, 651))
        self.lineVert.setFrameShape(QtWidgets.QFrame.VLine)
        self.lineVert.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.lineHori1 = QtWidgets.QFrame(self)
        self.lineHori1.setGeometry(QtCore.QRect(750, 250, 281, 16))
        self.lineHori1.setFrameShape(QtWidgets.QFrame.HLine)
        self.lineHori1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.lineHori2 = QtWidgets.QFrame(self)
        self.lineHori2.setGeometry(QtCore.QRect(750, 480, 281, 16))
        self.lineHori2.setFrameShape(QtWidgets.QFrame.HLine)
        self.lineHori2.setFrameShadow(QtWidgets.QFrame.Sunken)

    def setupArm(self):
        self.arm = XArmAPI('192.168.1.240')
        self.arm.motion_enable(enable=True)
        self.arm.set_mode(0)
        self.arm.set_state(state=0)
        #self.arm.reset(wait=True)

        self.arm.set_tcp_offset([0.0, 0.0, 104.0, 0.0, 0.0, 0.0])
        self.arm.set_teach_sensitivity(5)

    def setupVNA(self):
        rm = pyvisa.ResourceManager('@py')
        #Connect to a Socket on the local machine at 5025
        try:
            self.CMT = rm.open_resource('TCPIP0::127.0.0.1::5025::SOCKET')
        except:
            print("Failure to connect to VNA!")
            print("Check network settings")
        #The VNA ends each line with this. Reads will time out without this
        self.CMT.read_termination='\n'
        #Set longer timeout period for slower sweeps
        self.CMT.timeout = 10000

        ''' set up the VNA '''
        self.CMT.write('DISP:WIND:SPL 6') 
        self.CMT.write('CALC1:PAR:COUN 4') 

        self.CMT.write('CALC1:PAR1:DEF S21') 
        self.CMT.write('CALC1:PAR2:DEF S21') 
        self.CMT.write('CALC1:PAR3:DEF S11') 
        self.CMT.write('CALC1:PAR4:DEF S11') 

        # select the trace first and then choose a measurement format
        self.CMT.write('CALC1:PAR1:SEL')
        self.CMT.write('CALC1:FORM MLIN')  # lin Mag format
        self.CMT.write('CALC1:PAR2:SEL')
        self.CMT.write('CALC1:FORM PHAS') # phase format

        self.CMT.write('CALC1:PAR3:SEL')
        self.CMT.write('CALC1:FORM MLIN')  # lin Mag format
        self.CMT.write('CALC1:PAR4:SEL')
        self.CMT.write('CALC1:FORM PHAS') # phase format

        self.CMT.write('SOUR1:POW:AMPL 3')
        
    def gotoHomepose(self):
        self.torqueOn()
        self.arm.move_gohome()

    def calibrateVNA(self):
        points = 125
        minf = self.spinBoxMinf.value
        maxf = self.spinBoxMaxf.value
        #points = maxf - minf + 1
        #f'{minf:.2E}'
        
        print("Using ACM2506")
        #self.CMT.write("SOUR:POW 0")
        self.CMT.write("SENS1:FREQ:STAR 2E7")
        self.CMT.write("SENS1:FREQ:STOP 1.44E8")
        self.CMT.write("SENS1:SWE:POIN 125")
        self.CMT.write("SENS:CORR:COLL:ECAL:SOLT2 2,1")
        opc_response = self.CMT.query("*OPC?")

        self.CMT.write('SOUR1:POW:AMPL 3')

    def collectSingleVNAdata(self):
        #44
        #pos64 = 64 - self.spinBoxMinf.value
        #108
        #pos128 = 128 - self.spinBoxMinf.value

        self.CMT.write('TRIG:SOUR BUS')
        # Always end an *OPC? command after all the VNA setups to make sure the setups are complete before making measurement
        self.CMT.query('*OPC?')

        count = 0
        # Trigger a measurement
        self.CMT.write('TRIG:SING')  # Trigger a single sweep
        self.CMT.query('*OPC?')  # Wait for measurement to complete

        # Read frequency data (NOTE: the data read from VNA is a string that contains comma separated data points)
        Freq = self.CMT.query("SENS1:FREQ:DATA?")  # Get data as string
        # Split the strings by commas
        Freq = Freq.split(",")
        Frequency = [Freq[44], Freq[108]]
        
        LoopPhase64 = []
        LoopPhase128 = []
        LoopMag64 = []
        LoopMag128 = []

        for count in range(6):
            count+=1

            # Trigger a measurement
            self.CMT.write('TRIG:SING')  # Trigger a single sweep
            self.CMT.query('*OPC?')  # Wait for measurement to complete
            # Read frequency data (NOTE: the data read from VNA is a string that contains comma separated data points)
            #Freq = self.CMT.query("SENS1:FREQ:DATA?")  # Get data as string
            # Read log mag data
            self.CMT.write('CALC1:PAR1:SEL')
            M = self.CMT.query("CALC1:DATA:FDAT?")  # Get data as string
            # Read phase data
            self.CMT.write('CALC1:PAR2:SEL')
            P = self.CMT.query("CALC1:DATA:FDAT?")  # Get data as string

            ''' change the trigger source back to internal after automation '''
            #self.CMT.write('TRIG:SOUR INT')

            ''' print results '''
            # Split the strings by commas
            #Freq = Freq.split(",")
            #Frequency = [Freq[44], Freq[108]]
            P = P.split(",")
            LoopPhase64.append(P[88])
            LoopPhase128.append(P[216])
            M = M.split(",")
            LoopMag64.append(M[88])
            LoopMag128.append(M[216])

            # remove the 0s from the data (every other number)
            #P = P[::2]
            #M = M[::2]

        LoopMag64 = [float(m) for m in LoopMag64]
        LoopMag64.sort()
        LoopMag128 = [float(m) for m in LoopMag128]
        LoopMag128.sort()
        LoopPhase64 = [float(p) for p in LoopPhase64]
        LoopPhase64.sort()
        LoopPhase128 = [float(p) for p in LoopPhase128]
        LoopPhase128.sort()

        Mag64 = sum(LoopMag64[1:5])/4
        Mag128 = sum(LoopMag128[1:5])/4
        Phase64 = sum(LoopPhase64[1:5])/4
        Phase128 = sum(LoopPhase128[1:5])/4

        self.x_plotMag64.append(Mag64)
        self.x_plotPhase64.append(Phase64)
        self.x_plotMag128.append(Mag128)
        self.x_plotPhase128.append(Phase128)
        self.VNAdata_list.append([Mag64, Phase64, Mag128, Phase128])

        self.CMT.write('TRIG:SOUR INT')

        return [Mag64, Phase64, Mag128, Phase128]

    def saveS21(self):
        currentTime = datetime.datetime.now().strftime("%Hh_%Mm_%Ss")
        dataFile = open('data_' + currentTime + '.csv', 'w', newline='')
        writer = csv.writer(dataFile)
        writer.writerow(['Number', '64 Mag', '64 Phase', '128 Mag', '128 Phase'])

        VNAdata = self.VNAdata_list
        for i in range(len(VNAdata)):
            writer.writerow([i+1, VNAdata[i][0], VNAdata[i][1], VNAdata[i][2], VNAdata[i][3]])
        dataFile.close()

        self.cleanup()
        self.x_plotMag64 = []
        self.x_plotPhase64 = []
        self.x_plotMag128 = []
        self.x_plotPhase128 = []

    def saveS11(self):
        pass

    def onstartMovethreadfinished(self):
        self.plot()
        #clean up
        #self.cleanup()
        self.x_plotMag64 = []
        self.x_plotPhase64 = []
        self.x_plotMag128 = []
        self.x_plotPhase128 = []
        #self.points_set.reverse()
        
    def startMoveThread(self):
        self.worker_thread = WorkerThread(self.startMove, args=(), kwargs={})
        self.worker_thread.finished.connect(self.onstartMovethreadfinished)

        # Start the worker thread
        self.worker_thread.start()

    def startMove(self):
        self.torqueOn()
        step = self.spinBoxStep.value()*10
        length = self.spinBoxLeadLen.value()*10
        waypoints = round(length/step)
        fixedpoz = self.points_set[0][0:3]
        self.arm.set_position(*fixedpoz, pitch=0, yaw=0, speed=30, wait=True)
        self.collectSingleVNAdata()
        yaxis = self.points_set[0][1]
        for i in range(waypoints):
            y = yaxis - (i+1)*step
            self.arm.set_position(y=y, speed=40, wait=True)
            time.sleep(0.1)
            print(i+1)
            self.collectSingleVNAdata()
        print(self.arm.get_position())
     
    def gotofixedposition(self):
        self.clearplot()
        fixedpoz = self.points_set[0][0:3]
        print(fixedpoz)
        self.torqueOn()
        self.arm.set_position(*fixedpoz, roll=180, pitch=0, yaw=0, speed=60, wait=True)

    def clearplot(self):
        self.plotMag64.detachItems()
        self.plotMag64.replot()
        self.plotPhase64.detachItems()
        self.plotPhase64.replot()
        self.plotMag128.detachItems()
        self.plotMag128.replot()
        self.plotPhase128.detachItems()
        self.plotPhase128.replot()

    #measure quatercircle
    def measureCurve(self):
        time.sleep(1)
        print('startnow')
        _, current_position = self.arm.get_position()

        x = current_position[0]
        y = current_position[1]
        z = current_position[2]
        roll = -145
        leadlength = 550
        delta_y = leadlength*math.cos(math.pi*35/180)
        delta_z = leadlength*math.sin(math.pi*35/180)
        step = 5
        step_number = round(leadlength/5)
        delta_y_step = delta_y/step_number
        delta_z_step = delta_z/step_number

        for i in range(step_number+1):
            
            self.arm.set_position(x=x, y=y, z=z, roll=-145, speed=50, is_radian=False, wait=True)
            y = y+delta_y_step
            z = z+delta_z_step
            time.sleep(0.1)
            self.collectSingleVNAdata()
        time.sleep(0.1)
        self.collectSingleVNAdata()
        
        self.plot()


    def measuretrajectorypipo(self):

        #x = [0.00, -0.12, -0.23, -0.35, -0.46, -0.58, -0.69, -0.80, -0.91, -1.01, -1.12, -1.22, -1.32, -1.41, -1.50, -1.58, -1.66, -1.74, -1.81, -1.88, -1.94, -1.99, -2.04, -2.08, -2.11, -2.14, -2.16, -2.17, -2.18, -2.17, -2.16, -2.14, -2.10, -2.06, -2.01, -1.95, -1.88, -1.80, -1.70, -1.60, -1.48, -1.35, -1.21, -1.06, -0.89, -0.72, -0.52, -0.32, -0.10, 0.14, 0.57, 1.94, 4.21, 7.27, 11.04, 15.36, 20.09, 25.06, 30.10, 35.02, 39.62, 43.70, 47.13, 49.81, 51.64, 52.55, 52.71, 52.82, 52.92, 53.01, 53.09, 53.16, 53.23, 53.29, 53.34, 53.39, 53.43, 53.46, 53.49, 53.51, 53.52, 53.53, 53.54, 53.54, 53.54, 53.53, 53.52, 53.50, 53.49, 53.47, 53.44, 53.42, 53.39, 53.36, 53.33, 53.29, 53.26, 53.23, 53.19, 53.16, 53.12, 53.09, 53.05, 53.02, 52.99, 52.96, 52.93, 52.91, 52.88, 52.86, 52.84, 52.83, 52.81, 52.81, 52.80]
        #y = [0.00, 4.99, 9.98, 14.97, 19.97, 24.96, 29.95, 34.94, 39.93, 44.92, 49.91, 54.91, 59.90, 64.89, 69.88, 74.87, 79.87, 84.86, 89.85, 94.84, 99.84, 104.83, 109.82, 114.82, 119.81, 124.80, 129.80, 134.79, 139.79, 144.78, 149.78, 154.77, 159.77, 164.76, 169.76, 174.75, 179.75, 184.75, 189.74, 194.74, 199.74, 204.74, 209.73, 214.73, 219.73, 224.73, 229.73, 234.73, 239.73, 244.73, 249.71, 254.51, 258.98, 262.98, 266.35, 268.94, 270.59, 271.24, 270.94, 269.74, 267.67, 264.75, 261.10, 256.86, 252.20, 247.29, 242.30, 237.30, 232.31, 227.31, 222.32, 217.32, 212.33, 207.33, 202.34, 197.34, 192.35, 187.36, 182.36, 177.37, 172.37, 167.38, 162.38, 157.39, 152.39, 147.40, 142.41, 137.41, 132.42, 127.42, 122.43, 117.43, 112.44, 107.44, 102.45, 97.45, 92.46, 87.47, 82.47, 77.48, 72.48, 67.49, 62.49, 57.50, 52.50, 47.51, 42.52, 37.52, 32.53, 27.53, 22.54, 17.54, 12.55, 7.55, 2.56]
        #z = [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
        #spline 1, turn at 20,32
        #x = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        #y = [0, 5.007646452, 10.01481653, 15.02103387, 20.02582209, 25.02870483, 30.0292057, 35.02684835, 40.0211564, 45.01165347, 49.99786319, 54.97930921, 59.95551513, 64.92600459, 69.89030122, 74.84792865, 79.7984105, 84.7412704, 89.67603199, 94.62534835, 99.37566956, 102.512672, 104.7335216, 106.9037289, 109.185528, 111.485117, 113.7083251, 115.7669411, 117.8287465, 120.4085234, 123.8565087, 128.0202297, 132.6647002, 137.558672, 142.5496134, 147.5616127, 152.5596595, 157.5455661, 162.5226612, 167.4942739, 172.4637331, 177.4343678, 182.4093977, 187.3893386, 192.3718876, 197.3547366, 202.3370152, 207.3187641, 212.3000389, 217.2808947, 222.261387, 227.2415711, 232.2215023, 237.2012359, 242.1808272, 247.1603317, 252.1420995, 257.1224164, 262.1027333, 267.0830501, 272.063367, 277.0436839, 282.0240007, 287.0043176, 291.9846344, 296.9649513, 301.9452682, 306.925585, 311.9059019, 316.8862187, 321.8665356, 326.8468525, 331.8271693, 336.8074862, 341.787803, 346.7681199, 351.7484368, 356.7287536, 361.7090705]
        #z = [0, -0.053624893, -0.106304013, -0.15709159, -0.205041851, -0.249209024, -0.288647338, -0.32241102, -0.349554298, -0.369131401, -0.380196556, -0.381803992, -0.373007937, -0.352862618, -0.320422265, -0.274741104, -0.214873364, -0.139873273, -0.048795059, 0.013386608, 0.469869392, 4.077837569, 9.322913729, 14.36981388, 18.89935514, 23.14430966, 27.33824402, 31.70900551, 36.23875539, 40.57636022, 44.38298463, 47.41556519, 49.44675824, 50.27207224, 50.16821734, 49.85213982, 49.67667582, 49.62356277, 49.65925141, 49.7501925, 49.8628368, 49.96363505, 50.0201367, 50.02714556, 50.00787009, 49.98557121, 49.96902114, 49.95780809, 49.9513744, 49.94916241, 49.95061444, 49.95517283, 49.96227991, 49.97137801, 49.98190948, 49.99331663, 49.99644166, 50.00398659, 50.01153151, 50.01907644, 50.02662136, 50.03416629, 50.04171122, 50.04925614, 50.05680107, 50.06434599, 50.07189092, 50.07943584, 50.08698077, 50.0945257, 50.10207062, 50.10961555, 50.11716047, 50.1247054, 50.13225032, 50.13979525, 50.14734018, 50.1548851, 50.16243003]
        #spline 2, turn at 20
        x = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        y = [0, 5.015244205, 10.03002161, 15.04386541, 20.05630882, 25.06688503, 30.07512724, 35.08056865, 40.08274246, 45.08118187, 50.07542009, 55.06499031, 60.04942573, 65.02825955, 70.00102498, 74.96725521, 79.92648345, 84.87824288, 89.82206673, 94.78430286, 99.51067537, 102.6312842, 104.8169459, 106.8682444, 108.9991151, 111.2314777, 113.5871417, 116.0872798, 118.7318884, 121.4958531, 124.3620945, 127.3222335, 130.368208, 133.4919557, 136.6841094, 139.9085608, 143.104163, 146.2096647, 149.1984455, 152.0895718, 154.905235, 157.6676264, 160.3989372, 163.1213588, 165.8570825, 168.6282995, 171.4572012, 174.3659788, 177.3768237, 180.5118665, 183.7704368, 187.0949545, 190.4191069, 193.6765812, 196.8121892, 199.8311374, 202.7590308, 205.62149, 208.4441357, 211.2560017, 214.2532681, 217.2505346, 220.247801, 223.2450674, 226.2423339, 229.2396003, 232.2368667, 235.2341332, 238.2313996, 241.2286661, 244.2259325, 247.2231989, 250.2204654, 253.2177318, 256.2149982, 259.2122647, 262.2095311, 265.2067975, 268.204064]
        z = [0, -0.053383018, -0.105821408, -0.15637054, -0.204085787, -0.24802252, -0.28723611, -0.320781929, -0.347715349, -0.367091741, -0.377966476, -0.379394925, -0.370432462, -0.350134456, -0.317556279, -0.271753303, -0.2117809, -0.13669444, -0.045549296, 0.008336253, 0.537866902, 4.228864956, 9.514006827, 14.60896196, 19.20744432, 23.48694675, 27.62523934, 31.79609222, 36.0402537, 40.24131105, 44.34452165, 48.35998034, 52.30014307, 56.17746577, 60.00520653, 63.81306008, 67.64611167, 71.54939801, 75.54214357, 79.60951965, 83.73436842, 87.89953207, 92.08785278, 96.28217273, 100.4653341, 104.6201791, 108.7295498, 112.7762885, 116.7432373, 120.6132861, 124.3871837, 128.1102551, 131.8346653, 135.612579, 139.4873868, 143.4548428, 147.4946124, 151.5863482, 155.7097028, 159.3547783, 163.2648432, 167.1749081, 171.084973, 174.9950379, 178.9051029, 182.8151678, 186.7252327, 190.6352976, 194.5453625, 198.4554274, 202.3654924, 206.2755573, 210.1856222, 214.0956871, 218.005752, 221.9158169, 225.8258819, 229.7359468, 233.6460117]
        #spline 4, turn at 20, 34
        #x = [0, -8.25E-08, -1.62E-07, -2.36E-07, -3.01E-07, -3.54E-07, -3.93E-07, -4.15E-07, -4.16E-07, -3.94E-07, -3.46E-07, -2.68E-07, -1.59E-07, -1.52E-08, 1.58E-07, 3.06E-07, 3.6E-07, 2.5E-07, -8.46E-08, 4.31E-07, -4.74E-07, 1.73E-05, -4.06E-05, -0.000141052, -2.91E-05, 0.00037281, 0.000145067, -0.001545286, -0.003065266, -0.001866897, 0.003656004, 0.000442723, -0.012758662, 0.047198965, 0.039393828, -0.243162494, -0.064895641, 1.550001308, 4.642347866, 8.95942679, 14.24841873, 20.25650432, 26.73086422, 33.41867906, 40.0740398, 46.50843519, 52.56178231, 58.0742016, 62.88581348, 66.8367384, 69.76709678, 71.52131528, 72.11035977, 71.76103754, 70.71453083, 69.21202189, 67.49237525, 65.64834268, 63.54205135, 61.01529671, 57.92023091, 54.23231158, 50.00795143, 45.32437954, 40.38826359, 35.45882906, 30.71444457, 26.15573036, 21.75984392, 17.51067089, 13.40200202, 9.425662877, 5.558533157, 1.772454931, -1.960733585, -5.669194173, -9.381088615, -13.11571685, -16.81960417, -20.40357429, -23.77820477, -26.85712797, -29.86742371, -33.6168378, -38.7605022, -44.42218651, -49.0627644, -51.14045385]
        #y = [0, 4.890282662, 9.780491287, 14.67055184, 19.56039027, 24.44993256, 29.33910466, 34.22783253, 39.11604215, 44.00365946, 48.89061043, 53.77682103, 58.66221722, 63.54672495, 68.43049925, 73.31490592, 78.20170944, 83.0926745, 87.98939297, 92.86443815, 97.77567017, 101.6977795, 104.2828216, 106.0091261, 107.6267555, 109.7379047, 112.0839294, 114.2237016, 116.3011307, 118.6772485, 121.6800381, 125.1180615, 128.6358219, 132.8784999, 137.937708, 143.2211802, 147.8588205, 151.027431, 152.7296155, 153.226844, 152.7806769, 151.6526743, 150.1043963, 148.3974031, 146.784001, 145.439631, 144.5016645, 144.1072, 144.3933364, 145.4971726, 147.5558072, 150.7014026, 154.8752072, 159.7710374, 165.0662309, 170.4381251, 175.5663309, 180.2737653, 184.6095404, 188.6427094, 192.4219591, 195.7534929, 198.2843146, 199.7099302, 200.0679595, 199.536006, 198.2884295, 196.4915516, 194.3098901, 191.8693163, 189.2388071, 186.47487, 183.5911612, 180.5868931, 177.4612671, 174.2134847, 170.8427472, 167.3559832, 163.8235764, 160.3470399, 157.0281019, 153.9652877, 150.9285089, 147.0789152, 141.7375637, 135.8303234, 130.9777543, 128.8031995]
        #z = [0, -0.006593029, -0.012953928, -0.018850565, -0.02405081, -0.028322532, -0.031433602, -0.033151887, -0.033245257, -0.031481582, -0.027628731, -0.021454574, -0.012726979, -0.001213816, 0.012598924, 0.024428945, 0.028744124, 0.020011574, -0.006759738, 0.034421491, -0.037854317, 2.635510151, 7.203470151, 11.80541432, 16.28476512, 20.62243214, 24.96116596, 29.44685389, 33.9284911, 38.1449064, 41.86958625, 45.41771302, 48.99671647, 50.67115009, 50.41972617, 49.99466288, 49.83067058, 49.76873326, 49.75925808, 49.78786095, 49.84017003, 49.90181347, 49.95841944, 49.99561609, 50.0007252, 49.97513582, 49.92720437, 49.86533708, 49.79794021, 49.73341999, 49.68018266, 49.64651233, 49.63596897, 49.64598998, 49.67360495, 49.71584351, 49.7697376, 49.83246732, 49.90144654, 49.97410973, 50.04780102, 50.11878856, 50.18263413, 50.23534142, 50.27594468, 50.30472144, 50.32256456, 50.33170877, 50.33455572, 50.33291995, 50.3277517, 50.3198487, 50.30955771, 50.29707348, 50.28259067, 50.26630389, 50.2484078, 50.22913537, 50.2090345, 50.18880756, 50.16915799, 50.1507688, 50.1322277, 50.10824078, 50.07453323, 50.0370594, 50.00620163, 49.99236]

        _, current_position = self.arm.get_position()

        xoffset = current_position[0]
        yoffset = current_position[1]
        zoffset = current_position[2]

        self.arm.set_position(x[0]+xoffset, -y[0]+yoffset, z[0]+zoffset, yaw=0, speed=40, is_radian=False, wait=True)
        self.collectSingleVNAdata()

        time.sleep(5)
        for i in range(1, 21):
            self.arm.set_position(x[i]+xoffset, -y[i]+yoffset, z[i]+zoffset, speed=30, is_radian=False, wait=True)
            time.sleep(0.1)
            self.collectSingleVNAdata()

        time.sleep(5)
        self.arm.set_position(roll=135, speed=30, is_radian=False, wait=True)
        time.sleep(5)
        for i in range(21, 32):
            self.arm.set_position(x[i]+xoffset, -y[i]+yoffset, z[i]+zoffset, speed=30, is_radian=False, wait=True)
            time.sleep(0.1)
            self.collectSingleVNAdata()
        
        #time.sleep(5)
        #self.arm.set_position(roll=179.9, speed=30, is_radian=False, wait=True)
        #time.sleep(5)
        for i in range(32, 79):
            self.arm.set_position(x[i]+xoffset, -y[i]+yoffset, z[i]+zoffset, speed=30, is_radian=False, wait=True)
            time.sleep(0.1)
            self.collectSingleVNAdata()

        self.plot()


    def measuretrajectorypipo2(self):

        #x = [0.00, -0.12, -0.23, -0.35, -0.46, -0.58, -0.69, -0.80, -0.91, -1.01, -1.12, -1.22, -1.32, -1.41, -1.50, -1.58, -1.66, -1.74, -1.81, -1.88, -1.94, -1.99, -2.04, -2.08, -2.11, -2.14, -2.16, -2.17, -2.18, -2.17, -2.16, -2.14, -2.10, -2.06, -2.01, -1.95, -1.88, -1.80, -1.70, -1.60, -1.48, -1.35, -1.21, -1.06, -0.89, -0.72, -0.52, -0.32, -0.10, 0.14, 0.57, 1.94, 4.21, 7.27, 11.04, 15.36, 20.09, 25.06, 30.10, 35.02, 39.62, 43.70, 47.13, 49.81, 51.64, 52.55, 52.71, 52.82, 52.92, 53.01, 53.09, 53.16, 53.23, 53.29, 53.34, 53.39, 53.43, 53.46, 53.49, 53.51, 53.52, 53.53, 53.54, 53.54, 53.54, 53.53, 53.52, 53.50, 53.49, 53.47, 53.44, 53.42, 53.39, 53.36, 53.33, 53.29, 53.26, 53.23, 53.19, 53.16, 53.12, 53.09, 53.05, 53.02, 52.99, 52.96, 52.93, 52.91, 52.88, 52.86, 52.84, 52.83, 52.81, 52.81, 52.80]
        #y = [0.00, 4.99, 9.98, 14.97, 19.97, 24.96, 29.95, 34.94, 39.93, 44.92, 49.91, 54.91, 59.90, 64.89, 69.88, 74.87, 79.87, 84.86, 89.85, 94.84, 99.84, 104.83, 109.82, 114.82, 119.81, 124.80, 129.80, 134.79, 139.79, 144.78, 149.78, 154.77, 159.77, 164.76, 169.76, 174.75, 179.75, 184.75, 189.74, 194.74, 199.74, 204.74, 209.73, 214.73, 219.73, 224.73, 229.73, 234.73, 239.73, 244.73, 249.71, 254.51, 258.98, 262.98, 266.35, 268.94, 270.59, 271.24, 270.94, 269.74, 267.67, 264.75, 261.10, 256.86, 252.20, 247.29, 242.30, 237.30, 232.31, 227.31, 222.32, 217.32, 212.33, 207.33, 202.34, 197.34, 192.35, 187.36, 182.36, 177.37, 172.37, 167.38, 162.38, 157.39, 152.39, 147.40, 142.41, 137.41, 132.42, 127.42, 122.43, 117.43, 112.44, 107.44, 102.45, 97.45, 92.46, 87.47, 82.47, 77.48, 72.48, 67.49, 62.49, 57.50, 52.50, 47.51, 42.52, 37.52, 32.53, 27.53, 22.54, 17.54, 12.55, 7.55, 2.56]
        #z = [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
        #spline4
        x = [0, -8.63E-08, -1.7E-07, -2.47E-07, -3.15E-07, -3.71E-07, -4.11E-07, -4.34E-07, -4.35E-07, -4.12E-07, -3.61E-07, -2.8E-07, -1.66E-07, -1.51E-08, 1.66E-07, 3.2E-07, 3.76E-07, 2.61E-07, -9.09E-08, 4.55E-07, -1.9E-06, 1.26E-05, -4.37E-05, -9.17E-05, 0.000184394, 0.000423238, -0.000449385, -0.002422029, -0.003640344, -0.002078384, 0.003393404, -0.00173243, -0.010604145, 0.056671652, 0.016687248, -0.270241189, 0.050281627, 1.868618313, 5.133135305, 9.590754762, 14.98839884, 21.0729897, 27.5914495, 34.2907004, 40.9287495, 47.32464105, 53.31831538, 58.74973121, 63.45884728, 67.2856223, 70.070015, 71.66213969, 72.11274662, 71.65646608, 70.53472484, 68.98894962, 67.25404765, 65.38329616, 63.22877582, 60.63212162, 57.45311982, 53.68761274, 49.39317768, 44.65832754, 39.70616329, 34.79483465, 30.07577034, 25.53933451, 21.16287965, 16.93207911, 12.84112532, 8.880346193, 5.02492343, 1.246666666, -2.482614459, -6.191110302, -9.907011223, -13.64378495, -17.33736537, -20.89825419, -24.23693827, -27.2749434, -30.33865551, -34.26675779, -39.57924446, -45.19074266, -49.55794032, -51.1374909]
        y = [0, 4.890622606, 9.781217381, 14.67175649, 19.56221211, 24.45255641, 29.34276154, 34.2327997, 39.12264303, 44.01226371, 48.90163392, 53.79072581, 58.67951156, 63.56796333, 68.45614067, 73.34455876, 78.23388091, 83.12477046, 88.01781986, 92.90265328, 97.77559033, 101.7752112, 104.5966041, 106.7507478, 108.7711431, 110.8971968, 113.0571228, 115.2241052, 117.4698734, 119.8753326, 122.5232392, 125.5287309, 129.0890257, 133.5102108, 138.6124338, 143.8604144, 148.3544405, 151.3291957, 152.8662265, 153.2281673, 152.6776528, 151.4773175, 149.8897959, 148.1777227, 146.5887658, 145.2881825, 144.4130168, 144.1002876, 144.4870143, 145.7102158, 147.9069113, 151.202486, 155.4924829, 160.4617977, 165.7875405, 171.1468212, 176.2231418, 180.8780812, 185.1704789, 189.1694157, 192.9082826, 196.15295, 198.547902, 199.8179652, 200.0436766, 199.4031653, 198.0697391, 196.2094255, 193.9856571, 191.5140709, 188.8613681, 186.0798433, 183.1783653, 180.1561345, 177.0123518, 173.7462177, 170.3569329, 166.8565353, 163.3246679, 159.8631486, 156.5738089, 153.5469066, 150.4482505, 146.4065641, 140.8845315, 135.0272033, 130.4595337, 128.8065131]
        z = [0, 0.008762218, 0.017215721, 0.025051795, 0.031961726, 0.037636799, 0.0417683, 0.044047515, 0.044165729, 0.041814227, 0.036684295, 0.028467219, 0.016854285, 0.001536777, -0.016824936, -0.032516008, -0.038179035, -0.026455741, 0.009225408, -0.046228262, 0.504555724, 3.210918287, 7.303580997, 11.68544593, 16.11787095, 20.51844922, 24.92636896, 29.34455066, 33.70664094, 37.9398362, 41.97966063, 45.90674851, 49.37796268, 50.68792785, 50.34577077, 49.96887171, 49.81896054, 49.75907425, 49.7526948, 49.78481264, 49.8404182, 49.90450191, 49.96205422, 49.99806557, 50.00033738, 49.97214933, 49.92208004, 49.85871283, 49.79063099, 49.72641782, 49.67465663, 49.64363643, 49.63583228, 49.64839081, 49.67826171, 49.72239467, 49.77774778, 49.84151306, 49.91114168, 49.98409825, 50.0576852, 50.12798929, 50.19054568, 50.24160629, 50.28058495, 50.30777811, 50.32428621, 50.332423, 50.33457267, 50.33239385, 50.32680237, 50.31855202, 50.30793942, 50.29515939, 50.28040674, 50.2638763, 50.24576287, 50.22632498, 50.20615668, 50.18596207, 50.1664453, 50.14823674, 50.12926037, 50.10401557, 50.06913032, 50.03195609, 50.0029033, 49.99238256]
        #spline5
        #x = [0, 0.000279774, -0.000654477, -0.000924383, -0.000740358, -0.000327404, 9.01E-05, 0.000365518, 0.00050658, 0.000539055, 0.000488739, 0.000381428, 0.000242915, 9.9E-05, -2.46E-05, -0.00010549, -0.000128959, -8.1E-05, 5.08E-05, 0.000179488, 5.68E-05, -0.000490693, -0.001068274, -0.001059829, 0.00015097, 0.002308828, 0.002392852, -0.002985682, -0.010479329, -0.008125803, 0.013631769, 0.004192241, -0.094535618, -0.107140165, 0.162863734, -0.311701243, -2.890429511, -7.188979472, -12.61935632, -18.59356525, -24.52361146, -29.82150014, -33.91972069, -36.57233749, -37.78890556, -37.58602759, -35.98030626, -33.00184856, -28.86912003, -23.93888028, -18.57107966, -13.12566855, -7.961938532, -3.314120548, 0.855730276, 4.62134707, 8.056462961, 11.23481108, 14.23012455, 17.1161365, 19.96658007, 22.85518838, 25.8501142, 28.94006747, 32.05461296, 35.12190573, 38.07010085, 40.82735336, 43.32181834, 45.48951037, 47.34655394, 48.95587005, 50.38096679, 51.68535225]
        #y = [0, 3.906490787, 11.95852741, 17.72938863, 21.95225951, 25.41033838, 28.88469545, 32.87959784, 37.35100958, 42.19037724, 47.28914738, 52.53876657, 57.83068137, 63.05633833, 68.10766588, 72.9536, 77.72393174, 82.56861386, 87.63337022, 92.77645205, 97.38996257, 100.9306488, 103.5340678, 105.6005727, 107.531086, 109.6360346, 111.938709, 114.4049672, 116.9775999, 119.5698966, 122.1153341, 124.9956386, 128.8493013, 133.5515543, 138.7077394, 143.1109577, 145.5765518, 146.546691, 146.6517472, 146.5220924, 146.7880984, 148.0801372, 150.9850397, 155.4061003, 160.7035452, 166.2226199, 171.3085702, 175.3337688, 178.048962, 179.4826999, 179.6699425, 178.6456493, 176.4451837, 173.1804825, 169.1301336, 164.5946379, 159.8744962, 155.2702095, 151.0822786, 147.6112042, 145.1574874, 144.021629, 144.4812526, 146.4882993, 149.7522392, 153.9767633, 158.8655627, 164.1223283, 169.4507512, 174.5749656, 179.4274765, 184.0625102, 188.5358196, 192.9031578]
        #z = [0, 0.00431247, -0.005543268, 0.001491972, 0.01233685, 0.0136017, -0.00803513, -0.057048292, -0.120387932, -0.182942133, -0.229598976, -0.245246545, -0.21477292, -0.123066185, 0.044691292, 0.256284635, 0.381256469, 0.276835634, -0.193090736, -0.712016318, -0.229495107, 2.179587453, 6.222508894, 11.13148225, 16.13771686, 20.68176599, 24.8684184, 28.93164145, 33.0206188, 37.17610474, 41.41024967, 45.29884082, 48.13236825, 49.77258915, 50.27759604, 50.15131222, 50.03980475, 49.99448114, 49.99715208, 50.02962824, 50.07372031, 50.11123896, 50.12493608, 50.11233948, 50.08271636, 50.04565777, 50.01075475, 49.98709014, 49.97665837, 49.97624951, 49.98253358, 49.99218055, 50.00186581, 50.00928664, 50.0143643, 50.01731251, 50.01834495, 50.01767535, 50.0155174, 50.0120848, 50.00759126, 50.00225048, 49.99630568, 49.9904202, 49.98557016, 49.98273913, 49.98291069, 49.98706843, 49.9961959, 50.01115489, 50.03156551, 50.0563226, 50.08431188, 50.11441908]
        unitvector = self.calculate_unit_vector(x, y)

        theta = []
        for i in range(len(x)-1):
            angle = self.calculate_angle(*unitvector[i])
            angle = round(angle-90, 2)
            theta.append(angle)

        _, current_position = self.arm.get_position()

        xoffset = current_position[0]
        yoffset = current_position[1]
        zoffset = current_position[2]

        time.sleep(5)
        self.arm.set_position(x[0]+xoffset, y[0]+yoffset, z[0]+zoffset, yaw=0, speed=50, is_radian=False, wait=True)
        self.collectSingleVNAdata()

        for i in range(1, 21):
            self.arm.set_position(x[i]+xoffset, -y[i]+yoffset, z[i]+zoffset, speed=30, is_radian=False, wait=True)
            time.sleep(0.1)
            self.collectSingleVNAdata()

        time.sleep(5)
        self.arm.set_position(roll=135, speed=30, is_radian=False, wait=True)
        time.sleep(5)
        for i in range(21, 33):
            self.arm.set_position(x[i]+xoffset, -y[i]+yoffset, z[i]+zoffset, speed=30, is_radian=False, wait=True)
            time.sleep(0.1)
            self.collectSingleVNAdata()
        time.sleep(5)
        self.arm.set_position(roll=179.9, speed=30, is_radian=False, wait=True)
        time.sleep(5)

        for i in range(33, 79):
            self.arm.set_position(-x[i]+xoffset, -y[i]+yoffset, z[i]+zoffset, yaw=theta[i], speed=30, is_radian=False, wait=True)
            time.sleep(0.1)
            self.collectSingleVNAdata()

        self.plot()


    def measuretrajectoryide(self):

        #x = [0.00, -0.12, -0.23, -0.35, -0.46, -0.58, -0.69, -0.80, -0.91, -1.01, -1.12, -1.22, -1.32, -1.41, -1.50, -1.58, -1.66, -1.74, -1.81, -1.88, -1.94, -1.99, -2.04, -2.08, -2.11, -2.14, -2.16, -2.17, -2.18, -2.17, -2.16, -2.14, -2.10, -2.06, -2.01, -1.95, -1.88, -1.80, -1.70, -1.60, -1.48, -1.35, -1.21, -1.06, -0.89, -0.72, -0.52, -0.32, -0.10, 0.14, 0.57, 1.94, 4.21, 7.27, 11.04, 15.36, 20.09, 25.06, 30.10, 35.02, 39.62, 43.70, 47.13, 49.81, 51.64, 52.55, 52.71, 52.82, 52.92, 53.01, 53.09, 53.16, 53.23, 53.29, 53.34, 53.39, 53.43, 53.46, 53.49, 53.51, 53.52, 53.53, 53.54, 53.54, 53.54, 53.53, 53.52, 53.50, 53.49, 53.47, 53.44, 53.42, 53.39, 53.36, 53.33, 53.29, 53.26, 53.23, 53.19, 53.16, 53.12, 53.09, 53.05, 53.02, 52.99, 52.96, 52.93, 52.91, 52.88, 52.86, 52.84, 52.83, 52.81, 52.81, 52.80]
        #y = [0.00, 4.99, 9.98, 14.97, 19.97, 24.96, 29.95, 34.94, 39.93, 44.92, 49.91, 54.91, 59.90, 64.89, 69.88, 74.87, 79.87, 84.86, 89.85, 94.84, 99.84, 104.83, 109.82, 114.82, 119.81, 124.80, 129.80, 134.79, 139.79, 144.78, 149.78, 154.77, 159.77, 164.76, 169.76, 174.75, 179.75, 184.75, 189.74, 194.74, 199.74, 204.74, 209.73, 214.73, 219.73, 224.73, 229.73, 234.73, 239.73, 244.73, 249.71, 254.51, 258.98, 262.98, 266.35, 268.94, 270.59, 271.24, 270.94, 269.74, 267.67, 264.75, 261.10, 256.86, 252.20, 247.29, 242.30, 237.30, 232.31, 227.31, 222.32, 217.32, 212.33, 207.33, 202.34, 197.34, 192.35, 187.36, 182.36, 177.37, 172.37, 167.38, 162.38, 157.39, 152.39, 147.40, 142.41, 137.41, 132.42, 127.42, 122.43, 117.43, 112.44, 107.44, 102.45, 97.45, 92.46, 87.47, 82.47, 77.48, 72.48, 67.49, 62.49, 57.50, 52.50, 47.51, 42.52, 37.52, 32.53, 27.53, 22.54, 17.54, 12.55, 7.55, 2.56]
        #z = [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]

        x = [0, -8.25E-08, -1.62E-07, -2.36E-07, -3.01E-07, -3.54E-07, -3.93E-07, -4.15E-07, -4.16E-07, -3.94E-07, -3.46E-07, -2.68E-07, -1.59E-07, -1.52E-08, 1.58E-07, 3.06E-07, 3.6E-07, 2.5E-07, -8.46E-08, 4.31E-07, -4.74E-07, 1.73E-05, -4.06E-05, -0.000141052, -2.91E-05, 0.00037281, 0.000145067, -0.001545286, -0.003065266, -0.001866897, 0.003656004, 0.000442723, -0.012758662, 0.047198965, 0.039393828, -0.243162494, -0.064895641, 1.550001308, 4.642347866, 8.95942679, 14.24841873, 20.25650432, 26.73086422, 33.41867906, 40.0740398, 46.50843519, 52.56178231, 58.0742016, 62.88581348, 66.8367384, 69.76709678, 71.52131528, 72.11035977, 71.76103754, 70.71453083, 69.21202189, 67.49237525, 65.64834268, 63.54205135, 61.01529671, 57.92023091, 54.23231158, 50.00795143, 45.32437954, 40.38826359, 35.45882906, 30.71444457, 26.15573036, 21.75984392, 17.51067089, 13.40200202, 9.425662877, 5.558533157, 1.772454931, -1.960733585, -5.669194173, -9.381088615, -13.11571685, -16.81960417, -20.40357429, -23.77820477, -26.85712797, -29.86742371, -33.6168378, -38.7605022, -44.42218651, -49.0627644, -51.14045385]
        y = [0, 4.890282662, 9.780491287, 14.67055184, 19.56039027, 24.44993256, 29.33910466, 34.22783253, 39.11604215, 44.00365946, 48.89061043, 53.77682103, 58.66221722, 63.54672495, 68.43049925, 73.31490592, 78.20170944, 83.0926745, 87.98939297, 92.86443815, 97.77567017, 101.6977795, 104.2828216, 106.0091261, 107.6267555, 109.7379047, 112.0839294, 114.2237016, 116.3011307, 118.6772485, 121.6800381, 125.1180615, 128.6358219, 132.8784999, 137.937708, 143.2211802, 147.8588205, 151.027431, 152.7296155, 153.226844, 152.7806769, 151.6526743, 150.1043963, 148.3974031, 146.784001, 145.439631, 144.5016645, 144.1072, 144.3933364, 145.4971726, 147.5558072, 150.7014026, 154.8752072, 159.7710374, 165.0662309, 170.4381251, 175.5663309, 180.2737653, 184.6095404, 188.6427094, 192.4219591, 195.7534929, 198.2843146, 199.7099302, 200.0679595, 199.536006, 198.2884295, 196.4915516, 194.3098901, 191.8693163, 189.2388071, 186.47487, 183.5911612, 180.5868931, 177.4612671, 174.2134847, 170.8427472, 167.3559832, 163.8235764, 160.3470399, 157.0281019, 153.9652877, 150.9285089, 147.0789152, 141.7375637, 135.8303234, 130.9777543, 128.8031995]
        z = [0, -0.006593029, -0.012953928, -0.018850565, -0.02405081, -0.028322532, -0.031433602, -0.033151887, -0.033245257, -0.031481582, -0.027628731, -0.021454574, -0.012726979, -0.001213816, 0.012598924, 0.024428945, 0.028744124, 0.020011574, -0.006759738, 0.034421491, -0.037854317, 2.635510151, 7.203470151, 11.80541432, 16.28476512, 20.62243214, 24.96116596, 29.44685389, 33.9284911, 38.1449064, 41.86958625, 45.41771302, 48.99671647, 50.67115009, 50.41972617, 49.99466288, 49.83067058, 49.76873326, 49.75925808, 49.78786095, 49.84017003, 49.90181347, 49.95841944, 49.99561609, 50.0007252, 49.97513582, 49.92720437, 49.86533708, 49.79794021, 49.73341999, 49.68018266, 49.64651233, 49.63596897, 49.64598998, 49.67360495, 49.71584351, 49.7697376, 49.83246732, 49.90144654, 49.97410973, 50.04780102, 50.11878856, 50.18263413, 50.23534142, 50.27594468, 50.30472144, 50.32256456, 50.33170877, 50.33455572, 50.33291995, 50.3277517, 50.3198487, 50.30955771, 50.29707348, 50.28259067, 50.26630389, 50.2484078, 50.22913537, 50.2090345, 50.18880756, 50.16915799, 50.1507688, 50.1322277, 50.10824078, 50.07453323, 50.0370594, 50.00620163, 49.99236]

        unitvector = self.calculate_unit_vector(x, y)

        theta = []
        for i in range(len(x)-1):
            angle = self.calculate_angle(*unitvector[i])
            angle = round(angle-90, 2)
            theta.append(angle)

        _, current_position = self.arm.get_position()

        xoffset = current_position[0]
        yoffset = current_position[1]
        zoffset = current_position[2]

        self.arm.set_position(x[0]+xoffset, y[0]+yoffset, z[0]+zoffset, yaw=0, speed=50, is_radian=False, wait=True)
        self.collectSingleVNAdata()

        for i in range(len(x)-1):
            self.arm.set_position(x[i+1]+xoffset, y[i+1]+yoffset, z[i+1]+zoffset, yaw=theta[i], speed=30, is_radian=False, wait=True)
            time.sleep(0.1)
            self.collectSingleVNAdata()

        _, current_position = self.arm.get_position()

        xcurrent = current_position[0]
        ycurrent = current_position[1]
        zcurrent = current_position[2]

        for i in range(0):
            self.arm.set_position(xcurrent, ycurrent+i*5, zcurrent, yaw=0, speed=30, is_radian=False, wait=True)
            time.sleep(0.1)
            self.collectSingleVNAdata()

        self.plot()

    def calculate_unit_vector(self, x, y):
        unit_vectors = []
        
        for i in range(len(x) - 1):
            x1, y1 = x[i], y[i]
            x2, y2 = x[i+1], y[i+1]
            
            # Calculate the differences in x and y coordinates
            dx = x2 - x1
            dy = y2 - y1
            
            # Calculate the magnitude of the vector
            magnitude = math.sqrt(dx**2 + dy**2)
            
            # Calculate the unit vector
            if magnitude != 0:  # Avoid division by zero
                unit_vector = (dx / magnitude, dy / magnitude)
            else:
                unit_vector = (0, 0)  # If the points are the same, set the unit vector as (0, 0)
            
            unit_vectors.append(unit_vector)
        
        return unit_vectors

    def calculate_angle(self, x, y):
        angle = math.atan2(y, x)
        return math.degrees(angle)

    #need a new thread?
    def recordPath(self):
        self.torqueOff()
        time.sleep(1)
        self.is_recording = True
        
        while self.is_recording:
            _, current_position = self.arm.get_position()
            self.points_set.append(current_position)
            time.sleep(0.1)

    def stop_record(self):
        self.is_recording = False
        self.torqueOn
    
    def select_record_points(self):
        step = 5
        position_list = [self.points_set[0]]
        for i in range(1, len(self.points_set)):
            distance = math.dist(position_list[0][0:3], self.points_set[i][0:3])
            if distance < step:
                continue

            position_list.append(self.points_set[i][0:3])
        
        return position_list

    def playbackPath(self):
        points_list =self.select_record_points()
        points_list.reverse
        for path in points_list:
            ret = self.arm.set_position(*path[:3], speed=200, wait=True)
            time.sleep(1)
            self.collectSingleVNAdata
    
    def getcurrentpoint(self):
        _, point = self.arm.get_position()
        self.appendpoint(point[0:3])
        point = [round(item, 3) for item in point ]
        self.listWidgetPoint.addItem(str(point))
        return point

    def torqueOn(self):
        self.arm.set_mode(0)
        self.arm.set_state(0)

    def torqueOff(self):
        self.arm.set_mode(2)
        self.arm.set_state(0)

    def appendpoint(self, point):
        self.points_set.append(point)

    def onplanthreadfinished(self):
        self.plot()
        #clean up
        #self.cleanup()
        self.x_plotMag64 = []
        self.x_plotPhase64 = []
        self.x_plotMag128 = []
        self.x_plotPhase128 = []
        self.points_set.reverse()

    def plannMoveThread(self):
        self.worker_thread = WorkerThread(self.plannMove, args=(), kwargs={})
        self.worker_thread.finished.connect(self.onplanthreadfinished)

        # Start the worker thread
        self.worker_thread.start()

    def plannMove(self):
        self.torqueOn()

        self.points_set.reverse()
        wp_number, unit_vector_list, angle_list = self.calDistance()

        waittime = 5
        for i in range(waittime):
            print(waittime-i)
            time.sleep(1)
        print('start')

        points_list = self.points_set
        self.arm.set_position(*points_list[0][0:3], speed=40, wait=True)
        
        self.collectSingleVNAdata()
        for i in range(len(points_list)-1):
            for j in range(wp_number[i]-1):
                position = points_list[i][0:3] + (j+1)*unit_vector_list[i]
                #self.safetyCheck(position)
                self.arm.set_position(*position, roll=-math.pi, pitch=0, yaw=-angle_list[i], is_radian=True, wait=True)
                time.sleep(0.1)
                print(j)
                self.collectSingleVNAdata()
                #self.plot()
        print(self.arm.get_position())
        #self.plot()
        #clean up
        #self.cleanup()
        #self.x_plotMag64 = []
        #self.x_plotPhase64 = []
        #self.x_plotMag128 = []
        #self.x_plotPhase128 = []
        #self.points_set.reverse()

    def calDistance(self):
        points_list = self.points_set
        distance_set = []
        unit_vector_list = []
        wp_number = []
        angle_list = []
        step = 5
        for i in range(len(points_list)-1):
            distance = math.dist(points_list[i][0:3], points_list[i+1][0:3])
            distance_set.append(distance)
            waypoints = round(distance/step)
            wp_number.append(waypoints)
            direction_vector = np.subtract(points_list[i+1][0:3], points_list[i][0:3])
            unit_vector = direction_vector/waypoints
            rad_angle = math.atan(unit_vector[0]/unit_vector[1])
            angle_list.append(rad_angle)
            unit_vector_list.append(unit_vector)
        
        return wp_number, unit_vector_list, angle_list

    def cleanup(self):
        #self.points_set = []
        self.VNAdata_list = []
        #self.x_plotMag64 = []
        #self.x_plotPhase64 = []
        #self.x_plotMag128 = []
        #self.x_plotPhase128 = []
    
    def safetyCheck(self, position):
        pass

    def emergencyStop(self):
        self.arm.emergency_stop()

    def cleandata(self):
        self.points_set = []
        self.VNAdata_list = []
        self.x_plotMag64 = []
        self.x_plotPhase64 = []
        self.x_plotMag128 = []
        self.x_plotPhase128 = []
        self.listWidgetPoint.clear()
        self.plotMag64.detachItems()
        self.plotMag64.replot()
        self.plotPhase64.detachItems()
        self.plotPhase64.replot()
        self.plotMag128.detachItems()
        self.plotMag128.replot()
        self.plotPhase128.detachItems()
        self.plotPhase128.replot()
    
    def plot(self):
        x = np.arange(0, len(self.VNAdata_list), 1)
        qwt.QwtPlotCurve.make(x, self.x_plotMag64, "Mag64", self.plotMag64, linecolor="blue", antialiased=True)
        self.plotMag64.show()
        self.plotMag64.replot()

        qwt.QwtPlotCurve.make(x, self.x_plotPhase64, "Phase64", self.plotPhase64, linecolor="blue", antialiased=True)
        self.plotPhase64.show()
        self.plotPhase64.replot()

        qwt.QwtPlotCurve.make(x, self.x_plotMag128, "Mag128", self.plotMag128, linecolor="blue", antialiased=True)
        self.plotMag128.show()
        self.plotMag128.replot()

        qwt.QwtPlotCurve.make(x, self.x_plotPhase128, "Phase128", self.plotPhase128, linecolor="blue", antialiased=True)
        self.plotPhase128.show()
        self.plotPhase128.replot()

    #10mm
    def manualMeasure(self):
        time.sleep(1)
        print('startnow')
        self.arm.set_position(x=326, y=-386, z=-5, yaw=0, speed=70, is_radian=True, wait=True)
        time.sleep(0.1)
        self.collectSingleVNAdata()
        print(self.arm.position)

        y = -386
        #range = /5 = 
        for i in range(53):
            y = y+5
            self.arm.set_position(y=y, speed=70, wait=True)
            time.sleep(0.1)
            self.collectSingleVNAdata()
        print(self.arm.position)
        #300, -20

        yaw_startpos = 0

        theta_rad = 5/10
        radius = 10
        x_offset = 326
        y_offset = -106

        self.arm.set_position(yaw=-math.pi/2, speed=70, is_radian=True, wait=True)
        self.collectSingleVNAdata()
        time.sleep(1)
        for i in range(5):
            x = x_offset + 5*i
            self.arm.set_position(x=x, speed=70, is_radian=True, wait=True)
            time.sleep(0.1)
            self.collectSingleVNAdata()
        print(self.arm.position)

        self.arm.set_position(yaw=-math.pi, speed=70, is_radian=True, wait=True)
        time.sleep(1)

        #self.arm.set_position(x=336, yaw=-180, speed=50, is_radian=False, wait=True)
        time.sleep(0.1)
        self.collectSingleVNAdata()
        print(self.arm.position)
        
        _, point = self.arm.get_position()
        y = point[1]
        for i in range(51):
            y = y-5
            self.arm.set_position(y=y, speed=50, wait=True)
            time.sleep(0.1)
            self.collectSingleVNAdata()
        print(self.arm.position)
        
        self.plot()



class WorkerThread(QThread):
    """Background worker thread."""
    finished = pyqtSignal()  # Custom signal to indicate when the thread has finished
    
    def __init__(self, func, args, kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        """Run the function in the background."""
        self.func(*self.args, **self.kwargs)
        self.finished.emit()  # Emit the 'finished' signal when the function has completed


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mWin = MainWindow()
    mWin.show()
    sys.exit(app.exec())
