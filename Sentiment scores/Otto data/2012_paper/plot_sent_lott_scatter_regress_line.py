font = {'family' : 'Helvetica', 
        'weight':'normal',
        'size'   : 20}
matplotlib.rc('font', **font)

ANALYSIS_YEAR = 2013
ALPHA = 0.1

msa =  'chicago' # 'nyc'  
IV = 'affect_mean' 
DV = 'resid' 
NUM_BINS = 4


resid_file = 'regress/lott_resid/'+msa+'_lott_resid_'+str(ANALYSIS_YEAR)+'_full.csv' 
resid_lott = read_csv(resid_file)
try: resid_lott.index = map(lambda x:datetools.to_datetime(x), resid_lott.X)
except: resid_lott.index = map(lambda x:datetools.to_datetime(x), resid_lott.date)
resid_lott['date'] = resid_lott.index

for col in resid_lott.columns:
    if(col not in ['date', 'resid', 'ZIP', 'log_purchase']):
        resid_lott = resid_lott.drop(col, 1)


resid_sent_file = 'regress/sent_resid/resid_'+msa + '_' + str(ANALYSIS_YEAR)+'_full.csv' 
resid_sent = read_csv(resid_sent_file)
try: resid_sent.index = map(lambda x:datetools.to_datetime(x), resid_sent.X)
except: resid_sent.index = map(lambda x:datetools.to_datetime(x), resid_sent.date)
resid_sent['date'] = resid_sent.index

for col in resid_sent.columns:
    if(col not in ['date', 'resid_sent', 'affect_mean', 'county']):
        resid_sent = resid_sent.drop(col, 1)

if(msa=='nyc'):    
    demographics = read_pickle('../data/demographics.dat')
    zip_to_county = DataFrame(columns=['ZIP', 'county'])
    zip_to_county['county'] = map(lambda x: {'Manhattan':'new york',
                                               'Staten Island':'richmond',
                                               'Bronx':'bronx',
                                               'Queens':'queens',
                                               'Brooklyn':'kings'}[x.split(':')[0]], demographics.desc)
    zip_to_county['ZIP'] = demographics.index
    zip_county = map(lambda x: zip_to_county[zip_to_county['ZIP']==x].iloc[0].county, resid_lott.ZIP)
    resid_lott['county']=zip_county
else:   
    demographics = read_pickle('../data/chicago_demographics.dat')
    zip_county = map(lambda x: demographics[demographics['ZIP']==x].iloc[0].desc.split(':')[0], resid_lott.ZIP)
    resid_lott['county']=zip_county


resid_sent.date = resid_sent.date.values.astype('datetime64[ns]')
resid_lott.date = resid_lott.date.values.astype('datetime64[ns]')


resid_lott = resid_lott.merge(resid_sent, on=['date', 'county'])


demographics = read_pickle('../data/extended_county_demographics.dat')

msa_pop = 0


county_weighting = {}.fromkeys( resid_lott.county.unique())

for county in resid_lott.county.unique():
    msa_pop += demographics[(demographics.county==county) & (demographics.msa==msa) ]['population'].iloc[0]
    print county, demographics[(demographics.county==county) & (demographics.msa==msa) ]['population'].iloc[0]

for county in resid_lott.county.unique():       
    county_weighting[county] = demographics[(demographics.county==county) & (demographics.msa==msa) ]['population'].iloc[0] / msa_pop


color_map = [[0, 0, .5, .6], [0, .5, 0, .8]] #['blue', 'green', 'red', 'orange', 'purple']


figure()
for county in resid_lott.county.unique():
    county_lott = resid_lott[resid_lott.county == county]

    if(msa == 'chicago'):     county_lott['affect_mean'] =pd_zscore(county_lott.affect_mean) 
    else: county_lott['affect_mean'] = pd_zscore(county_lott.resid_sent) 

    county_lott = county_lott[abs(county_lott.affect_mean) < 4]

    x = county_lott[IV]
    y = county_lott[DV]

    PE_BINS  = histogram(county_lott[~isnan(county_lott[IV])][IV],NUM_BINS)[1][1:].tolist() 
    PE_BIN_SIZE = PE_BINS[-1] - PE_BINS[-2]

    [mean_pe,sem_pe] = [[],[]]
    for bin_num in range(len(PE_BINS)):
        lower_pe = PE_BINS[bin_num] - PE_BIN_SIZE
        upper_pe = PE_BINS[bin_num]  
        bin_dv = county_lott[logical_and(county_lott[IV]>lower_pe,
                                      county_lott[IV]<=upper_pe)][DV]

        mean_pe.append( mean(bin_dv) ) 
        sem_pe.append( std(county_lott[logical_and(county_lott[IV]>lower_pe, county_lott[IV]<=upper_pe)][DV]) / sqrt(len(county_lott[logical_and(county_lott[IV]>lower_pe, county_lott[IV]<=upper_pe)][DV])))


    errorbar(    array(PE_BINS), 
                 mean_pe[:],
                 yerr=sem_pe[:], 
                 marker = '.',
                 ms = 25*(log(county_weighting[county])- min(log(array(county_weighting.values()))) ),
                 color=color_map[resid_lott.county.unique().tolist().index(county)],
                 ecolor={'will':'black', 'cook':'black'}[county], 
                 label=county,
                 lw = 2,
                 elinewidth = 1,
                 capsize=10)


legend(loc='lower right', numpoints=1, ncol=5, title='county', fontsize=12, labelspacing=1) #borderpad = 1, 


file_name = 'regress/effect_plot_df/'+msa+ '_sent_lott_'  +  str(ANALYSIS_YEAR) + '.csv'
effects_df = read_csv(file_name)
effects_df = effects_df[effects_df[IV] >= -2]

errorbar(effects_df[IV] , effects_df['fit']  - effects_df.fit.mean() +.02,
         color='black',
         lw = 3, ecolor='black',elinewidth=1, label=IV + '('+str(ANALYSIS_YEAR) + ')', 
         capsize=5) 

fill_between( effects_df[IV], 
              effects_df['fit'] - effects_df['se'] - effects_df.fit.mean() +.02,
              effects_df['fit'] + effects_df['se'] - effects_df.fit.mean() +.02,
              color=(.7, .7, .7, .3) ,linewidth=0) 

plot([PE_BINS[1]-PE_BIN_SIZE-2,PE_BINS[-1]+2], [0,0], color='gray', ls=':')


xlim(min(effects_df[IV])-.5, max(effects_df[IV])+.5)
xlabel('county-level Twitter mood on current day (z-score)')
ylabel('residual per capita lottery purchases')
show()

