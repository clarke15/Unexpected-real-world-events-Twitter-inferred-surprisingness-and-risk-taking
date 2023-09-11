import gzip, os
from numpy import *
from pylab import *
from scipy.stats import zscore, pearsonr, linregress, scoreatpercentile
from pandas import DataFrame, date_range, Series, datetools, tseries, rolling_mean, rolling_std, ols, concat, HDFStore, merge, read_csv, read_pickle, to_datetime
import urllib2, csv, re, cPickle, calendar, time, copy
from datetime import datetime
import statsmodels.api as sm
import statsmodels.formula.api as smf

def pd_zscore(x): return (x - mean(x)) / std(x)

DAY_NAMES = ['MON','TUE','WED','THU','FRI','SAT','SUN']
MONTH_NAMES = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC ']


DATE_RANGES = {2012: date_range(datetime(2012, 1, 1), datetime(2012, 12,31)),
               2013: date_range(datetime(2013, 1, 1), datetime(2013, 12,31))}
ANALYSIS_YEAR = 2013
analysis_range = DATE_RANGES[ANALYSIS_YEAR]

lott = read_csv('../data/lottery/nyc_'+str(ANALYSIS_YEAR)+'_lottery.csv')


sports = read_csv('../data/sports/nyc_sports_'+str(ANALYSIS_YEAR)+'.csv')
irradiance = read_csv('../data/weather/nyc_irradiance_'+str(ANALYSIS_YEAR)+'.csv')


all_zips = lott.ZIP.unique()

county_demographics = read_pickle('../data/misc/extended_county_demographics.dat')
demographics = read_pickle('../data/misc/nyc_demographics.dat')
demographics['z_ses'] = zscore(demographics.ses)

jackpot = DataFrame({'date':analysis_range})
jackpot.index = jackpot.date

weather = DataFrame.from_csv('../data/weather/nyc_weather.csv', index_col='EST')
weather['PrecipitationIn'] = weather.PrecipitationIn.replace('T', '0')
weather['PrecipitationIn'] = weather.PrecipitationIn.astype(float)
weather['temp_exp_avg'] = Series(index=weather.index) 
weather['temp_pe'] = Series(index=weather.index) 
avg_temp = weather.ix[datetime(2010,12,31)]['MeanTemperatureF']


hurricanes = {  'irene':[datetime(2011,8,27), datetime(2011,8,28), datetime(2011,8,29)],
                'sandy': date_range(datetime(2012,10,29),datetime(2012,11,1)) }
storm_regressor = Series(data=zeros(len(DATE_RANGES[ANALYSIS_YEAR])),index=DATE_RANGES[ANALYSIS_YEAR])
hurricane_regressor = Series(data=zeros(len(DATE_RANGES[ANALYSIS_YEAR])),index=DATE_RANGES[ANALYSIS_YEAR])

for name, dates in hurricanes.iteritems():
    for date in dates:
        hurricane_regressor.ix[date] = 1

temp_weather = weather[weather.index.year == ANALYSIS_YEAR]
storm_regressor = Series(data=zeros(len(DATE_RANGES[ANALYSIS_YEAR])),index=DATE_RANGES[ANALYSIS_YEAR])

storm_day_indices = temp_weather[logical_and(map(lambda x:'Snow' in str(temp_weather.Events.ix[x]), temp_weather.index), 
                                        temp_weather.MeanVisibilityMiles < 5)].index.tolist()
storm_regressor.ix[storm_day_indices ] = 1

new_storm_regressor = copy.deepcopy(storm_regressor)
for i in storm_regressor.index:
    if(storm_regressor.get_value(i)==1): 
        new_storm_regressor.set_value(i+1,1)

storm_regressor = new_storm_regressor


days_of_week_regressors = DataFrame(index=analysis_range)
for day_of_week in range(7):
    days_of_week_regressors[DAY_NAMES[day_of_week]] = map(int, analysis_range.dayofweek==day_of_week)

month_of_year_regressors = DataFrame(index=analysis_range)
for month_of_year in range(1,13):
    month_of_year_regressors[MONTH_NAMES[month_of_year-1]] = map(int, analysis_range.month==month_of_year)

week_of_year_regressors = DataFrame(index=analysis_range)
for week_of_year in range(1,53):
    week_of_year_regressors['WEEK_'+str(week_of_year)] = map(int, analysis_range.week==week_of_year)


csv_file = open('../data/misc/holidays_sent.csv', 'rU')
reader = csv.DictReader(csv_file)
holidays = {}
for row in reader:
    holidays[datetools.to_datetime(row['date'], errors='raise')] = row['holiday']+'_'+str(datetools.to_datetime(row['date'], errors='raise').year)[-2:]

holiday_regressor = Series(index=DATE_RANGES[ANALYSIS_YEAR], data=zeros(len(DATE_RANGES[ANALYSIS_YEAR])))
for date in holiday_regressor.index:
    if(date in holidays.keys()): holiday_regressor[date] = 1

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

lott['composite'] = (lott['Take5'] + lott['Win4Day'] + lott['Win4Eve'] +lott['QuickDraw'] + \
                         lott['Pick10'] +lott['NumbersDay'] + lott['NumbersEve'] ) #/ lott['RetailerCount']


lott['composite_per_capita'] = zeros(lott.shape[0])
grouped = lott.groupby('ZIP')
for zip, zip_lott in grouped:
    lott.ix[lott.ZIP==zip,'composite_per_capita'] = lott[lott.ZIP==zip]['composite'] / demographics.ix[zip]['population_over_18']


if(ANALYSIS_YEAR == 2012):
    for zip in lott.ZIP.unique():
        zip_df = lott[lott.ZIP == zip]
        pre_storm_mean = mean(zip_df[:datetime(2012, 10,27)].composite_per_capita)

        storm_mean = mean(zip_df[datetime(2012, 11,1):datetime(2012, 12,31)].composite_per_capita)
        if(storm_mean/pre_storm_mean < .75):
            print 'DROPPING FOR SANDY:', zip, demographics.ix[zip]['desc'], demographics.ix[zip]['population'], storm_mean/pre_storm_mean
            lott = lott[lott.ZIP != zip]

print len(unique(lott.ZIP)), 'ZIPs total'
zip_to_county = DataFrame(columns=['ZIP', 'county'])
zip_to_county['county'] = map(lambda x: {'Manhattan':'new york',
                                           'Staten Island':'richmond',
                                           'Bronx':'bronx',
                                           'Queens':'queens',
                                           'Brooklyn':'kings'}[x.split(':')[0]], demographics.desc)
zip_to_county['ZIP'] = demographics.index


lott['date'] = lott.index
lott = lott.merge(zip_to_county, on='ZIP')

sent = read_csv('../data/regress/sent_regress_input/nyc_metro_sent_regress_'+str(ANALYSIS_YEAR)+ '.csv')
sent.date = to_datetime(sent.date)

lott_sent = lott.merge(sent, on=['date', 'county'])
lott_sent.index = lott_sent.date




lott_sent_regress_df = DataFrame() 
lott_sent['composite_per_capita'] = zeros(lott_sent.shape[0])
grouped = lott_sent.groupby('ZIP')
for zip, zip_lott in grouped:
    print '***', zip, demographics.ix[zip]['desc'], len(sent[sent.county==zip_lott.county[0]].affect_mean), 'affect days'

    lott_sent.ix[lott_sent.ZIP==zip,'composite_per_capita'] = lott_sent[lott_sent.ZIP==zip]['composite'] / demographics.ix[zip]['population_over_18']
    zip_df = DataFrame(columns = [], index=zip_lott.index) 
    zip_df['ZIP'] = repeat(zip, len(zip_lott))
    zip_df['z_ses'] = repeat(demographics.ix[zip]['ses'], len(zip_lott))
    zip_df['county'] = zip_lott['county']
    zip_df['purchase'] = zip_lott['composite'] / demographics.ix[zip]['population_over_18'] 
    zip_df['log_purchase'] = log(zip_lott['composite'] / demographics.ix[zip]['population_over_18'] )
    zip_df['affect_mean'] = pd_zscore(zip_lott['affect_mean'])
    zip_df['STORM'] = storm_regressor
    zip_df['HURRICANE'] = hurricane_regressor
    zip_df['HOLIDAYS'] = holiday_regressor    
    zip_df['BAD_WEATHER'] = storm_regressor + hurricane_regressor
    zip_df['sports_sum_pe_with_na'] = pd_zscore(sports.sum_pe_with_na.shift(1))
    zip_df['dni_pe'] = pd_zscore(irradiance.dni_pe)

    for col in ind_holiday_regressors.columns: zip_df[col.split('_')[0]] = ind_holiday_regressors[col]
    for col in payday_regressors.columns:    zip_df[col] = payday_regressors[col]
    for col in days_of_week_regressors.columns:    zip_df[col] = days_of_week_regressors[col]
    for col in month_of_year_regressors.columns:    zip_df[col] = month_of_year_regressors[col]

    if((sum(isinf(zip_df['log_purchase'])) > 0) or (sum(isnan(zip_df['log_purchase'])) > 0)):
        print '\t missing' ,sum(isinf(zip_df['log_purchase'])) + sum(isnan(zip_df['log_purchase'])), 'observations'

    if(ANALYSIS_YEAR == 2012):
        zip_df = concat([ zip_df.ix[date_range(datetime(2012,1,1),datetime(2012,10,27))],
                          zip_df.ix[date_range(datetime(2012,11,4),datetime(2012,12,31))]])


    for col in zip_df.columns:
        if(zip_df[col].dtype != dtype('O')):
            assert(isnan(zip_df[col]).all() == False)

    lott_sent_regress_df = concat([lott_sent_regress_df, zip_df])  


lott_sent_regress_df = lott_sent_regress_df[~isinf(lott_sent_regress_df['log_purchase'])]
lott_sent_regress_df = lott_sent_regress_df[~isnan(lott_sent_regress_df['log_purchase'])]

lott_sent_regress_df.to_csv('regress/lott_sent_regress_input/nyc_lott_sent_regress_input_'+str(ANALYSIS_YEAR)+'.csv')


lott_regress_df = DataFrame() 
lott.index = lott.date
lott['composite_per_capita'] = zeros(lott.shape[0])
grouped = lott.groupby('ZIP')
for zip, zip_lott in grouped:
    print '***', zip, demographics.ix[zip]['desc'], len(zip_lott), 'days'

    lott.ix[lott.ZIP==zip,'composite_per_capita'] = lott[lott.ZIP==zip]['composite'] / demographics.ix[zip]['population_over_18']
    zip_df = DataFrame(columns = [], index=zip_lott.index) 
    zip_df['ZIP'] = repeat(zip, len(zip_lott))
    zip_df['z_ses'] = repeat(demographics.ix[zip]['ses'], len(zip_lott))
    zip_df['purchase'] = zip_lott['composite'] / demographics.ix[zip]['population_over_18'] 
    zip_df['log_purchase'] = log(zip_lott['composite'] / demographics.ix[zip]['population_over_18'] )
    zip_df['STORM'] = storm_regressor
    zip_df['HURRICANE'] = hurricane_regressor
    zip_df['HOLIDAYS'] = holiday_regressor    
    zip_df['BAD_WEATHER'] = storm_regressor + hurricane_regressor
    zip_df['sports_sum_pe_with_na'] = pd_zscore(sports.sum_pe_with_na.shift(1))
    zip_df['dni_pe'] = pd_zscore(irradiance.dni_pe)

    for col in ind_holiday_regressors.columns: zip_df[col.split('_')[0]] = ind_holiday_regressors[col]
    for col in payday_regressors.columns:    zip_df[col] = payday_regressors[col]
    for col in days_of_week_regressors.columns:    zip_df[col] = days_of_week_regressors[col]
    for col in month_of_year_regressors.columns:    zip_df[col] = month_of_year_regressors[col]

    if((sum(isinf(zip_df['log_purchase'])) > 0) or (sum(isnan(zip_df['log_purchase'])) > 0)):
        print '\t missing' ,sum(isinf(zip_df['log_purchase'])) + sum(isnan(zip_df['log_purchase'])), 'observations'

    if(ANALYSIS_YEAR == 2012):
        zip_df = concat([ zip_df.ix[date_range(datetime(2012,1,1),datetime(2012,10,27))],
                          zip_df.ix[date_range(datetime(2012,11,4),datetime(2012,12,31))]])

    for col in zip_df.columns:
        if(zip_df[col].dtype != dtype('O')):
            assert(isnan(zip_df[col]).all() == False)

    lott_regress_df = concat([lott_regress_df, zip_df])  


lott_regress_df = lott_regress_df[~isinf(lott_regress_df['log_purchase'])]
lott_regress_df = lott_regress_df[~isnan(lott_regress_df['log_purchase'])]

lott_regress_df.to_csv('regress/lott_sent_regress_input/nyc_lott_regress_input_'+str(ANALYSIS_YEAR)+'.csv')


