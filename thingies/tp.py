import numpy as npy
import scipy as scy
from scipy import signal as ssy
from scipy.optimize import least_squares
from matplotlib import pyplot as plt
import os
import sys
from datetime import date
import thingies.protocols


pi = npy.pi

fir = npy.array([])
fir2 = npy.array([])
sampling_rate = float()
fmtselection = str()
recfolder = str()
reporthtml = object()


################################
# Test pulse protocol settings #
################################

fallback_start_of_testpulse = 100.0    # in ms
fallback_end_of_testpulse = 150.0      # in ms

fallback_holding = -70                 # in mV
fallback_step = -5                      # in mV


def openthesegment(segmentV, segmentI, segmentname, segmentrecnumber, outputfolder, segmentscale, segmenttimeres, segmentlength, tracelen, fir, fir2, reporthtml, fileformat):
    print('opening with prot len = ' + str(segmentlength) + ' and trace length = '+ str(tracelen))
    segmentnamebasedir = os.path.dirname(segmentname)
    segmentfilename = os.path.basename(segmentname)
    newsegmentname = os.path.join(segmentnamebasedir, outputfolder, segmentfilename)
    relsegmentname = './'+outputfolder+'/' + segmentfilename[:-4] + '_' + str(segmentrecnumber) + '_'
    segmentname = os.fsdecode(newsegmentname)[:-4] + '_' + str(segmentrecnumber) + '_'
    
    ### read rec
    reportedfs = npy.round(100./(segmenttimeres),0)/100.0
    
    try:
        scI = segmentI * segmentscale / 1e-12
    except:
        scI = segmentI * 3.1250000e-1
    
    t_axis_all = npy.arange(0, len(scI)*segmenttimeres, segmenttimeres)

    plt.clf()
    plt.plot(t_axis_all, scI)
    plt.xlabel('time (s)')
    plt.ylabel('current (pA)')
    #plt.show()
    plt.savefig(segmentname+'_I.png')

    print(segmentV)
    if not (segmentV is None):
        scV = segmentV
        plt.clf()
        plt.plot(t_axis_all, scV)
        plt.xlabel('time (s)')
        plt.ylabel('voltage command (mV)')
        plt.savefig(segmentname+'_V.png')
        #plt.show()
  
    fscI = npy.convolve(scI, fir, 'valid')
    # plt.clf()
    # plt.plot(fscI, color = '#402060')
    # plt.title('400Hz low-pass')
    # plt.xlabel('time (samples)')
    # plt.ylabel('current (pA)')
    # plt.savefig(segmentname+'_filtered.png')
    # #plt.show()
    
    int_fscI = npy.round(fscI/3.1250000e-1, 0).astype('int16')

    # abf pad crop:
    crop = 0
    if fileformat=='ABF':
        crop = int(npy.floor(tracelen/64))
    print("crop = " + str(crop))
    ### testpulse:
    
    scI_n = int(segmentlength/tracelen)
    scI_sweeps = npy.reshape(scI[0:tracelen*scI_n] , [scI_n,tracelen])
    scI_sweeps[:-crop] = scI_sweeps[crop:,:]
    print('traces dimensions : ' + str(npy.shape(scI_sweeps)))
    scI_avg = npy.mean(scI_sweeps[:][0:], axis = 0)
    scI_med = npy.median(scI_sweeps[:][0:], axis = 0)
    npy.save(segmentname + '_raw', scI_med)

    try:
        scV_sweeps = npy.reshape(scV[0:tracelen*scI_n] , [scI_n,tracelen])
        scV_sweeps[:-crop] = scV_sweeps[crop:,:]

        scV_med = npy.median(scV_sweeps[:][0:], axis = 0)
        npy.save(segmentname + '_rawV', scV_med)
    except:
        scV_med = None
    
    ## test pulse autodetect to the nearest ms:
    try:
        if len(scV_med) == len(scI_med):
            scV_min = npy.argmin(npy.diff(scV_med)) / reportedfs
            scV_max = npy.argmax(npy.diff(scV_med)) / reportedfs
            print('min = ' + str(scV_min))
            tp_min = scV_min*1000
            print('min #2 = ' + str(tp_min))
            tp_max = scV_max*1000
            Cq_offset = 4
            
        else:
            scI_min = npy.argmin(npy.diff(scI_med)) / reportedfs
            scI_max = npy.argmax(npy.diff(scI_med)) / reportedfs
            tp_min = npy.round(scI_min*1000, 0)
            tp_max = npy.round(scI_max*1000, 0)
            Cq_offset = 2
        tp_start = min(tp_min,tp_max)
        tp_end = max(tp_min, tp_max)
        start_of_testpulse = tp_start
        end_of_testpulse = tp_end
    except:
        print('failed to detect pulse - using defaults')
        start_of_testpulse = fallback_start_of_testpulse
        end_of_testpulse = fallback_end_of_testpulse
    
    if not(scV_med is None):
        holdingV = npy.median(scV_med[:int(start_of_testpulse *0.001* reportedfs)])
        stepV = npy.median(scV_med[int(start_of_testpulse *0.001* reportedfs):int(end_of_testpulse *0.001* reportedfs)]) - holdingV
    else:
        holdingV = fallback_holding
        stepV = fallback_step

    start_point_adjusted = int(npy.round(start_of_testpulse / (1000.* segmenttimeres),0))
    end_point_adjusted = int(npy.round(end_of_testpulse / (1000.* segmenttimeres),0))
    print('testpulse detection: '+ str(start_point_adjusted) + ' - ' + str(end_point_adjusted))
    fit_axis = npy.arange(2*segmenttimeres,segmenttimeres*(end_point_adjusted-start_point_adjusted), segmenttimeres)
    old_fit_axis = npy.arange(0.2,0.8 *(end_of_testpulse-start_of_testpulse)+0.2,0.1)

    
    Cq_med1 = scy.integrate.cumtrapz(scI_med[start_point_adjusted + Cq_offset:end_point_adjusted - 3 - Cq_offset] - npy.median(scI_med[end_point_adjusted - 10 - Cq_offset:end_point_adjusted - 1]))[-1] * segmenttimeres * 1000. / (-5.0)  # in pF
                                                                     

    def fitf(x, t_, observed):
        t_ = t_ - 0
        return (x[0] * npy.exp(-t_/x[1]) + x[2] + x[3]* npy.exp(-t_/x[4]) - observed)
    plt.clf()
    LS_res1 = least_squares(fitf, x0 =[-200,30,-200,-200,0.1], args = (segmenttimeres*npy.arange(2, 0.8*(end_point_adjusted-start_point_adjusted)+2), scI_med[start_point_adjusted + 2 : int(npy.round((start_of_testpulse + 0.8*(end_of_testpulse - start_of_testpulse)) /(1000.* segmenttimeres),0))+2]),  ftol = 1e-9, xtol = 1e-8, gtol=1e-8, max_nfev = 80000, jac = '3-point', method = 'trf', loss = 'soft_l1' , bounds=([-2000,0,-10000,-2000,0],[2000,500,10000,2000,0.2]))
    lsp = LS_res1.x

    tp_0 = lsp[0] * npy.exp(-0/lsp[1]) + lsp[2] + lsp[3]* npy.exp(-0/lsp[4])
    tp_b = npy.median(scI_med[start_point_adjusted -20: start_point_adjusted -1])
    tp_endlim = lsp[0] * npy.exp(-500 /lsp[1]) + lsp[2] + lsp[3]* npy.exp(-int(npy.round((end_of_testpulse - start_of_testpulse) /(1000.* segmenttimeres),0))/lsp[4])
    tp_tau1 = lsp[1]
    tp_tau2 = lsp[4]
    
    Vm = npy.round(( holdingV + tp_b*(stepV)/(tp_b-scI_med[end_point_adjusted - 5]) ),1) 
    Ri = npy.round((-0.001*stepV*1e+6/(tp_b-npy.median(scI_med[end_point_adjusted - 10:end_point_adjusted - 1])) ),1)
    

    reporthtml.write('<p> resting membrane potential estimate (linearity condition): ' + str(Vm) + 'mV </p>')
    reporthtml.write('<p> input resistance: ' + str(Ri) + 'MOhm </p>')
    reporthtml.write('<p> amplitude 1 : '+ str(npy.round(lsp[0],2))+ 'pA </p>')
    reporthtml.write('<p> amplitude 2 : '+ str(npy.round(lsp[3],2))+ 'pA </p>')
    reporthtml.write('<p> baseline : '+ str(npy.round(lsp[2],2))+ 'pA </p>')
    
    tp_ampl = tp_b - tp_0
    Rs = npy.abs(0.001*stepV * 1e+6 / tp_ampl)        #### 1e+6  = 1/1e-12 (the pA)  /1e6  (for MOhm)
    Cq_med = Cq_med1 *((Ri-Rs)/((Ri-Rs)-Rs))
    reporthtml.write('<p> membrane capacitance (charge integration) : '+ str(npy.round(Cq_med,3))+ 'pF </p>')
    plt.plot(-1,Rs,'m*')
    reporthtml.write('<p> </p><p>Rs = '+str(Rs)+'</p>')
    mVm, mRs, mRi, mCq = Vm, Rs, Ri, Cq_med
    
    try:
        plt.clf()
        plot_axis = npy.arange(0, len(scI_avg)*segmenttimeres,segmenttimeres)

        plt.plot(plot_axis,scI_avg,color = '#c0f080')
        plt.plot(plot_axis,scI_med,color='#80c0f0')

        
        
        plt.plot(segmenttimeres*(start_point_adjusted -5),scI_avg[start_point_adjusted -5],'bs')
        plt.plot(segmenttimeres*(start_point_adjusted -5),scI_med[start_point_adjusted -5],'ro')
        
        plt.plot(segmenttimeres*(end_point_adjusted - 5),scI_avg[end_point_adjusted - 5],'bs')
        plt.plot(segmenttimeres*(end_point_adjusted - 5),scI_med[end_point_adjusted - 5],'ro')
        
        plt.plot(segmenttimeres*(start_point_adjusted) + fit_axis, lsp[0] * npy.exp(-fit_axis/lsp[1]) + lsp[2] + lsp[3]* npy.exp(-fit_axis/lsp[4]),'g--')
        plt.xlabel('time (s)')
        plt.ylabel('amplitude (pA)')
        
        plt.savefig(segmentname + '_average_tp.png')
    except:
        print('plot fail')
    plt.clf()
    
    try:
        reporthtml.write('<p> </p><image src="' + relsegmentname + '_average_tp.png" />' + '<p></p>')
    except:
        print(relsegmentname)

    
    tprecfile = open(segmentname+'_tp_.csv','w')
    tprecfile.write('Rs (MOhm),Vm (mV),Ri (MOhm), Cm_q (pF)\r')


    for tp_s in range(scI_n):
        LS_res1 = least_squares(fitf, x0 =[-200,30,-200,-200,0.05], args = (segmenttimeres*npy.arange(2, 0.8*(end_point_adjusted-start_point_adjusted)+2), scI_sweeps[tp_s][start_point_adjusted+2 : int(npy.round((start_of_testpulse + 0.8*(end_of_testpulse - start_of_testpulse)) /(1000.* segmenttimeres),0)) + 2]),   ftol = 1e-9, xtol = 1e-8, gtol=1e-8, max_nfev = 80000, jac = '3-point', method = 'trf', loss = 'soft_l1' , bounds=([-2000,0,-10000,-2000,0],[2000,500,10000,2000,0.2]))
        lsp = LS_res1.x
        tp_0 = lsp[0] * npy.exp(-0/lsp[1]) + lsp[2] + lsp[3]* npy.exp(-0/lsp[4])
        tp_b = npy.median(scI_sweeps[tp_s][start_point_adjusted -20: start_point_adjusted -1])
        Cq1 = scy.integrate.cumtrapz(scI_sweeps[tp_s][start_point_adjusted + Cq_offset:end_point_adjusted - 5] - scI_sweeps[tp_s][end_point_adjusted - 5])[-1] * segmenttimeres * 1000./ (-5.0) # in pF
        
        tp_ampl = tp_b - tp_0
        Rs = npy.abs(0.001*stepV * 1e+6 / tp_ampl)        #### 1e+6  = 1/1e-12 (the pA)  /1e6  (for MOhm)
        Ri = npy.abs(0.001*stepV * 1e+6 / (tp_b -scI_sweeps[tp_s][end_point_adjusted - 5]))
        Cq = Cq1 * ((Ri-Rs)/((Ri-Rs)-Rs))
        plt.plot(tp_s,Rs, 'g.')
        reporthtml.write('<p>   sweep #'+str(tp_s)+' :  Rs = '+str(Rs)+' ,  Ri = '+str(Ri)+ ' , RMP = ' + str(npy.round(( holdingV + tp_b*(stepV)/(tp_b-scI_sweeps[tp_s][end_point_adjusted - 5]) ),1))  +'mV, Cm (q integration) = '+str(Cq)+' pF </p>')
        tprecfile.write(str(Rs) +','+ str(npy.round(( holdingV + tp_b*(stepV)/(tp_b-scI_sweeps[tp_s][end_point_adjusted - 5]) ),1)) + ','+ str(npy.round((-0.001*stepV*1e+6/npy.abs(tp_b-scI_sweeps[tp_s][end_point_adjusted - 5]) ),1)) + ','+str(Cq)+'\r')
        
    plt.xlabel('test pulse')
    plt.ylabel('R-series (MOhm)')
    plt.savefig(segmentname+'_Rs.png')

    ### testpulse end

    reporthtml.write('<p> </p><image src="'+ relsegmentname+ '_Rs.png" /> <p></p>')
    tprecfile.close()
    
    return (mVm, mRs, mRi, mCq)
    


def main(recfolder, prot_list, ch_list, fir, fir2, fmtselection, window_reference):
    mwi = window_reference
    protocol_scanner = thingies.protocols.prots()
    name_selection = mwi.get_naming_setting()
    timestampsuffix = mwi.get_timestamp_setting()
    output_name = 'test pulse'
    if name_selection != '':
        output_name = 'test pulse-' + name_selection

    if timestampsuffix != '' :
        output_name = output_name + '_' + timestampsuffix 

    outputfolder = output_name+ '_results' 

    expfiles = []
    
    file_extension = '.inf'
    if fmtselection == 'HEKA':
        file_extension = '.inf'
    if fmtselection == 'ABF':
        file_extension = '.abf'
    for file in os.scandir(str(recfolder)):
        if (str(file.path)[-4:]) == file_extension :
            expfiles.append(str(file.path))
            print(len(expfiles))


    currentexpfile = 0
    csshdr = '<style>article.accordion {	display: block;	width: 64000em;	margin: 0 auto;	background-color: #859;	overflow: auto;	border-radius: 12px;	box-shadow: 0 3px 3px rgba(0,0,0,0.3);}article.accordion section{	position: relative;	display: block;	float: left;	width: 2em;	height: 65000em;	margin: 0.5em 0 0.5em 0.5em;	color: #406;	background-color: #406;	overflow: auto;	border-radius: 10px;}article.accordion section h2{	position: absolute;	font-size: 1em;	font-weight: bold;	width: 12em;	height: 2em;	top: 12em;	left: 0;	text-indent: 1em;	padding: 0;	margin: 0;	color: #ddd;	-webkit-transform-origin: 0 0;	-moz-transform-origin: 0 0;	-ms-transform-origin: 0 0;	-o-transform-origin: 0 0;	transform-origin: 0 0;	-webkit-transform: rotate(-90deg);	-moz-transform: rotate(-90deg);	-ms-transform: rotate(-90deg);	-o-transform: rotate(-90deg);	transform: rotate(-90deg);}article.accordion section h2 a{	display: block;	width: 100%;	line-height: 2em;	text-decoration: none;	color: inherit;	outline: 0 none;}article.accordion section:target{	width: 60em;	padding: 0 1em;	color: #333;	background-color: #fff;}article.accordion section:target h2{	position: static;	font-size: 1.3em;	text-indent: 0;	color: #333;	-webkit-transform: rotate(0deg);	-moz-transform: rotate(0deg);	-ms-transform: rotate(0deg);	-o-transform: rotate(0deg);	transform: rotate(0deg);}article.accordion section,article.accordion section h2{	-webkit-transition: all 1s ease;	-moz-transition: all 1s ease;	-ms-transition: all 1s ease;	-o-transition: all 1s ease;	transition: all 1s ease;}</style>'
    reporthtml = open(recfolder + '/' + output_name + '.html','w')
    reporthtml.write('<html><title>Automated summary report - '+ output_name +'</title>'+csshdr+'<p>directory : </p><p>'+ str(recfolder) + '</p><p>Analysis date: '+str(date.today().isoformat())+'</p><p><i>Reported Ri includes Rs, Rs (series) = Rp (pipette) + Ra (access)</i></p><body><article class="accordion">')
    reportcsv = open(recfolder + '/'+output_name+'.csv','w')
    reportcsv.write('sep=|\r')
    reportcsv.write('file|recording|Rs (MOhm)|Vm (mV)|Ri (MOhm)|Cm_q (pF)\r')
            
    for file in os.scandir(str(recfolder)):
        if (str(file.path)[-4:]) == file_extension :
            mwi.update1('# of files: ' + str(len(expfiles)))
            mwi.update2('# of files: ' + str(len(expfiles)))
            totalexpfiles = len(expfiles)
            
            
            reporthtml.write('</section>\r<section id="'+str(file.name)+'"><h2><a href="#'+str(file.name)+'">'+file.name[:-4]+'</a></h2>')
            if not os.path.exists(recfolder+'/'+output_name+'_results/'):
                os.makedirs(recfolder+'/'+output_name+'_results/')

            currentexpfile += 1
            
            try:
                window_reference.update1('processing file ' + str(currentexpfile) + ' of ' + str(totalexpfiles))
                reporthtml.write('<h1>'+ os.fsdecode(file.name) + '</h1>')    
                
                
                successful, preselect, extracted_HEKA, extracted_ABF, extracted_HEKA_V, extracted_ABF_V, HEKA_tstamp, HEKA_protocol, extracted_scale, extracted_resolution, extracted_sweeplength, extracted_tracelength = protocol_scanner.main(os.fsdecode(file.path),reporthtml,'nah',fmtselection,prot_list,ch_list,mwi)
                if successful == False:
                    continue
                
                if fmtselection == 'HEKA':
                    
                    for (k,n,nsel)  in preselect :
                        if len(preselect) >= 1:
                            mwi.update2('processing recording # ' + str(nsel + 1) + ' of ' + str(len(preselect)))
                            
                            h = int(HEKA_tstamp[k]/3600)
                            minutes = int((HEKA_tstamp[k] - 3600 *h) /60)
                        
                            #relative timestamp for easier clustering
                            relminutes = h * 60  + minutes - ((int(HEKA_tstamp[0]/3600)) * 60  + (int((HEKA_tstamp[0] - 3600 * int(HEKA_tstamp[0]/3600)) /60)))
                            
                            # add entry to the report
                            reporthtml.write('<h3> protocol #' + str(n) + ' --- ' + HEKA_protocol[k] + '</h3>')
                            reporthtml.write('<h4><b>' + str(relminutes) + '</b> minutes after start</h4>')
                    
                            #print('t : ' + str(relminutes) + '  --  ' + str(n) + ' : ' + protocol[k])
                            
                            try:    
                                print('trace @ ' + 't : ' + str(relminutes) + '  --  ' + str(nsel) + ' : ' + HEKA_protocol[k] + ' length = ' + str(len(extracted_HEKA[n])))
                                extracted_HEKA_V_scaled = extracted_HEKA_V[n] * 3.1250000e-2
                                mVm, mRs, mRi, mCq  = openthesegment(extracted_HEKA_V_scaled, extracted_HEKA[n], os.fsdecode(file), str(nsel), outputfolder, extracted_scale[n], extracted_resolution[n], len(extracted_HEKA[n]), extracted_tracelength[n], fir=fir, fir2=fir2,reporthtml = reporthtml, fileformat = fmtselection)
                                reporthtml.write('<h4><b>' + str(relminutes) + '</b> minutes after start</h4>')
                                reportcsv.write(str(os.fsdecode(file.name)) +'|'+ str(nsel) +'|'+str(mRs) +'|'+ str(mVm) +'|'+ str(mRi) +'|'+ str(mCq) + '\r')
                            except:
                                reporthtml.write('<h4><b>could not process recording @ ' + str(relminutes) + '</b></h4>')
                    reporthtml.write('\r</section>\r')

                if fmtselection == 'ABF':
                    nsel = 0
                    try:
                        #print(extracted_ABF_V)
                        mVm, mRs, mRi, mCq = openthesegment(segmentV= extracted_ABF_V, segmentI=extracted_ABF, segmentname=os.fsdecode(file), segmentrecnumber= '0', outputfolder=outputfolder, segmentscale= extracted_scale, segmenttimeres= extracted_resolution, segmentlength= len(extracted_ABF), tracelen = extracted_tracelength, fir=fir, fir2=fir2,reporthtml = reporthtml, fileformat=fmtselection)
                        print(str(os.fsdecode(file.name)) +','+ str(nsel) +','+str(mRs) +','+ str(mVm) +','+ str(mRi) +','+ str(mCq) + '\r')
                        reportcsv.write(str(os.fsdecode(file.name)) +'|'+ str(nsel) +'|'+str(mRs) +'|'+ str(mVm) +'|'+ str(mRi) +'|'+ str(mCq) + '\r')
                        reporthtml.write('\r</section>\r')
                    except:
                        print('could not process ABF recording')
                        reporthtml.write('\r</section>\r')
                    
            except:
                reporthtml.write('<p><b>DAMAGED RECORDING FILE (.inf/.dat/.abf) OR OTHER ERROR (disable this exception and try debug)</b></p>')
                reporthtml.write('\r</section>\r')     
        reporthtml.write('\r</section>\r')
    reportcsv.close()
    reporthtml.write('</article></body></html>')
    reporthtml.close()

    mwi.update2('finished')


if __name__ == "__main__":
    print('This is a module.')
    pass