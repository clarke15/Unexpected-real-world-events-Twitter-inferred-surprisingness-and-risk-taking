# Import libraries
import torch
from transformers import AutoModel, AutoTokenizer, pipeline, AutoModelForSequenceClassification
from TweetNormalizer import normalizeTweet
import pandas as pd
import re
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import numpy as np
from pysentimiento_master.pysentimiento.preprocessing import preprocess_tweet
from tqdm import tqdm

# FUNCTION FOR PREPROCESSING TWEETS
def pysent_clean_tweet(unclean_data):
    
    # Make a copy of the unclean data 
    data = unclean_data.copy()
    
    # Remove stopwords and then lemmatise 
    stop = set(stopwords.words("english"))
    lemmatizer = WordNetLemmatizer()
    
    # Index of the "text" column for use in .iloc[] below
    text_col_index = data.columns.get_loc("text")
    
    # Removing unwanted text features
    for i in range(len(data.loc[:,"text"])):
        
        # Preprocess the data using the pysentimiento package 
        data.iloc[i,text_col_index] = preprocess_tweet(data.iloc[i,text_col_index], lang = "en")
        
        # Remove stopwords and lemmatise tweets
        tokenised_tweet = word_tokenize(data.iloc[i,text_col_index])
        tokenised_without_stop = [word for word in tokenised_tweet if not word in stop]
        # lemmatise tokenised sentences without stops words in
        # Consider using default pos tagging of 'V' as seems to be most effective and does not take long to do
        lemmatised_output = (" ").join(lemmatizer.lemmatize(word) for word in tokenised_without_stop)

        # Remove spaces between punctuatioms e.g. ! ! or : ) - regex looks before and after a whitespace,
        # if it is not an alphanumeric it removes the space
        lemmatised_output = re.sub(r"(?<![a-zA-Z\d\s])\s(?![a-zA-Z\d\s])", "", lemmatised_output)
        # Remove spaces between @ sign and USER
        lemmatised_output = re.sub(r"(?<=@)\s", "", lemmatised_output)
        

        
    return(data)


# FUNCION THAT TAKES A DATAFRAME AS INPUT AND OUTPUTS IT WITH LABELS AND SCORES
def get_sentiment(df):
    
    # create the sentiment analyser pipeline
    model = AutoModelForSequenceClassification.from_pretrained("pysentimiento/robertuito-sentiment-analysis")
    tokenizer = AutoTokenizer.from_pretrained("pysentimiento/robertuito-sentiment-analysis")
    
	# Tryy wit "text-classification"
    classifier = pipeline("sentiment-analysis", model = model, tokenizer = tokenizer)
    
    # Take a list of the tweets and find the sentiment and score of each 
    tweets = list(df["text"])
    
    labels = []
    scores = []
    
    for sent in tqdm(tweets):
        
        try:
            results = classifier(sent)
            #Assign label to label
            #df.at[i,"label"] = results[0][0]["label"]
            #df.at[i,"score"] = results[0][0]["score"]
            
            labels.append(results[0]["label"])
            scores.append(results[0]["score"])
        # Get the exception to print out the error and for which team/time then pass to next month
        except:
        # except Exception as e:
        #     print(e)
            labels.append("DELETE")
            scores.append(100000)
            print("The tweet was: ",sent)
            pass

    # Create an empty col for label and score
    df = df.assign(label = labels)
    df = df.assign(score = scores)
    
    return df
    

    
    
    
    
    
 # FUNCTION THAT COMBINES THE pysent_clean_data and get_sentiment and saves the output as a csv file
def get_pysent_scores(unclean_data, file_name):
    
    # clean the data
    clean_data = pysent_clean_tweet(unclean_data)
    
    # Get the sentiment scores of the data 
    data = get_sentiment(clean_data)
    
    # Save the df with the sent/score down as a csv 
    data.to_csv(r"C:\Users\clark\OneDrive - University of Warwick\Diss\2. Analysis\Data\pysent_scores\{}.csv".format(file_name))