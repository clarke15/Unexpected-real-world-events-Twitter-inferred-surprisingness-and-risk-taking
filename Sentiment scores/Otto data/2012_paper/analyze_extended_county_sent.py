import gzip, os
from numpy import *
from pylab import *
from scipy.stats import zscore, pearsonr, linregress, scoreatpercentile
from pandas import DataFrame, date_range, Series, datetools, tseries, rolling_mean, rolling_std, concat, HDFStore, merge, read_csv, read_pickle, read_excel, to_datetime, Timestamp
#import statsmodels.api as sm
import urllib2, csv, re, cPickle, calendar, time
from datetime import datetime
import statsmodels.api as sm
import statsmodels.formula.api as smf

def pd_zscore(x): return (x - mean(x)) / std(x)


DAY_NAMES = ['MON','TUE','WED','THU','FRI','SAT','SUN']
MONTH_NAMES = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC ']

msa_mapping = {'la': ['06-037','06-059','06-065','06-111','06-071'],
               'chicago':['17-031','17-037','17-043','17-063','17-089','17-093','17-111','17-197','17-097','18-073','18-089','18-111','18-127','55-059'],
               'dfw':['48-085','48-113','48-121','48-139','48-221','48-231','48-251','48-257','48-367','48-397','48-439','48-497'],
               'sfbay':['06-001','06-013','06-081','06-041','06-085','06-069','06-097','06-077','06-095','06-085','06-055','06-075'],
               'boston':['25-027','25-005','44-001','44-003','44-005','44-007','44-009','09-015','33-013','33-001','33-011','25-001',
                         '25-021','25-023','25-025','25-017','25-009','33-015','33-017'],
               'nyc_metro':['36-047','36-081','36-061','36-005','36-085','36-119','36-087','36-071','36-103','36-059','36-079','36-027',
                            '34-003','34-017','34-023','34-025','34-029','34-031','34-013','34-039','34-027','34-035','34-037','34-019']}
nyc_fips_codes = ['36-047', '36-081', '36-061', '36-005', '36-085']

DATE_RANGES = { 2012: date_range(datetime(2012, 1, 1), datetime(2012, 12,31)),
                2013: date_range(datetime(2013, 1, 1), datetime(2013, 12,31))}
DAY_NAMES = ['MON','TUE','WED','THU','FRI','SAT','SUN']
MONTH_NAMES = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC ']
ANALYSIS_YEAR = 2013
WEATHER_ALPHA = 0.1
SPORTS_ALPHA = 0.1
analysis_range = DATE_RANGES[ANALYSIS_YEAR]

fips_county = read_csv('../data/misc/fips_county.csv')

demographics = read_pickle('../data/county_data/extended_county_demographics.dat')
sent = read_csv('../data/sent_estimates/extended_county_list_afint_counts.csv')
new_sent = DataFrame(columns=['county', 'date', 'affect_mean'])

for col in sent.columns:
    if('affect_mean'  not in col): continue
    if(len(col.split('_')[0]) < 5):  fixed_col = '0'  + col 
    else: fixed_col = col

    state = int(fixed_col.split('_')[0][0:2])
    county = int(fixed_col.split('_')[0][2:])
    county_name = fips_county[(fips_county.fips_state==state) & (fips_county.fips_county==county)].county_name.values[0].replace('County',' ').lower().strip()
    sent[county_name+'_'+'_'.join(col.split('_')[1:])] = sent[col]

    msa_found = False
    for msa_name, fips_codes in msa_mapping.iteritems():
        if("%02d" % (state,) + '-' + "%03d" % (county,) in fips_codes):
            msa_found = True
            break
    new_sent = new_sent.append( DataFrame({'date':sent.created_date,
                                           'affect_mean' :sent[col],
                                           'num_tweets': sent[col.split('_')[0] + '_counts'],
                                           'msa':msa_name,
                                           'county': county_name}) )

    print 'loading sentiment estimates:', msa_name, county_name

for col in sent.columns:
    if(('affect_mean'  not in col) or (not col[0].isdigit())): continue
    if(len(col.split('_')[0]) < 5):  fixed_col = '0'  + col 
    else: fixed_col = col

    state = int(fixed_col.split('_')[0][0:2])
    county = int(fixed_col.split('_')[0][2:])
    county_name = fips_county[(fips_county.fips_state==state) & (fips_county.fips_county==county)].county_name.values[0].replace('County',' ').lower().strip()
    sent[county_name+'_'+'_'.join(col.split('_')[1:])] = sent[col]

    msa_found = False
    if("%02d" % (state,) + '-' + "%03d" % (county,) in nyc_fips_codes):
        msa_found = True

    if(not msa_found): continue

    new_sent = new_sent.append( DataFrame({'date':sent.created_date,
                                           'affect_mean' :sent[col],
                                           'num_tweets': sent[col.split('_')[0] + '_counts'],
                                           'msa':'nyc',
                                           'county': county_name}) )

sent = new_sent
sent.date = to_datetime(sent.date)
sent.index = sent.date
sent = sent[map(lambda x:x.year==ANALYSIS_YEAR, sent.date)]

bad_counties = []
for msa in sent.msa.unique():
    print '***', msa
    msa_sent = sent[sent.msa==msa]
    for county in msa_sent.county.unique():
        num_bad_days = len(msa_sent[(msa_sent.county==county) & ((msa_sent.num_tweets<100) | (msa_sent.num_tweets>10000))])
        num_days = len(msa_sent[msa_sent.county==county])
        
        if((num_days < 292) or (num_bad_days > 72)):   #contains less than 80%  useful days
            bad_counties.append(county)
            print 'DROPPING COUNTY:', county, num_bad_days, 'bad days'
        else:
            print '\t', county, 'dropping:', num_bad_days, 'days'

print 'dropping:', len(bad_counties), 'counties'

for bad_county in bad_counties:
    sent = sent[sent.county != bad_county]

sent = sent[(sent.num_tweets>=100) & (sent.num_tweets<10000)]

print 'final n obs:', len(sent)

days_of_week_regressors = DataFrame(index=analysis_range)
for day_of_week in range(7):
    days_of_week_regressors[DAY_NAMES[day_of_week]] = map(int, analysis_range.dayofweek==day_of_week)

month_of_year_regressors = DataFrame(index=analysis_range)
for month_of_year in range(12):
    month_of_year_regressors[MONTH_NAMES[month_of_year]] = map(int, analysis_range.month==month_of_year)


csv_file = open('../data/misc/holidays_sent.csv', 'rU')
reader = csv.DictReader(csv_file)
holidays = {}
for row in reader:
    holidays[datetools.to_datetime(row['date'], errors='raise')] = row['holiday'] #+'_'+str(datetools.to_datetime(row['date'], errors='raise').year)[-2:]


ind_holiday_regressors = DataFrame(index=analysis_range)
for holiday_date, name in holidays.iteritems():
    if(holiday_date in analysis_range): 
        if(not '*' in name):
            holiday_name = name.replace(' ', '').replace('\'','').replace('*','2').replace('.', '').upper()
            ind_holiday_regressors[holiday_name] = Series( map(int, analysis_range == holiday_date),index=analysis_range)

for holiday_date, name in holidays.iteritems():
    if(holiday_date in analysis_range): 
        if('*' in name):
            holiday_name = name.replace(' ', '').replace('\'','').replace('*','').replace('.', '').upper()
            ind_holiday_regressors[holiday_name].ix[holiday_date] = 1

payday_regressors = DataFrame(index=analysis_range)
payday_regressors['FIRST_OF_MONTH'] = zeros(len(analysis_range))
payday_regressors['FIFTEENTH_OF_MONTH'] = zeros(len(analysis_range))

for date in analysis_range:
    if(date.day == 1):
        if((not datetools.isBusinessDay(date)) or sum(ind_holiday_regressors.ix[date]) > 0):
            for i in range(5):
                if((date-i)  not in analysis_range):   break
                if(datetools.isBusinessDay(date-i)):
                    payday_regressors['FIRST_OF_MONTH'].ix[date-i]  = 1
                    break
        else:
            payday_regressors['FIRST_OF_MONTH'].ix[date]  = 1
    elif(date.day == 15):
        if((not datetools.isBusinessDay(date)) or sum(ind_holiday_regressors.ix[date]) > 0):
            for i in range(5):
                if((date-i)  not in analysis_range): break
                if(datetools.isBusinessDay(date-i)):
                    payday_regressors['FIFTEENTH_OF_MONTH'].ix[date-i]  = 1
                    break
        else:
            payday_regressors['FIFTEENTH_OF_MONTH'].ix[date]  = 1

all_msa_county_weighting = {}.fromkeys((sent.county+':' + sent.msa).unique())
all_msa_pop = 0
for county_msa in  (sent.county+':' + sent.msa).unique():
    all_msa_pop += demographics[(demographics.county==county_msa.split(':')[0]) & 
                                (demographics.msa==county_msa.split(':')[1]) ]['population'].iloc[0]
for county_msa in  (sent.county+':' + sent.msa).unique():
    all_msa_county_weighting[county_msa] = demographics[(demographics.county==county_msa.split(':')[0]) & 
                                                        (demographics.msa==county_msa.split(':')[1])]['population'].iloc[0] / all_msa_pop




regress_df = DataFrame()
for msa in ['sfbay', 'la',  'chicago', 'boston', 'dfw', 'nyc_metro']:
    print 'outputting:', msa
    msa_regress_df = DataFrame() 
    
    sports = read_csv('../data/sports/'+msa+'_sports_'+str(ANALYSIS_YEAR)+'.csv')

    county_weighting = {}.fromkeys(sent[sent.msa==msa].county.unique())
    
    adj_msa_pop = 0
    for county in  sent[sent.msa==msa].county.unique():
        adj_msa_pop += demographics[demographics.county==county]['population'].iloc[0]

    for county in  sent[sent.msa==msa].county.unique():
        county_weighting[county] = demographics[(demographics.msa==msa) & (demographics.county==county)]['population'].iloc[0] / adj_msa_pop

    new_df = DataFrame()    
    for county, county_sent in sent.groupby('county'):
        new_df = concat([new_df, county_sent])

    grouped = sent[sent.msa==msa].groupby('county')
    for county, county_sent in grouped:
        
        irradiance = read_csv('../data/weather/'+msa+'_'+'_'.join(county.split(' '))+'_irradiance_'+str(ANALYSIS_YEAR)+'.csv')

        print '\t',county
        county_df = DataFrame(columns = [], index=county_sent.index) 

        county_df['county_weight'] = county_weighting[county]
        county_df['county_msa_weight'] = all_msa_county_weighting[county + ':' + msa]
        county_df['affect_mean'] = county_sent.affect_mean
        county_df['log_affect_mean'] = log(county_sent.affect_mean)
        county_df['num_tweets'] = county_sent.num_tweets
        county_df['log_num_tweets'] = log(county_sent.num_tweets)
        county_df['county'] = repeat(county, len(county_sent))

        for col in ind_holiday_regressors.columns: county_df[col.split('_')[0]] = ind_holiday_regressors[col]
        for col in payday_regressors.columns:    county_df[col] = payday_regressors[col]
        for col in days_of_week_regressors.columns:    county_df[col] = days_of_week_regressors[col]
        for col in month_of_year_regressors.columns:    county_df[col] = month_of_year_regressors[col]

        county_df = county_df[~isnan(county_df.affect_mean)]
        county_df['sports_sum_pe_with_na'] = pd_zscore(sports.sum_pe_with_na.shift(1))
        county_df['raw_sports_sum_pe_with_na'] = sports.sum_pe_with_na.shift(1)
        county_df['sports_composite'] = pd_zscore(sports.sports_composite.shift(1))
        county_df['sports_p_win'] = (sports.p_win.shift(1))
        county_df['dni'] = pd_zscore(irradiance.dni)
        county_df['dni_pe'] = pd_zscore(irradiance.dni_pe)
        county_df['raw_dni_pe'] = irradiance.dni_pe
        county_df['date'] = county_df.index
        msa_regress_df = concat([msa_regress_df, county_df])  

    msa_regress_df.index = msa_regress_df.date
    msa_regress_df.to_csv('../data/regress/sent_regress_input/'+msa+'_sent_regress_'+str(ANALYSIS_YEAR)+'.csv')

    msa_regress_df['msa'] = msa
    regress_df = concat([regress_df, msa_regress_df])  

regress_df.to_csv('../data/regress/sent_regress_input/all_msa_sent_regress_'+str(ANALYSIS_YEAR)+'.csv')





        
