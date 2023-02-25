import numpy as npy
import os
import pyabf as abf
from PyQt5 import QtWidgets as qtw

class prots():
    def __init__(self):
        
        self.target_folder_path = str()
        self.targetfile = str()
        self.reportfile = object()
        self.logfile = object()
        self.mwi = object()
        self.protocol_list = []
        self.ch_list = []



    def  get_prots(self, inffile, reporthtml, mwi):
        infofile = open(inffile, 'r', newline='\n')
        # read it as text
        allfile = infofile.readlines()

        infofile.close()

        numlines = npy.size(allfile) - 1
        # initialize field lists
        traceid=[]
        ch=[]
        protocol=[]
        timeres=[]
        scalef=[]
        units=[]
        tstamp=[]
        vhold=[]
        nsamples=[]
        offset=[]
        chunksize=[]

        # parse text for field values
        for i in range(int(npy.size(allfile)/17)-1):
            # trace ID
            traceid.append(allfile[17*i + 3])
            # channel
            temp1,junkstr=allfile[17*i + 4].split(';')
            ch.append(temp1.strip())
            # protocol name
            temp2,junkstr=allfile[17*i + 5].split(';')
            protocol.append(temp2.strip())
            # sampling interval
            temp3,junkstr=allfile[17*i + 6].split(';')
            timeres.append(float(temp3.strip()))
            # scaling factor (y-axis)
            temp4,junkstr=allfile[17*i + 7].split(';')
            scalef.append(float(temp4.strip()))
            # units (y-axis)
            temp5,junkstr=allfile[17*i + 8].split(';')
            units.append(temp5.strip())
            # trace time stamp
            temp6,junkstr=allfile[17*i + 9].split(';')
            tstamp.append(float(temp6.strip()))
            # holding potential
            temp7,junkstr=allfile[17*i + 10].split(';')
            vhold.append(float(temp7.strip()))
            # number of samples in the trace
            temp8,junkstr=allfile[17*i + 11].split(';')
            nsamples.append(int(temp8.strip()))
            # trace offset in the file
            temp9,junkstr=allfile[17*i + 12].split(';')
            offset.append(int(temp9.strip()))
            # chunk size for gap-free recordings --- this is important and most applications miss it.
            temp0,junkstr=allfile[17*i + 15].split(';')
            chunksize.append(int(temp0.strip()))
        
        # initialise number of trace samples in the entire file to 0
        totalsamples = 0
        # special case for gap-free modes, to handle HEKA signature chunk glitch (chunk-size = 0) --- this is IMPORTANT!
        for i in range(int(npy.size(allfile)/17)-1):
            totalsamples = totalsamples + nsamples[i]
            if protocol[i] == protocol[i-1]:
                if chunksize[i] == 0:
                    if ch[i-1] != ch[i]:
                        if chunksize[i-1]>0:
                            chunksize[i] = chunksize[i-1]
            

        # readying an array for the entire file data
        try:
            dataseg = npy.zeros((int(totalsamples),2),'int16')
        except:
            if len(ch) == 1:
                dataseg = npy.zeros(int(totalsamples),'int16')
            if len(ch) >= 2:
                dataseg = npy.zeros((int(totalsamples),len(ch)),'int16')

        if self.ch_list == []:
           self.ch_list = ['Imon','CurrentIn','Imon-1']
        ### read the rec data
        def rawthingy():

                    # get or infer dat file
            datfile = inffile[:-3] + 'dat'
            datfy = open(datfile, 'rb')
            rawdata = npy.fromfile(datfy, 'int16') # read it to 16-bit array
            datfy.close()
            print(npy.size(rawdata))


            # getting number of continuous recording segments
            startpoint = 0
            savedstartpoint = 0
            segments = int(npy.size(allfile)/17)-1
            # loop through them
            for j in range(segments) :
                offset[j] = int(offset[j] / 2)

                if j>0:
                    if tstamp[j]==tstamp[j-1]:      # determine if they're the same recording (i.e. 2nd channel)
                        startpoint = savedstartpoint
                    else:
                        savedstartpoint = startpoint

                if (chunksize[j]==0) :          # handle the fragmentation and write to the array
                    if ch[j] in self.ch_list :
                        try:
                            dataseg[startpoint:startpoint+nsamples[j],0] = rawdata[offset[j]:offset[j]+nsamples[j]]
                        except:
                            dataseg[startpoint:startpoint+nsamples[j]] = rawdata[offset[j]:offset[j]+nsamples[j]]
                    else :
                        dataseg[startpoint:startpoint+nsamples[j],1] = rawdata[offset[j]:offset[j]+nsamples[j]]
                    startpoint = startpoint + nsamples[j]

                else :
                    nchunks = int(npy.ceil(2 * nsamples[j] / chunksize[j]))
                    lastchunk = nsamples[j] - (nchunks-1) * int(chunksize[j] / 2)
                    if lastchunk <= 0 :
                        lastchunk= nsamples[j]

                    for k in range(int(nchunks)) :
                        if k == nchunks -1 :
                    
                            if ch[j] in self.ch_list:
                                try:
                                    dataseg[startpoint : startpoint + lastchunk, 0] = rawdata[offset[j] + k * chunksize[j] : offset[j] + k * chunksize[j] + lastchunk]
                                except:
                                    dataseg[startpoint : startpoint + lastchunk] = rawdata[offset[j] + k * chunksize[j] : offset[j] + k * chunksize[j] + lastchunk]
                            else:
                                dataseg[startpoint : startpoint + lastchunk, 1] = rawdata[offset[j] + k * chunksize[j] : offset[j] + k * chunksize[j] + lastchunk]
                            startpoint = startpoint + lastchunk
                
                        else :
                            if ch[j] in self.ch_list:
                                try:
                                    dataseg[startpoint:startpoint+int(chunksize[j]/2),0] = rawdata[offset[j]+k*chunksize[j]:offset[j]+k*chunksize[j]+int(chunksize[j]/2)]
                                except:
                                    dataseg[startpoint:startpoint+int(chunksize[j]/2)] = rawdata[offset[j]+k*chunksize[j]:offset[j]+k*chunksize[j]+int(chunksize[j]/2)]
                            else:
                                dataseg[startpoint:startpoint+int(chunksize[j]/2),1] = rawdata[offset[j]+k*chunksize[j]:offset[j]+k*chunksize[j]+int(chunksize[j]/2)]

                            startpoint = startpoint + int(chunksize[j]/2)
            

            # ignore this, unless you need it for debugging
        # writefilename = datfile.rstrip('.dat') + '_IV.dat'
            # interleave channels
            return startpoint

        

        ### end read
        startpoint = rawthingy()
        try:
            onlyI= dataseg[0:startpoint,0]
            onlyV= dataseg[0:startpoint,1]
        except:
            onlyI= dataseg[0:startpoint]
            pass

        # getting number of continuous recording segments
        startpoint = 0
        savedstartpoint = 0
        segments = int(npy.size(allfile)/17)-1
        # prepare trace arranging
        uniquesegs = [0]
        i=[]
        j=[]
        k=[]

        i=0
        j=0
        k=0
        # get the protocol name field for each trace
        for i in range(1,segments):
            if tstamp[i] != tstamp[i-1]:
                uniquesegs.append(i)

        prots = [0]
        protslen = [nsamples[0]]
        protscale = [scalef[0]]
        protres = [timeres[0]]
        sweeplen = [nsamples[0]]
        m=0

        for j in uniquesegs:

            if j>0:
                if protocol[j] != protocol[m]:
                    prots.append(j)
                    protslen.append(nsamples[j])
                    protres.append(timeres[j])
                    sweeplen.append(nsamples[j])
                    if ch[j] in self.ch_list:
                        protscale.append(scalef[j])
                    else:
                        protscale.append(3.125e-4)
                    m = j
                else:
                    protslen[-1] = protslen[-1] + nsamples[j]
        

        startpoint = 0
        n=0
        # save each protocol name with the interlreaved data to a separate dat file
        #tempfilenm = datfile.rstrip('.dat')+'_'+ str(n) +'_'+ protocol[k] + '.dat'
        #tempwrite = open(tempfilenm, 'wb')
        
        # preselecting the correct protocol names
        preselect = []
        preselectindex = 0

        # protocol start points:
        startpoints = []

        # protocol raw data (might have to move or tag as global
        protDataV = []
        protDataI = []


        for k in prots:
            
            h = int(tstamp[k]/3600)
            minutes = int((tstamp[k] - 3600 *h) /60)
            
            #relative timestamp for easier clustering
            relminutes = h * 60  + minutes - ((int(tstamp[0]/3600)) * 60  + (int((tstamp[0] - 3600 * int(tstamp[0]/3600)) /60)))
            startpoints.append(startpoint)


            print('t : ' + str(relminutes) + '  --  ' + str(n) + ' : ' + protocol[k])
            reporthtml.write('<p>' + ('t : ' + str(relminutes) + '  --  ' + str(n) + ' : ' + protocol[k]) + '</p>')
            
            try:
                protrawV = onlyV[startpoint:startpoint+protslen[n]]
                protDataV.append(protrawV)
            except:
                protDataV = None

            protrawI = onlyI[startpoint:startpoint+protslen[n]]
            
            
            protDataI.append(protrawI)

            if self.protocol_list == []:
                if protocol[k][:7] == 'Cont.VC' :
                    preselect.append((k,n,preselectindex))
                    preselectindex += 1
            else:
                if protocol[k] in self.protocol_list :
                    #print(protocol[k])
                    preselect.append((k,n,preselectindex))
                    preselectindex += 1
            #protdata.astype('int16').tofile(tempwrite)
        
            startpoint = startpoint + protslen[n]
            n=n+1


        print('\r\n')
        print(len(preselect))
        saveprots = []
        saveprotname = []
        saveprotdata = []
        
        
        successful = True
        return (successful, preselect, protDataI, protDataV, tstamp, protocol, protscale, protres, protslen, sweeplen)


    def get_abf_prots(self, inffile, reporthtml, mwi):
        successful = False
        abffile = abf.ABF(inffile)
        data_segment = abffile.data
        data_segment_2 = None
        abf_scale = 1.
        abf_sampling_rate = abffile.dataRate
        abf_time_res = 1. / abf_sampling_rate
        abf_protocol = abffile.protocol
        selected_channel = -999
        abf_sweeplen = int()
        if abf_protocol in self.protocol_list:
            print(abf_protocol)
            for abf_channel in abffile.adcNames:
                if abf_channel in self.ch_list:
                    selected_channel = abffile.channelList[abffile.adcNames.index(abf_channel)]
                    abf_scale_unit_prefix = abffile.adcUnits[selected_channel][0]
                    abf_sweeplen = abffile.sweepPointCount
                    if abf_scale_unit_prefix == 'm':
                        abf_scale = 1.e-3
                    if abf_scale_unit_prefix == 'u':
                        abf_scale = 1.e-6
                    if abf_scale_unit_prefix == 'n':
                        abf_scale = 1.e-9
                    if abf_scale_unit_prefix == 'p':
                        abf_scale = 1.e-12
                    successful = True

        
        if selected_channel>=0:
            data_segment = abffile.data[selected_channel]
            try:
                data_segment_2 = abffile.data[selected_channel - 1]
            except:
                data_segment_2 = None
        #print('abf sub, sweeplength = ' + str(abf_sweeplen))
        #print('raw length = ' + str(npy.size(data_segment)))
        return (successful, data_segment, data_segment_2, abf_scale, abf_time_res, abf_sweeplen)
        
        
    def main(self, targetfile, reportfile, logfile, fileformat, protlist, chlist, windowinstance):
        self.targetfile = targetfile
        self.reportfile = reportfile
        self.logfile = logfile
        self.protocol_list = protlist
        self.ch_list = chlist
        self.mwi = windowinstance

        prot_selections = None
        extracted_HEKA = None
        extracted_HEKA_V = None
        extracted_ABF = None
        extracted_ABF_V = None
        HEKA_tstamp = None
        HEKA_protocol = None
        extracted_scale = None
        extracted_resolution = None
        extracted_sweeplength = None

        if fileformat == 'HEKA':
            successful, prot_selections, extracted_HEKA, extracted_HEKA_V, HEKA_tstamp, HEKA_protocol, extracted_scale, extracted_resolution, extracted_sweeplength, extracted_tracelength = self.get_prots(inffile = self.targetfile, reporthtml = self.reportfile, mwi = self.mwi)
        if fileformat == 'ABF':
            successful, extracted_ABF, extracted_ABF_V, extracted_scale, extracted_resolution, extracted_sweeplength = self.get_abf_prots(inffile= self.targetfile, reporthtml= self.reportfile, mwi= self.mwi)
            extracted_tracelength = extracted_sweeplength
            print('protocol processing, trace length = ' + str(extracted_sweeplength))
            
        return (successful, prot_selections, extracted_HEKA, extracted_ABF, extracted_HEKA_V, extracted_ABF_V, HEKA_tstamp, HEKA_protocol, extracted_scale, extracted_resolution, extracted_sweeplength, extracted_tracelength)


if __name__ == "__main__":
    print('This is a module.')
    pass