# Import packages
import pandas as pd
import vaderSentiment
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


# Function for cleaning tweets
# vader_cleaning() returns the original input data (with tweet id and timestamp) but with text suitable for VADER
# data - column must have "text" 

def vader_cleaning(unclean_data):
    
    # Create a copy of the data frame
    data = unclean_data.copy()
    
    # Remove stopwords and then lemmatise 
    stop = set(stopwords.words("english"))
    lemmatizer = WordNetLemmatizer()
    
    # Index of the "text" column for use in .iloc[] below
    text_col_index = data.columns.get_loc("text")

    # Removing unwanted text features
    for i in range(len(data.loc[:,"text"])):
        
        
        # Removing web links
        data.iloc[i,text_col_index] = re.sub(r"http\S+", "", data.iloc[i,text_col_index])
        data.iloc[i,text_col_index] = re.sub(r"www\S+", "", data.iloc[i,text_col_index])

        # Removing tags - i.e. '@' followed by any number of letters, numbers and symbols
        data.iloc[i,text_col_index] =re.sub(r"@[A-Za-z0-9_]+", "", data.iloc[i,text_col_index])

        # Removing hashtags - can think about whether to keep the text or remove entirely
        data.iloc[i,text_col_index] =re.sub(r"#[A-Za-z0-9_]+", "", data.iloc[i,text_col_index])


        # Remove stopwords and lemmatise tweets
        tokenised_tweet = word_tokenize(data.iloc[i,text_col_index])
        tokenised_without_stop = [word for word in tokenised_tweet if not word in stop]
        # lemmatise tokenised sentences without stops words in
        # Consider using default pos tagging of 'V' as seems to be most effective and does not take long to do
        lemmatised_output = (" ").join(lemmatizer.lemmatize(word) for word in tokenised_without_stop)

        # Remove spaces between punctuatioms e.g. ! ! or : ) - regex looks before and after a whitespace,
        # if it is not an alphanumeric it removes the space
        lemmatised_output = re.sub(r"(?<![a-zA-Z\d\s])\s(?![a-zA-Z\d\s])", "", lemmatised_output)


        # Reassign to the data
        data.iloc[i,text_col_index] = lemmatised_output
    
    return(data)


# Create an instance of the VADER sentiment analyser
sid_analyzer = SentimentIntensityAnalyzer()

# This returns a sentiment score for either a positive, negative, neutral or compound sentiment
def get_sentiment(text:str, analyser,desired_type:str='compound'):
    # Get sentiment from text
    sentiment_score = analyser.polarity_scores(text)
    return sentiment_score[desired_type]

# This bolts the score on to the existing data 
def get_sentiment_scores(df,data_column):
#     df[f'{data_column} Positive Sentiment Score'] = df.iloc[:,data_column].astype(str).apply(lambda x: get_sentiment(x,sid_analyzer,'pos'))
#     df[f'{data_column} Negative Sentiment Score'] = df.iloc[:,data_column].apply(lambda x: get_sentiment(x,sid_analyzer,'neg'))
#     df[f'{data_column} Neutral Sentiment Score'] = df.iloc[:,data_column].astype(str).apply(lambda x: get_sentiment(x,sid_analyzer,'neu'))
    df["VADER"] = df.iloc[:,data_column].astype(str).apply(lambda x: get_sentiment(x,sid_analyzer,'compound'))
    return df


###############################################################
# Function that pulls the VADER sentiment analysis together 
# Returns vaderd cleaned data (tweet_id, text, created_at) as well as compound sentiment vader score 
def get_vader_scores(unclean_data):
    
    # Clean the data 
    clean_data = vader_cleaning(unclean_data)
    
    # Analyse the data
    text_col_index = clean_data.columns.get_loc("text")
    data_with_vader_score = get_sentiment_scores(clean_data, text_col_index)
    
    return(data_with_vader_score)