# import packages
import pandas as pd
import numpy as np
import datetime
from calendar import monthrange
from _3_get_prediction_errors import *



# Inputs: Year, the dataframe with daily sent scores (e.g. from distil_bert function)
# Outputs: distilbert_sent_and_pe_scores - Contains a daily mean sentiment and PE  
def get_mean_and_pe_distilbert_scores(year, team_df, score_name= "score"):
    
    
    # distilbert_sent_and_pe_scores: To be populated
    distilbert_sent_and_pe_scores = pd.DataFrame(columns = ["date", "mean_distilbert", "PE_distilbert"])

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
#             print(date_)
#             print(mean_daily_sentiment)

            # display(rows)
            #print("MEAN SENTIMENT: ",str(mean_daily_sentiment))

            # UPDATE distilbert_sent_and_pe_scores table:

            # Update the date
            distilbert_sent_and_pe_scores.at[row_index, "date"] = date_
            # Update mean distilbert
            distilbert_sent_and_pe_scores.at[row_index, "mean_distilbert"] = mean_daily_sentiment
            
            # If the date is empty (as is the case with 16/9/12 knicks) set it equal to prior day mean
            if len(rows) == 0:
                distilbert_sent_and_pe_scores.at[row_index, "mean_distilbert"] = distilbert_sent_and_pe_scores.at[row_index - 1, "mean_distilbert"] 
            
            # rows is used to index the table
            row_index += 1
        
    # Create prediction errors 
    distilbert_sent_and_pe_scores["PE_distilbert"] = get_prediction_error(distilbert_sent_and_pe_scores["mean_distilbert"])
    
    
    return distilbert_sent_and_pe_scores 


def output_distilbert_pe_csv(year, team):
    
    # Load in the team from the yearly distilbert scores folder
    tweets_file_path = r"C:\Users\clark\OneDrive - University of Warwick\Diss\2. Analysis\Data\distilbert_scores"
    tweets_file = "\{}_{}_distilbert_surprise.csv".format(year, team)
    
    # Load in the distilbert yearly scores dataframe
    team_df = pd.read_csv(tweets_file_path + tweets_file)
    
    # Now we have the compound score in the team_df
    # Carry out the get_mean_and_pe_distilbert_scores, which looks at the compound score
    mean_pe_distilbert = get_mean_and_pe_distilbert_scores(year, team_df)
    
    # Save mean_pe_distilbert in the distilbert_pe_scores
    save_down_dir = r"C:\Users\clark\OneDrive - University of Warwick\Diss\2. Analysis\Data\distilbert_pe_scores"
    save_down_file = "\{}_{}_distilbert_pe.csv".format(year,team)
    
    mean_pe_distilbert.to_csv(save_down_dir + save_down_file)

