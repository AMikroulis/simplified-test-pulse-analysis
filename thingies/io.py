import numpy as npy
import scipy as scy
from scipy import signal as ssy
from matplotlib import pyplot as plt
import os
import sys
from datetime import date
import thingies.protocols


fallback_start_of_testpulse = 100.0    # in ms
fallback_end_of_testpulse = 200.0      # in ms

def openthesegment(segmentV, segmentI, segmentname, segmentrecnumber, outputfolder, segmentscale, segmenttimeres, segmentlength, tracelen, fir, fir2, reporthtml):
    segmentnamebasedir = os.path.dirname(segmentname)
    segmentfilename = os.path.basename(segmentname)
    newsegmentname = os.path.join(segmentnamebasedir, outputfolder, segmentfilename)
    relsegmentname = './'+outputfolder+'/' + segmentfilename[:-4] + '_' + str(segmentrecnumber) + '_'
    segmentname = os.fsdecode(newsegmentname)[:-4] + '_' + str(segmentrecnumber) + '_'

    # read rec
    reportedfs = npy.round(100./(segmenttimeres), 0)/100.0

    try:
        scI = segmentI * segmentscale / 1e-12
        scV = segmentV * segmentscale / 1e-12
    except:
        scI = segmentI * 3.1250000e-1
        scV = segmentV * 3.1250000e-1
    t_ = npy.arange(0,segmenttimeres * len(scI),segmenttimeres)[:len(scI)]
    plt.clf()
    plt.plot(t_,scI)
    plt.xlabel('time (s)')
    plt.ylabel('current (pA)')
    plt.savefig(segmentname+'_I.png')
    scV = segmentV #* 3.1250000e-2
    plt.clf()
    plt.plot(t_,scV)
    plt.xlabel('time (s)')
    plt.ylabel('voltage (mV)')
    plt.savefig(segmentname+'_V.png')

    scI_n = int(npy.size(scI)/tracelen)
    #print('scI length = ' + str(npy.size(scI))+ ' , sweeplength = ' + str(tracelen))

    scI_sweeps = npy.reshape(scI[0:tracelen*scI_n], [scI_n, tracelen])
    scV_sweeps = npy.reshape(scV[0:tracelen*scI_n], [scI_n, tracelen])
    
    plt.clf()
    for q in range(scI_n):
        plt.plot(scV_sweeps[q])
    plt.savefig(segmentname+'_Vsteps.png')

    # autodetect to the nearest ms:
    try:
        scV_min = npy.argmin(npy.diff(scV_sweeps[:][5])) / reportedfs
        scV_max = npy.argmax(npy.diff(scV_sweeps[:][5])) / reportedfs
        tp_min = npy.round(scV_min*1000, 0)
        tp_max = npy.round(scV_max*1000, 0)
        tp_start = min(tp_min, tp_max)
        tp_end = max(tp_min, tp_max)
        start_of_testpulse = tp_start
        end_of_testpulse = tp_end
    except:
        print('failed to detect pulse - using defaults')
        start_of_testpulse = fallback_start_of_testpulse
        end_of_testpulse = fallback_end_of_testpulse

    plt.clf()
    iorecfile = open(segmentname+'_io_.csv', 'w')
    iorecfile.write('sep=|\r')
    iorecfile.write('step (mV)|Na (pA)|K-fast (pA)|K-slow (pA)|t_AP (ms)|t_AHP (ms)|holding current (pA)| negative peak (pA)| positive peak (pA)\r')

    
    steps, holding_currents, min_currents, max_currents, Na_currents, K_slow_currents, K_fast_currents = [], [], [], [], [], [], []
    
    for tp_s in range(scI_n):
        
        try:
            Q0point = int(npy.round(start_of_testpulse / (1000. * segmenttimeres), 0)) + 1
            Q1point = int(npy.round(start_of_testpulse / (1000. * segmenttimeres), 0)) + int(npy.round((end_of_testpulse - start_of_testpulse) / (4000. * segmenttimeres), 0))
            Q3point = int(npy.round(start_of_testpulse / (1000. * segmenttimeres), 0)) + int(npy.round(3*(end_of_testpulse - start_of_testpulse) / (4000. * segmenttimeres), 0))
            Q4point = int(npy.round(end_of_testpulse / (1000. * segmenttimeres), 0)) - 1

            stepV = npy.median(scV_sweeps[tp_s][Q1point:Q3point])
            stepV = npy.round(int(1000 * stepV)/1000, 0)  # to nearest mV
            

            holding_current = npy.median(scI_sweeps[tp_s][0:Q0point])
            min_current = npy.min(scI_sweeps[tp_s][Q0point+5:Q4point - int(20.0 / (1000. * segmenttimeres))])
            min_current_t = Q0point + 5 + npy.argmin(scI_sweeps[tp_s][Q0point+5:Q4point - int(20.0 / (1000. * segmenttimeres))])
            max_current = npy.max(scI_sweeps[tp_s][min_current_t:min_current_t + int(20.0 / (1000. * segmenttimeres))])
            max_current_t = min_current_t + npy.argmax(scI_sweeps[tp_s][min_current_t:min_current_t + int(20.0 / (1000. * segmenttimeres))])

            ss_current = npy.median(scI_sweeps[tp_s][Q3point:Q4point])

            Na_current = min_current - ss_current
            K_fast_current = max_current - ss_current
            K_slow_current = ss_current

            steps.append(stepV)
            holding_currents.append(holding_current)
            min_currents.append(min_current)
            max_currents.append(max_current)
            Na_currents.append(Na_current)
            K_fast_currents.append(K_fast_current)
            K_slow_currents.append(K_slow_current)

            iorecfile.write(str(stepV)+'|'+str(Na_current)+'|'+str(K_fast_current)+'|'+str(K_slow_current)+'|'+str(min_current_t/(1000. * segmenttimeres)) + '|' + str(max_current_t / (1000. * segmenttimeres))+'|'+str(holding_current) + '|'+str(min_current) + '|'+str(max_current)+'\r')

        except:
            print('sweep failed')

    holding_currents_fold, min_currents_fold, max_currents_fold, Na_currents_fold, K_fast_currents_fold, K_slow_currents_fold = [], [], [], [], [], []
    holding_currents_meds, min_currents_meds, max_currents_meds, Na_currents_meds, K_fast_currents_meds, K_slow_currents_meds = [], [], [], [], [], []
    unique_steps = list(npy.unique(steps))
    print('total steps: '+ str(unique_steps))
    
    for step_index in range(len(unique_steps)):
        holding_currents_fold, min_currents_fold, max_currents_fold, Na_currents_fold, K_fast_currents_fold, K_slow_currents_fold = [], [], [], [], [], []
        sweep_index = 0
        for tp_s in range(len(steps)):
            if unique_steps[step_index] == steps[tp_s]:
                holding_currents_fold.append(holding_currents[tp_s])
                min_currents_fold.append(min_currents[tp_s])
                max_currents_fold.append(max_currents[tp_s])
                Na_currents_fold.append(Na_currents[tp_s])
                K_fast_currents_fold.append(K_fast_currents[tp_s])
                K_slow_currents_fold.append(K_slow_currents[tp_s])
            sweep_index += 1
        holding_currents_med = npy.median(holding_currents_fold)
        min_currents_med = npy.median(min_currents_fold)
        max_currents_med = npy.median(max_currents_fold)
        Na_currents_med = npy.median(Na_currents_fold)
        K_fast_currents_med = npy.median(K_fast_currents_fold)
        K_slow_currents_med = npy.median(K_slow_currents_fold)
        
        holding_currents_meds.append(holding_currents_med) 
        min_currents_meds.append(min_currents_med) 
        max_currents_meds.append(max_currents_med)
        Na_currents_meds.append(Na_currents_med)
        K_fast_currents_meds.append(K_fast_currents_med)
        K_slow_currents_meds.append(K_slow_currents_med)

    
    plt.plot(unique_steps, Na_currents_meds, '#400080',unique_steps, K_fast_currents_meds, '#008000',unique_steps, K_slow_currents_meds, '#808080')
    plt.gca().legend(('Na','K (fast)','K (slow)'))
    plt.xlabel('voltage (mV)')
    plt.ylabel('current (pA)')
    plt.savefig(segmentname + '_currents.png')
    reporthtml.write('<p> </p><image src="' + relsegmentname + '_currents.png" /> <p></p>')

    iorecfile.close()

    
    #segmentdataoutput.append(0)

    return (steps, Na_currents, K_fast_currents, K_slow_currents, holding_currents, min_currents, max_currents)

def main(recfolder, prot_list, ch_list, fir, fir2, fmtselection, window_reference):
    mwi = window_reference
    protocol_scanner = thingies.protocols.prots()
    name_selection = mwi.get_naming_setting()
    timestampsuffix = mwi.get_timestamp_setting()
    output_name = 'io'
    if name_selection != '':
        output_name = 'io-' + name_selection

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
    reporthtml.write('<html><title>Automated summary report - '+ output_name +'</title>'+csshdr+'<p>directory : </p><p>'+ str(recfolder) + '</p><p>Analysis date: '+str(date.today().isoformat())+'</p><body><article class="accordion">')
    reportcsv = open(recfolder + '/'+output_name+'.csv','w')
    reportcsv.write('sep=|\r')
    reportcsv.write('file|recording|step (mV)|Na (pA)|K fast (pA)|K slow (pA)|holding (pA)|negative peak (pA)|positive peak (pA)\r')
    
    def writecsv(file_name, nsel, steps, Na_currents, K_fast_currents, K_slow_currents, holding_currents, min_currents, max_currents):
        holding_currents_fold, min_currents_fold, max_currents_fold, Na_currents_fold, K_fast_currents_fold, K_slow_currents_fold = [], [], [], [], [], []
        holding_currents_meds, min_currents_meds, max_currents_meds, Na_currents_meds, K_fast_currents_meds, K_slow_currents_meds = [], [], [], [], [], []
        unique_steps = list(npy.unique(steps))
    
        for step_index in range(len(unique_steps)):
            holding_currents_fold, min_currents_fold, max_currents_fold, Na_currents_fold, K_fast_currents_fold, K_slow_currents_fold = [], [], [], [], [], []
            sweep_index = 0
            for tp_s in range(len(steps)):
                if unique_steps[step_index] == steps[tp_s]:
                    holding_currents_fold.append(holding_currents[tp_s])
                    min_currents_fold.append(min_currents[tp_s])
                    max_currents_fold.append(max_currents[tp_s])
                    Na_currents_fold.append(Na_currents[tp_s])
                    K_fast_currents_fold.append(K_fast_currents[tp_s])
                    K_slow_currents_fold.append(K_slow_currents[tp_s])
                sweep_index += 1
            holding_currents_med = npy.median(holding_currents_fold)
            min_currents_med = npy.median(min_currents_fold)
            max_currents_med = npy.median(max_currents_fold)
            Na_currents_med = npy.median(Na_currents_fold)
            K_fast_currents_med = npy.median(K_fast_currents_fold)
            K_slow_currents_med = npy.median(K_slow_currents_fold)
        
            holding_currents_meds.append(holding_currents_med) 
            min_currents_meds.append(min_currents_med) 
            max_currents_meds.append(max_currents_med)
            Na_currents_meds.append(Na_currents_med)
            K_fast_currents_meds.append(K_fast_currents_med)
            K_slow_currents_meds.append(K_slow_currents_med)
            reportcsv.write(str(os.fsdecode(file_name)) +'|'+ str(nsel) +'|'+ str(unique_steps[step_index]) +'|'+ str(Na_currents_med) +'|'+ str(K_fast_currents_med) +'|'+ str(K_slow_currents_med) +'|'+ str(holding_currents_med) +'|'+ str(min_currents_med) +'|'+ str(max_currents_med) +'\r')


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
                                steps, Na_currents, K_fast_currents, K_slow_currents, holding_currents, min_currents, max_currents = openthesegment(extracted_HEKA_V_scaled, extracted_HEKA[n], os.fsdecode(file), str(nsel), outputfolder, extracted_scale[n], extracted_resolution[n], len(extracted_HEKA[n]), extracted_tracelength[n], fir=fir, fir2=fir2,reporthtml = reporthtml)
                                reporthtml.write('<h4><b>' + str(relminutes) + '</b> minutes after start</h4>')
                                file_name = file.name
                                writecsv(file_name, nsel, steps, Na_currents, K_fast_currents, K_slow_currents, holding_currents, min_currents, max_currents)

                            except:
                                reporthtml.write('<h4><b>could not process recording @ ' + str(relminutes) + '</b></h4>')


                if fmtselection == 'ABF':
                    nsel = 0
                    try:
                        print(extracted_ABF_V)
                        steps, Na_currents, K_fast_currents, K_slow_currents, holding_currents, min_currents, max_currents = openthesegment(segmentV= extracted_ABF_V, segmentI=extracted_ABF, segmentname=os.fsdecode(file), segmentrecnumber= '0', outputfolder=outputfolder, segmentscale= extracted_scale, segmenttimeres= extracted_resolution, segmentlength= len(extracted_ABF), tracelen = extracted_tracelength, fir=fir, fir2=fir2,reporthtml = reporthtml)
                        file_name = file.name
                        print('calling calculation function...')
                        writecsv(file_name, nsel, steps, Na_currents, K_fast_currents, K_slow_currents, holding_currents, min_currents, max_currents)

                    except:
                       print('could not process ABF recording')
                
            except:
                reporthtml.write('<p><b>DAMAGED RECORDING FILE (.inf/.dat/.abf) OR OTHER ERROR (disable this exception and try debug)</b></p>')
            
            reporthtml.write('\r</section>\r')
    reportcsv.close()
    reporthtml.write('</article></body></html>')
    reporthtml.close()

    mwi.update2('finished')


if __name__ == "__main__":
    print('This is a module.')
    pass