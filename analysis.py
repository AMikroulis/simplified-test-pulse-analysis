from ast import arguments
import datetime
import numpy as npy
import scipy as scy
from scipy import signal as ssy
import matplotlib as mpl
from matplotlib import pyplot as plt
import os
import sys
from datetime import date
import pyabf as abf
import threading
import thingies.io
import thingies.tp

from thingies.mainwindow import Ui_MainWindow
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QListWidget, QDoubleSpinBox

import thingies.protocols as prot_module

mpl.use('agg')

class mwin(qtw.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mwinui = Ui_MainWindow()
        self.mwinui.setupUi(self)

        self.mwinui.startbutton.setDisabled(False)
        self.mwinui.HEKAfmt.setDisabled(False)
        self.mwinui.ABFfmt.setDisabled(False)
        
        self.mwinui.iclamptp.setDisabled(True)
        self.mwinui.io_switch.setDisabled(False)
        self.mwinui.tab_3.setDisabled(False)
        self.mwinui.tab_4.setDisabled(True)
        
        self.template_file = ''
        self.template_file_2 = ''

        self.mwinui.startbutton.clicked.connect(self.cleared)
        self.mwinui.scanfolder.clicked.connect(self.scan_folder)
        

    def update1(self,updatetext):
        self.mwinui.textInfo1.setText(updatetext)
        

    def update2(self,updatetext):
        self.mwinui.textInfo2.setText(updatetext)
        
    def get_tp_check(self):
        det_check = self.mwinui.tp_switch.isChecked()
        return det_check
    
    def get_io_check(self):
        det_check = self.mwinui.io_switch.isChecked()
        return det_check
        
    def getformat(self):
        if self.mwinui.HEKAfmt.isChecked():
            formatselection = 'HEKA' 
        if self.mwinui.ABFfmt.isChecked():
            formatselection = 'ABF'
        return(formatselection)
                        

    def scan_folder(self):
        protocol_names = []
        channel_names = []
        selected_format = 'HEKA'
        file_filter = '.inf'
        selected_format = str(self.getformat())
        if selected_format == 'HEKA':
            file_filter = '.inf'
        if selected_format == 'ABF':
            file_filter = '.abf'
        askfiledlg = qtw.QFileDialog()
        askfiledlg.directory()
        askfolder = askfiledlg.getExistingDirectory()
        expfiles = []
        currentexpfile = 0
        for file in os.scandir(str(askfolder)):
            if (str(file.path)[-4:]) == file_filter :
                ch = []
                protocol = []
                try:
                    expfiles.append(str(file.path))
                    currentexpfile += 1
                    if selected_format == 'HEKA':
                        inffy = open(file, 'r', newline='\n')
                        allfile = inffy.readlines()
                        inffy.close()
                        numlines = npy.size(allfile) - 1
                        
                        ch=[]
                        protocol=[]
                        
                        for i in range(int(npy.size(allfile)/17)-1):
                            temp1,junkstr=allfile[17*i + 4].split(';')
                            ch.append(temp1.strip())
                            temp2,junkstr=allfile[17*i + 5].split(';')
                            protocol.append(temp2.strip())

                    if selected_format == 'ABF':
                        allfile = abf.ABF(file.path)
                        
                        ch=[]
                        protocol=[]

                        protocol.append(allfile.protocol.strip())
                        
                        for temp_ch in allfile.adcNames:
                            ch.append(temp_ch.strip())
                                                
                except:
                    continue
                
                for channel in ch:
                    if not (channel in channel_names):
                        channel_names.append(channel)

                for prot in protocol:
                    if not (prot in protocol_names):
                        protocol_names.append(prot)

        self.mwinui.prot_list_2.addItems(protocol_names)
        self.mwinui.ch_list_2.addItems(channel_names)
        self.mwinui.prot_list_3.addItems(protocol_names)
        self.mwinui.ch_list_3.addItems(channel_names)
        

    def selectprots(self,caller):
        selected_p = []
        if caller == 'tp':
            selected_pi = self.mwinui.prot_list_2.selectedItems()
        if caller == 'io':
            selected_pi = self.mwinui.prot_list_3.selectedItems()
        for i in selected_pi:
            selected_p.append(i.text())
        return(selected_p)
    
    def selectch(self,caller):
        selected_c = []
        if caller == 'tp':
            selected_ci = self.mwinui.ch_list_2.selectedItems()
        if caller == 'io':
            selected_ci = self.mwinui.ch_list_3.selectedItems()
        for i in selected_ci:
            selected_c.append(i.text())
        return(selected_c)

    def get_start_of_testpulse(self):
        start_of_tp = self.mwinui.stepstartbox.value()
        return(start_of_tp)
    
    def get_end_of_testpulse(self):
        end_of_tp = self.mwinui.stependbox.value()
        return(end_of_tp)
    
    def get_start_of_io(self):
        start_of_io = self.mwinui.stepstartbox_2.value()
        return(start_of_io)
    
    def get_end_of_io(self):
        end_of_io = self.mwinui.stependbox_2.value()
        return(end_of_io)

    def notch(self):
        selected_freqs = [False, False, False, False, False]
        notch_freq = self.mwinui.doubleSpinBox.value()

        if self.mwinui.checkBox.isChecked():
            selected_freqs[0] = True
        if self.mwinui.checkBox_2.isChecked():
            selected_freqs[1] = True
        if self.mwinui.checkBox_3.isChecked():
            selected_freqs[2] = True
        if self.mwinui.checkBox_4.isChecked():
            selected_freqs[3] = True
        if self.mwinui.checkBox_6.isChecked():
            selected_freqs[4] = True
        
        return(notch_freq, selected_freqs)
        


    def get_naming_setting(self):
        if self.mwinui.default_naming.isChecked():
            naming_setting = ''
        if self.mwinui.custom_naming.isChecked():
            naming_setting = self.mwinui.folder_identifier.text()
        return naming_setting

    def get_timestamp_setting(self):
        if self.mwinui.add_timestamp.isChecked():
            timestampstring = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        else:
            timestampstring = ''
        return timestampstring

    def get_log_setting(self):
        if self.mwinui.Log_active.isChecked():
            log_flag = True
            user_comment = self.mwinui.log_comment.toPlainText()
        else:
            log_flag = False
            user_comment = ''
        return log_flag, user_comment

    def cleared(self):
        self.mwinui.scanfolder.setDisabled(True)
        self.mwinui.HEKAfmt.setDisabled(True)
        self.mwinui.ABFfmt.setDisabled(True)
        self.mwinui.tab_2.setDisabled(True)
        self.mwinui.tab_3.setDisabled(True)
        self.mwinui.groupBox_2.setDisabled(True)
        self.mwinui.groupBox_3.setDisabled(True)
        self.mwinui.tab_4.setDisabled(True)
        
        askfiledlg = qtw.QFileDialog()
        askfiledlg.directory()
        askfolder = askfiledlg.getExistingDirectory()
        self.mwinui.startbutton.setDisabled(True)
        self.mwinui.startbutton.setText('running')

        self.analysisthread = analysisloop()
        #self.analysisthread.__init__()
        self.analysisthread.setup(askfolder)
        self.analysisthread.start()
   


class analysisloop(QThread):
    
    def __init__(self, *args, **kwargs):
            
        super(analysisloop, self).__init__(*args, **kwargs)
        
        self.recfolder = str()
        self.fir = npy.array([])
        self.fir2 = npy.array([])
        
        self.sampling_rate = float()
        self.protocol_list = []
        self.ch_list = []
        self.template_selection = str()
        self.template_sampling_rate = float()
        self.fmtselection = str()
        self.prots_instance = object()

  

    def setup(self,askfolder):
        

        self.fir = ssy.remez(2799,[0,400,420,5000],[1,0],[1,10],10000,'bandpass',2048,256)
        self.fir = npy.convolve(self.fir,self.fir,'full')
        
        self.fir2 = ssy.remez(2799,[0,2200,2213,5000],[1,0],[1,10],10000,'bandpass',2048,256)
        self.fir2 = npy.convolve(self.fir2,self.fir2,'full')
        #presets:
        self.sampling_rate = 10000.0
        self.fmtselection = 'HEKA'
        
        try:
            self.fmtselection = str(mwi.getformat())
        except:
            self.protocol_list = []
            self.ch_list = []
            self.fmtselection = 'HEKA'
        print(self.protocol_list)
        print(self.ch_list)
        self.recfolder = askfolder
    
        
    def run(self):
        
        selected_modules = []
        if mwi.get_tp_check() == True:
            selected_modules.append('tp')
        if mwi.get_io_check() == True:
            selected_modules.append('io')
        print('selected modules: ' + str(selected_modules))
        current_module = str()

        logcheck, logcomment = mwi.get_log_setting()

        if logcheck == True:
            logfile = open(self.recfolder+ '/log.txt', 'a')
            logfile.write('# '+ datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+ '\r')
            logfile.write('analysis folder: ' + str(self.recfolder) + '\r')
            logfile.write('selected analyses: ' + str(selected_modules)+ '\r')
            logfile.write('/ user comment / : '+ str(logcomment) +'\r/end user comment/\r')
            logfile.write('format: '+ self.fmtselection +'\r')
            logfile.write('custom output name: '+ mwi.get_naming_setting() + '\t' + mwi.get_timestamp_setting() +'\r')
            

        for current_module in selected_modules:
            print('currently in ' + str(current_module))
            self.protocol_list = mwi.selectprots(caller=current_module)
            self.ch_list = mwi.selectch(caller=current_module)
            print('protocols for '+ str(current_module) + ' : '+ str(self.protocol_list))
            if current_module == 'tp':
                #logging
                if logcheck == True:
                    logfile.write('*tp settings\r')
                    protocol_list_2 = mwi.selectprots(caller='tp')
                    ch_list_2 = mwi.selectch(caller='tp')
                    logfile.write('protocols: '+ str(protocol_list_2) +'\r')
                    logfile.write('channels: '+ str(ch_list_2) +'\r')
                    logfile.write(' >- processing start - '+ datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +'\r')
                    
                #call
                thingies.tp.main(recfolder=self.recfolder, prot_list=self.protocol_list,ch_list=self.ch_list,fir=self.fir,fir2=self.fir2,fmtselection=self.fmtselection,window_reference=mwi)
                 
                if logcheck == True:
                    logfile.write(' <- processing end - '+ datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +'\r')


            if current_module == 'io':
                #logging
                if logcheck == True:
                    logfile.write('*io settings\r')
                    protocol_list_3 = mwi.selectprots(caller='io')
                    ch_list_3 = mwi.selectch(caller='io')
                    logfile.write('protocols: '+ str(protocol_list_3) +'\r')
                    logfile.write('channels: '+ str(ch_list_3) +'\r')
                    logfile.write(' >- processing start - '+ datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +'\r')
                    
                #call
                thingies.io.main(recfolder=self.recfolder, prot_list=self.protocol_list,ch_list=self.ch_list,fir=self.fir,fir2=self.fir2,fmtselection=self.fmtselection,window_reference=mwi)
                 
                if logcheck == True:
                    logfile.write(' <- processing end - '+ datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +'\r')


        if logcheck == True:
            logfile.write('[session end]\r\r')
            logfile.close()      




if __name__ == "__main__":
    app = qtw.QApplication([])
    mwi = mwin()
    mwi.show()
    app.exec_()
