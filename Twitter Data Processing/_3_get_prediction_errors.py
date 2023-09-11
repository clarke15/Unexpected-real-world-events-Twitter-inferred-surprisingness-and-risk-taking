import pandas as pd


# Inputs: column of scores (e.g. df["col name"]), "col name" 
# Outputs: Pandas series of prediction errors
def get_prediction_error(column_of_scores,  alpha = 0.1):
    
    # Get column index for .iloc()
    # col_index = column_of_scores.columns.get_loc(column_name)
    
    # Create a pandas df to store p_t and pe in
    pe_df = pd.DataFrame(columns = ["P_t", "PE"])
    
    # Initialise p_t  as the same as the first entry
    p_t = column_of_scores.iloc[0]
    
    
    # Iterate through all rows
    for t in range(len(column_of_scores)):
        
        # Access the actual outcome for t
        actual_outcome = column_of_scores.iloc[t]
        
        # Calculate prediction error
        pe = actual_outcome - p_t 
        
        # Update pe_df with current p_t and PE values
        pe_df.at[t, "P_t"] = p_t
        pe_df.at[t, "PE"] = pe
        
        # Update the values of p_t for next iteration (i.e. p_t+1)
        p_t = p_t + alpha*(actual_outcome - p_t)
        
    return pe_df.loc[:,"PE"]
        