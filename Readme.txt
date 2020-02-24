The information is stored in sampleRecMitdb207.mat.

You can load this in Python as a dictionary

Run the following in Python to extract the data (see below for more info):

from scipy.io import loadmat
a = loadmat('sampleRecMitdb207.mat')

fs = a['Fs'] # sampling frequency = 360Hz
ecg = a['denoised_ecg'] # raw ecg samples
beat_locs = a['ecg_locs'] # beat locations
beat_type = a['beat_type'] # beat annotations : 0 --> Normal, 1--> PVC
vtvf_arr = a['vtvf_arr'] # rhythm annotations for sustained ventricular fibrillation/tachycardia
bi_arr = a['bi_arr'] # rhythm annotations for ventricular bigeminy
tri_arr = a['tri_arr'] # rhythm annotations for ventricular trigeminy
quad_arr = a['quad_arr'] # rhythm annotations for ventricular quadrigeminy
tach_arr = a['tach_arr'] # rhythm annotations for supraventricular tachycardia


The "beat_type" key in the dictionary refers to the annotation type of beats:

	0 indicates a Normal (N) beat
	1 indicates a Ventricular (V) beat
	2 indicates a Supraventricular (S) beat

The beat types have a 1-to-1 correspondence to beat locations (beat_locs) i.e for
each beat location, you mark the corresponding beat as normal, ventricualr or supraventricular
base on the beat_type value.

	
The keys ending with "_arr" refer to the rhythm annotations. For example,
the key "tach_arr" indicates start and stop locations of tachycardia:

>>> print(a['tach_arr'].shape)
	Output:
		(2, 2)  # (#rows, #columns)
		
>>> print(a['tach_arr'])
	Output:
		[[631349, 644297]
		 [644507, 649869]]

The above outputs indicate that there are 2 episodes (indicated by 2 rows) 
and two columns (one for starting sample and one for ending sample), 
corresponding to that episode.

The first episode starts at sample# 631349 and ends at sample# 644297
The second episode starts at sample# 644507 and ends at sample# 649869

So on the plot, you will mark '(TACH' at x-locations 631349 and 644507 for the respective start samples.
Similarly, you will mark 'TACH)' at x-locations 644297 and 649869 for the respective stop samples.

As a general rule, "(rhythmKey" is used for marking start of an episode on the plot and similarly
"rhythmKey)" is used to denote end of an episode on the plot.

For each arrhyhtmia, you can substitute "rhythmKey" with the term that precedes the '_' in the 
arrhythmia key names. for example, for tach_arr, the rhythmKey would be 'tach', for vtvf_arr, the 
rhythmKey would be vtvf, and so on.

Note that some of the rhythm annotations will be empty indicating absence of that specific 
arrhythmia. Your code must just go on to the next arrhythmia in such cases.