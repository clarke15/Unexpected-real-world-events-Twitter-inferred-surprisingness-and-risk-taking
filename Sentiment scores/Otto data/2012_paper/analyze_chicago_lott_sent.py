import gzip, os
from numpy import *
from pylab import *
from scipy.stats import zscore, pearsonr, linregress, scoreatpercentile
from pandas import DataFrame, date_range, Series, datetools, tseries, rolling_mean, rolling_std, ols, concat, HDFStore, merge, read_csv, read_pickle, to_datetime
#import statsmodels.api as sm
import urllib2, csv, re, cPickle, calendar, time
from datetime import datetime
import statsmodels.api as sm
import statsmodels.formula.api as smf

def pd_zscore(x): return (x - mean(x)) / std(x)

DAY_NAMES = ['MON','TUE','WED','THU','FRI','SAT','SUN']
MONTH_NAMES = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC ']

DATE_RANGES = {2013: date_range(datetime(2013, 1, 1), datetime(2013, 12,31))}
ANALYSIS_YEAR = 2013
analysis_range = DATE_RANGES[ANALYSIS_YEAR]

lott = read_csv('../data/lottery/chicago_'+str(ANALYSIS_YEAR) + '_lottery.csv')
lott.ZIP = lott.ZIP.astype(int)

all_zips = lott.ZIP.unique()

county_demographics = read_pickle('../data/misc/extended_county_demographics.dat')
demographics = read_pickle('../data/misc/chicago_demographics.dat')

demographics = demographics[demographics.population >= 15000]

bad_zips = filter(lambda x:x not in demographics.ZIP, all_zips)
lott = lott.loc[~lott['ZIP'].isin(bad_zips)]

sports = read_csv('../data/sports/chicago_sports_'+str(ANALYSIS_YEAR)+'.csv')
irradiance = read_csv('../data/weather/chicago_irradiance_'+str(ANALYSIS_YEAR)+'.csv')

weather = DataFrame.from_csv('../data/weather/chicago_weather.csv', index_col='EST')
weather['PrecipitationIn'] = weather.PrecipitationIn.replace('T', '0')
weather['PrecipitationIn'] = weather.PrecipitationIn.astype(float)

#demographics = merge(demographics, zoning, on='ZIP')
demographics.index = demographics.ZIP.astype(int)

storm_regressor = Series(data=zeros(len(analysis_range)),index=analysis_range)
hurricane_regressor = Series(data=zeros(len(analysis_range)),index=analysis_range)

storm_regressor = Series(data=zeros(len(analysis_range)),index=analysis_range)
storm_regressor.ix[ weather[logical_and(map(lambda x:'Snow' in str(weather.Events.ix[x]), weather.index), 
                                        weather.MeanVisibilityMiles < 5)].index.tolist() ] = 1

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



print len(unique(lott.ZIP)), 'ZIPs total'


regress_df = DataFrame() 
grouped = lott.groupby('ZIP')
for zip, zip_lott in grouped:
    print '***', zip, demographics.ix[zip]['desc'], 'pop:', demographics.ix[zip]['population_over_18']

    zip_df = DataFrame(columns = [], index=analysis_range)
    zip_df['purchase'] = ((zip_lott[zip_lott.game=='pick3']['sales_amount'] + zip_lott[zip_lott.game=='pick4']['sales_amount'] + zip_lott[zip_lott.game=='luckyday']['sales_amount'] + zip_lott[zip_lott.game=='lotto']['sales_amount'])/ float(demographics.ix[zip]['population_over_18']))
    zip_df['log_purchase'] = log((zip_lott[zip_lott.game=='pick3']['sales_amount'] + zip_lott[zip_lott.game=='pick4']['sales_amount'] + zip_lott[zip_lott.game=='luckyday']['sales_amount'] + zip_lott[zip_lott.game=='lotto']['sales_amount'])/float(demographics.ix[zip]['population_over_18']))
    zip_df['ZIP'] = repeat(zip, len(zip_df)) 
    zip_df['sports_sum_pe_with_na'] = pd_zscore(sports.sum_pe_with_na.shift(1))
    zip_df['dni_pe'] = pd_zscore(irradiance.dni_pe)
    zip_df['STORM'] = storm_regressor
 
    for col in ind_holiday_regressors.columns: zip_df[col.split('_')[0]] = ind_holiday_regressors[col]
    for col in payday_regressors.columns:    zip_df[col] = payday_regressors[col]
    for col in days_of_week_regressors.columns:    zip_df[col] = days_of_week_regressors[col]
    for col in month_of_year_regressors.columns:    zip_df[col] = month_of_year_regressors[col]

    if((sum(isinf(zip_df['log_purchase'])) > 0) or (sum(isnan(zip_df['log_purchase'])) > 0)):
        print '\t missing' ,sum(isinf(zip_df['log_purchase'])) + sum(isnan(zip_df['log_purchase'])), 'observations'

    regress_df = concat([regress_df, zip_df])  


regress_df = regress_df[~isinf(regress_df['log_purchase'])]
regress_df = regress_df[~isnan(regress_df['log_purchase'])]
regress_df.to_csv('regress/lott_sent_regress_input/chicago_lott_regress_input_'+str(ANALYSIS_YEAR)+'.csv')

sent = read_csv('regress/sent_regress_input/chicago_sent_regress_'+str(ANALYSIS_YEAR)+ '.csv')
sent.index = to_datetime(sent.date)


lott_sent_regress_df = DataFrame()
grouped = lott.groupby('ZIP')
for zip, zip_lott in grouped:
    county = demographics[demographics['ZIP']==zip].iloc[0].desc.split(':')[0]

    if(county not in sent.county.unique()):
        continue
       
    print '***', zip, demographics.ix[zip]['desc'], len(sent[sent.county==county].affect_mean), 'affect days'

    zip_df = DataFrame(columns = [], index=analysis_range)
    zip_df['county']=  repeat(county, len(zip_df))
    zip_df['affect_mean'] = pd_zscore(sent[sent.county==county]['affect_mean'])
    zip_df['purchase'] = ((zip_lott[zip_lott.game=='pick3']['sales_amount'] + zip_lott[zip_lott.game=='pick4']['sales_amount'] + zip_lott[zip_lott.game=='luckyday']['sales_amount'] + zip_lott[zip_lott.game=='lotto']['sales_amount'])/ float(demographics.ix[zip]['population_over_18']))
    zip_df['log_purchase'] = log((zip_lott[zip_lott.game=='pick3']['sales_amount'] + zip_lott[zip_lott.game=='pick4']['sales_amount'] + zip_lott[zip_lott.game=='luckyday']['sales_amount'] + zip_lott[zip_lott.game=='lotto']['sales_amount'])/ float(demographics.ix[zip]['population_over_18']))
    zip_df['ZIP'] = repeat(zip, len(zip_df)) 
    zip_df['sports_sum_pe_with_na'] = pd_zscore(sports.sum_pe_with_na.shift(1))
    zip_df['dni_pe'] = pd_zscore(irradiance.dni_pe)
    zip_df['STORM'] = storm_regressor
 
    for col in ind_holiday_regressors.columns: zip_df[col.split('_')[0]] = ind_holiday_regressors[col]
    for col in payday_regressors.columns:    zip_df[col] = payday_regressors[col]
    for col in days_of_week_regressors.columns:    zip_df[col] = days_of_week_regressors[col]
    for col in month_of_year_regressors.columns:    zip_df[col] = month_of_year_regressors[col]

    if((sum(isinf(zip_df['log_purchase'])) > 0) or (sum(isnan(zip_df['log_purchase'])) > 0)):
        print '\t missing' ,sum(isinf(zip_df['log_purchase'])) + sum(isnan(zip_df['log_purchase'])), 'observations'

    lott_sent_regress_df = concat([lott_sent_regress_df, zip_df])  

lott_sent_regress_df = lott_sent_regress_df[~isinf(lott_sent_regress_df['log_purchase'])]
lott_sent_regress_df = lott_sent_regress_df[~isnan(lott_sent_regress_df['log_purchase'])]
lott_sent_regress_df.to_csv('regress/lott_sent_regress_input/chicago_lott_sent_regress_input_'+str(ANALYSIS_YEAR)+'.csv')



