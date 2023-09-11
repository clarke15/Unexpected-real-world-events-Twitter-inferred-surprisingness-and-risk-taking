import pandas as pd
import numpy as np

# A function that takes a pysent csv file as input and adds a column with a simple compound score
def get_compound_pysent_score(df):
    
    # Create an empty compoun pysent column
    df["compound pysent"] = np.nan
    # Set the neutral scores to zero
    df.loc[df["label"] == "NEU", "compound pysent"] = 0
    # Set the postive to 1 * prob
    df.loc[df["label"] == "POS", "compound pysent"] = df["score"]*1
    # Set the negative to -1 * prob
    df.loc[df["label"] == "NEG", "compound pysent"] = df["score"]*-1
    
    return df