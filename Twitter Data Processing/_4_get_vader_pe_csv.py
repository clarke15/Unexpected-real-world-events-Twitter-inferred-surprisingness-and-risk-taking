import pandas as pd
import numpy as np
import datetime
from calendar import monthrange
from _1_get_vader_scores import *
from _3_get_prediction_errors import *


# Inputs: Year, VADER; dataframe with daily sent scores (e.g. from get_vader_score function)
# Outputs: vader_sent_and_pe_scores - Contains a daily mean sentiment for each score, and PE for each score.  
def get_mean_and_pe_vader_scores(year, team_df, score_name = "VADER"):
    
    # Create VADER sentiment scores for each tweet
    team_df = get_vader_scores(team_df)
    
    # vader_sent_and_pe_scores: To be populated
    vader_sent_and_pe_scores = pd.DataFrame(columns = ["date", "VADER", "PE_Vader"])

    # Change the "created_at" column to type date
    team_df["created_at"] = pd.to_datetime(team_df["created_at"]).dt.date

    row_index = 0

    # Iterate through each month
    for month in range(1,13):
        # How many days were in that month for the year
        num_days = monthrange(year, month)[1]

        # Iterate through each day of the month and calculate the mean sentiment score
        for day  in range(1,num_days + 1):



            # The current date
            date_ = datetime.date(year,month, day) 
            # Select all rows of tweets for that day
            rows = team_df[team_df['created_at'] == date_]

            mean_daily_sentiment = np.mean(rows[score_name])

            # display(rows)
            #print("MEAN SENTIMENT: ",str(mean_daily_sentiment))

            # UPDATE vader_sent_and_pe_scores table:

            # Update the date
            vader_sent_and_pe_scores.at[row_index, "date"] = date_
            # Update mean Vader
            vader_sent_and_pe_scores.at[row_index, score_name] = mean_daily_sentiment
            
	     # If the date is empty (as is the case with 16/9/12 knicks) set it equal to prior day mean
            if len(rows) == 0:
                vader_sent_and_pe_scores.at[row_index, score_name] = vader_sent_and_pe_scores.at[row_index - 1, score_name] 
            

            

            

            # rows is used to index the table
            row_index += 1
        
    # Create prediction errors 
    # def get_prediction_error(column_of_scores, column_name, alpha = 0.1)
    vader_sent_and_pe_scores["PE_Vader"] = get_prediction_error(vader_sent_and_pe_scores["VADER"])
    
    
    return vader_sent_and_pe_scores 



# Input: the number year and string team (NOTE: input df must be from the FINAL Tweets folder)
# Output: Saves down a csv with date, prediction and prediction error of Vader sentiment scores
def output_vader_pe_csv(year, team):
    
    # Load in the team dataframe
    tweets_file_path = r"C:\Users\clark\OneDrive - University of Warwick\Diss\1. Twitter API\Data\Data - Scraped Tweets\FINAL Tweets"
    tweets_file = "\{}_{}.csv".format(team, year)
    
    #print(tweets_file_path + tweets_file)
    team_df = pd.read_csv(tweets_file_path + tweets_file)
    
    # Run the get_mean_and _pe_vader_scores
    data = get_mean_and_pe_vader_scores(year, team_df)
    
    # Save the data down in C:\Users\clark\OneDrive - University of Warwick\Diss\2. Analysis\Data\vader_pe_scores
    file_path = r"C:\Users\clark\OneDrive - University of Warwick\Diss\2. Analysis\Data\vader_pe_scores"
    file_name = "\{}_{}_vader_pe.csv".format(year,team)
    data.to_csv(file_path + file_name)