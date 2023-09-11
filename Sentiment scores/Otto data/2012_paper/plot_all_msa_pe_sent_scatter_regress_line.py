font = {'family' : 'Helvetica', 
        'weight':'normal',
        'size'   : 18}
matplotlib.rc('font', **font)

ANALYSIS_YEAR = 2013


MSA_NAMES = {'sfbay':'SF Bay', 
             'chicago':'Chicago', 
             'boston':'Boston', 
             'dfw':'DFW', 
             'nyc_metro':'NYC', 
             'la': 'LA'}


IV = 'sports_sum_pe_with_na'  #'dni_pe' #
DV = 'resid_sent' #''affect_mean' 
NUM_BINS = 3


file_name = 'regress/effect_plot_df/all_msa_' + \
    {'affect_mean':'sent', 'sports_sum_pe_with_na':'sports', 'dni_pe':'irradiance'}[IV] + \
    '_sent_' +  str(ANALYSIS_YEAR) + '.csv'
effects_df = read_csv(file_name)
effects_df = effects_df[effects_df[IV] >= -2.5]

resid_file = 'regress/sent_resid/resid_all_msa_'+str(ANALYSIS_YEAR)+'_full.csv' 
resid_sent = read_csv(resid_file)
try: resid_sent.index = map(lambda x:datetools.to_datetime(x), resid_sent.X)
except: resid_sent.index = map(lambda x:datetools.to_datetime(x), resid_sent.date)

msas = ['sfbay', 'chicago', 'boston', 'dfw', 'nyc_metro', 'la'] 

demographics = read_pickle('../data/misc/extended_county_demographics.dat')

all_msa_weighting = {}.fromkeys(resid_sent.msa.unique())
all_msa_pop = 0
for county_msa in  (resid_sent.county+':' + resid_sent.msa).unique():
    all_msa_pop += demographics[(demographics.county==county_msa.split(':')[0]) & 
                                (demographics.msa==county_msa.split(':')[1]) ]['population'].iloc[0]

for msa in resid_sent.msa.unique():
    msa_pop = 0
    for county in resid_sent[resid_sent.msa==msa].county.unique():
        msa_pop += demographics[(demographics.county==county) & (demographics.msa==msa) ]['population'].iloc[0]
    all_msa_weighting[msa] = msa_pop / all_msa_pop



fig= figure()
num_colors = len(msas)
cm = get_cmap('Paired')
ax = fig.add_subplot(111)

for msa in msas:
    msa_sent = resid_sent[resid_sent.msa == msa]

    PE_BINS  = histogram(msa_sent[~isnan(msa_sent[IV])][IV],NUM_BINS)[1][1:].tolist() 
    PE_BIN_SIZE = PE_BINS[-1] - PE_BINS[-2]

    [mean_pe,sem_pe] = [[],[]]
    for bin_num in range(len(PE_BINS)):
        lower_pe = PE_BINS[bin_num] - PE_BIN_SIZE
        upper_pe = PE_BINS[bin_num]   
        bin_dv = msa_sent[logical_and(msa_sent[IV]>lower_pe,
                                        msa_sent[IV]<=upper_pe)][DV]+  resid_sent.affect_mean.mean()
        mean_pe.append( mean(bin_dv) ) 


        n = msa_sent[logical_and(msa_sent[IV]>lower_pe,  msa_sent[IV]<=upper_pe)]['num_tweets'].mean()
        sem_pe.append( std(bin_dv) / sqrt(n))

    print msa, [cm(.5*i/num_colors) for i in range(num_colors)][msas.index(msa)]

    errorbar(array(PE_BINS),
             mean_pe[:],
             color=[cm(.5*i/num_colors) for i in range(num_colors)][msas.index(msa)],
             yerr=sem_pe[:], 
             label=MSA_NAMES[msa],
             lw = 2, 
             ecolor=[cm(.5*i/num_colors) for i in range(num_colors)][msas.index(msa)],
             elinewidth = 1,
             ms = 25*(log(all_msa_weighting[msa])- min(log(array(all_msa_weighting.values()))) ),
             capsize=10,
             marker='.')


legend(loc='lower right', numpoints=1, ncol=2, title='MSA', fontsize=12, labelspacing=1, scatterpoints = 1)
show()



errorbar(effects_df[IV] , effects_df['fit'],
         color='black', 
         lw = 1, ecolor='black',elinewidth=1, label=IV + '('+str(ANALYSIS_YEAR) + ')', 
         capsize=5) 

fill_between( effects_df[IV], 
              (effects_df['fit']) - effects_df['se'], 
              (effects_df['fit']) + effects_df['se'], 
              color=(.7, .7, .7, .3) ,linewidth=0) 


xlim(min(effects_df[IV])-.5, max(effects_df[IV])+.5)
xlabel(IV)
ylabel(DV)
show()

