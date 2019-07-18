from ophyd import EpicsSignal
import numpy as np
import matplotlib.pyplot as plt
import time
from decimal import Decimal
import os
import sys
import threading
sys.path.append('../')
pv_EM6 = 'XF:12IDA-BI:2{EM:BPM1}'
pv_EM102 = 'XF:12IDA-BI:2{EM:BPM2}'
interval = 30 #30s between each measurement spans
span=25 #time span to take data
max_time=3600*48 # run for 24 hours

time_init=time.time()
out='channel, start time(s), end time (s), voltage mean, voltage std, voltage num, current mean, current std, current num'

#Initialization
EpicsSignal(pv_EM6+'CalibrationMode').put(1)
EpicsSignal(pv_EM6+'CopyADCOffsets.PROC').put(0)
EpicsSignal(pv_EM6+'CalibrationMode').put(0)

EpicsSignal(pv_EM6+'AveragingTime').put(100e-3)
EpicsSignal(pv_EM6+'TS:TSAveragingTime').put(100e-3)
EpicsSignal(pv_EM6+'TS:TSNumPoints').put(1)

EpicsSignal(pv_EM6+'TS:TSAcquireMode').put(0) #sets to circular buffer
EpicsSignal(pv_EM6+'Range').put(0) #sets range to 1micro amp

#DATA COLLECTION
with open(path+"/drift."+trial_id+".csv","w") as f: #open a file to write data to
    f.write(out+'\n')
    counter = 0
    time_init=time.time()
    target_time = time_init+counter*interval
    while time.time() < time_init+max_time:
        if time.time() > target_time:
            counter+=1
            target_time = time_init+counter*interval
            drift_curr_6=[]
            temp_curr_102=[]
            start_time=0
            end_time=0
            def collect(id):
                while time.time() < start_time+span:
                    if id==0: #Temperature collection
                        #pro.write("meas:volt:dc?",13)
                        #value_measured_orig=pro.readline()
                        #value_measured=value_measured_orig.split(',')[0].split('N')[0]
                    if id==1: #Drift collection
                        isAquiring = EpicsSignal(pv_EM6+'TS:TSAcquiring').get()
                        if isAquiring == 0: #if it's done acquiring
                            channel=1 #1-4
                            curr_str=EpicsSignal(pv_EM6+'TS:Current'+channel+':TimeSeries').value
                            drift_curr_6.append(curr_str[0])
                            EpicsSignal(pv_EM6+'TS:TSAcquire').put(1) #acquire new data

            temp_thread = threading.Thread(target=collect, args=(0,))
            drift_thread = threading.Thread(target=collect, args=(1,))
            EpicsSignal(pv_EM6+'TS:TSAcquire').put(1) #acquire new data
            start_time=time.time()
            # starting thread 1
            drift_thread.start()
            # starting thread 2
            temp_thread.start()

            # wait until thread 1 is completely executed
            drift_thread.join()
            # wait until thread 2 is completely executed
            temp_thread.join()
            end_time=time.time()

            temp_curr_mean = np.average(temp_curr_102)
            temp_curr_std = np.std(temp_curr_102,ddof=1)
            temp_curr_num = len(temp_curr_102)

            drift_curr_mean = np.average(drift_curr_6)
            drift_curr_std = np.std(drift_curr_6,ddof=1)
            drift_curr_num=len(drift_curr_6)

            out=str(start_time)+','+str(end_time)+','+str(voltage_mean)+','+str(voltage_std)+','+str(voltage_num)+','+str(current_mean)+','+str(current_std)+','+str(current_num)
            print(out)
            f.write(out+'\n')
            f.flush()

print('Finished')
