# Load in libraries

library("xlsx")

# install.packages("rempsyc", repos = c(
#  rempsyc = "https://rempsyc.r-universe.dev",
# CRAN = "https://cloud.r-project.org"))
# library(rempsyc)


# Read in the data
data <- read.csv("aggregate_regression_input_7.csv")
# Data that excludes days with zero prediction error
data_no_zeros <- read.csv("aggregate_regression_input_no_zero_pe.csv")


colnames(data) #head(data)
colnames(data_no_zeros)

# Create a variable with the nuisance variables in

ivs = '+ TUE + WED + THU + FRI + SAT + SUN + FEB + MAR + APR + MAY +
JUN + JUL + AUG + SEP + OCT + NOV + DEC + FIRST_OF_MONTH +
FIFTEENTH_OF_MONTH + HURRICANE + INDEPENDENCEDAY + THANKSGIVING +
CHRISTMASDAY + DAYAFTERCHRISTMAS + LABORDAY + EASTER + NEWYEARSDAY +
COLUMBUSDAY + MEMORIALDAY + BIRTHDAYOFMARTINLUTHERKINGJR + VETERANSDAY +
WASHINGTONSBIRTHDAY + VALENTINESDAY'

# Create a vector to iterate through the lm_output function
sent_scores <- c("norm_sum_vader", "norm_sum_pysent", "norm_sum_roberta", "norm_sum_distilbert" )

# Write a function that takes the iv as input and then saves the output as a csv

lm_output <- function(iv, dv, excel_file_name){
  
  ind_v <- iv
  
  # create the formula 
  formula = paste(dv,' ~ ',ind_v, ivs)
  
  # Evaluate the formula using lmer 
  eval(parse(text=paste('regress_obj=', 'lm(as.formula(formula), data=data)')))

  # print the summary print(summary(regress_obj))

  csv_output <-  summary(regress_obj)$coefficients

  # Save the summary figures down in an excel 
  write.xlsx(csv_output, file = excel_file_name, sheetName= iv, append=TRUE,row.names = TRUE)

}

### LINEAR REGRESSIONS WITH SALES AND SENT ###

# Trying a loop that will run the regressions and save the coefficients
lapply(sent_scores, lm_output, dv = "purchase", excel_file_name =
         "lm_purchase_1.xlsx")

# Next day purchase
lapply(sent_scores, lm_output, dv = "next_day_purchase", excel_file_name
       = "lm_next_day_purchase_1.xlsx")

# log purchase
lapply(sent_scores, lm_output, dv = "log_purchase", excel_file_name =
         "lm_log_purchase_1.xlsx")

# Next day log purchase
lapply(sent_scores, lm_output, dv = "next_day_log_purchase",
       excel_file_name = "lm_next_day_log_purchase_1.xlsx")


### LINEAR REGRESSIONS BETWEEN SENT SCORES ###

validation <- function (dv, iv, excel_file_name) {
  
  formula  <- paste(dv,' ~ ',iv)
  # Evaluate the formula using lmer 
  eval(parse(text=paste('validation_lm=', 'lm(as.formula(formula), data=data)')))
  print(summary(validation_lm))
  csv_output <-  summary(validation_lm)$coefficients
  name <- paste("dv=",dv,iv)
  write.xlsx(csv_output, file = excel_file_name, sheetName= name, append=TRUE,row.names = TRUE)
}

validation("norm_sum_pysent", "norm_sum_vader", excel_file_name = "sent_validation_regressions_1.xlsx")
validation("norm_sum_pysent", "norm_sum_roberta", excel_file_name = "sent_validation_regressions_1.xlsx")


### LINEAR REGRESSIONS BETWEEN SPORTS PE AND SENTIMENT 

pe_regression <- function (dv, iv, excel_file_name) {
  # Including all nuisance variables
  formula  <- paste(dv,' ~ ',iv, ivs)
  # Evaluate the formula using lmer 
  eval(parse(text=paste('validation_lm=', 'lm(as.formula(formula), data=data)')))
  summary(validation_lm)
  csv_output <-  summary(validation_lm)$coefficients
  name <- paste("dv=",dv," iv=",iv)
  write.xlsx(csv_output, file = excel_file_name, sheetName= name, append=TRUE,row.names = TRUE)
}


# Regressions with sent scores as DV
pe_regression("norm_sum_vader", "sum_pe", excel_file_name = "sent_against_sports_pe.xlsx")
pe_regression("norm_sum_pysent", "sum_pe", excel_file_name = "sent_against_sports_pe.xlsx")
pe_regression("norm_sum_roberta", "sum_pe", excel_file_name = "sent_against_sports_pe.xlsx")



### REGRESSIONS ON NON-ZERO SPORTS P.E. DAYS ####
data <- read.csv("aggregate_regression_input_no_zero_pe.csv")
pe_regression("norm_sum_pysent", "sum_pe", excel_file_name = "no_z_sent_against_sports_pe.xlsx")
pe_regression("norm_sum_roberta", "sum_pe", excel_file_name = "no_z_sent_against_sports_pe.xlsx")


### REGRESSIONS ON POSITIVE SPORTS P.E. DAY ###
data <- read.csv("only_pos_days.csv")
pe_regression("norm_sum_pysent", "sum_pe", excel_file_name = "pos_pe_days.xlsx")
pe_regression("norm_sum_roberta", "sum_pe", excel_file_name = "pos_pe_days.xlsx")
pe_regression("norm_sum_no_neg_pysent", "sum_pe", excel_file_name = "pos_pe_days.xlsx")

### REGRESSIONS ON NEGATIVE SPORTS P.E. DAY ###
data <- read.csv("only_neg_days.csv")
pe_regression("norm_sum_pysent", "sum_pe", excel_file_name = "neg_pe_days.xlsx")
pe_regression("norm_sum_roberta", "sum_pe", excel_file_name = "neg_pe_days.xlsx")
pe_regression("norm_sum_no_neg_pysent", "sum_pe", excel_file_name = "neg_pe_days.xlsx")

### REGRESSIONS WITH NON-NEGATIVE PYSENT P.E. ###
data <- read.csv("aggregate_regression_input_7.csv")
pe_regression("norm_sum_no_neg_pysent", "sum_pe", excel_file_name = "non_negative_sent.xlsx")



### Corr between sentiments ###

cor.test(data$norm_sum_pysent, data$norm_sum_roberta)
cor.test(data$norm_sum_pysent, data$norm_sum_vader)
cor.test(data$norm_sum_roberta, data$norm_sum_distilbert)





### LINEAR REGRESSION BETWEEN TEAM SPECIFIC PE AND SENTS

pe_regression <- function (dv, iv, excel_file_name, sheetname) {
  # Including all nuisance variables
  formula  <- paste(dv,' ~ ',iv, ivs)
  # Evaluate the formula using lm
  eval(parse(text=paste('validation_lm=', 'lm(as.formula(formula), data=data)')))
  summary(validation_lm)
  csv_output <-  summary(validation_lm)$coefficients
  
  write.xlsx(csv_output, file = excel_file_name, sheetName= sheetname, append=TRUE,row.names = TRUE)
}

#team_pe <- c("knicks_pe", "mets_pe", "yankees_pe", "giants_pe", "jets_pe")

pe_regression("knicks_pe", "knicks_pysent_pe", sheetname = "knicks_pysent", excel_file_name = "indiv_sports_team_pe_regressions.xlsx")
pe_regression("knicks_pe", "knicks_mean_roberta", sheetname = "knicks_roberta", excel_file_name = "indiv_sports_team_pe_regressions.xlsx")

pe_regression("mets_pe", "mets_pysent_pe", sheetname = "mets_pysent", excel_file_name = "indiv_sports_team_pe_regressions.xlsx")
pe_regression("mets_pe", "mets_mean_roberta", sheetname = "mets_roberta", excel_file_name = "indiv_sports_team_pe_regressions.xlsx")

pe_regression("yankees_pe", "yankees_pysent_pe", sheetname = "yankees_pysent", excel_file_name = "indiv_sports_team_pe_regressions.xlsx")
pe_regression("yankees_pe", "yankees_mean_roberta", sheetname = "yankees_roberta", excel_file_name = "indiv_sports_team_pe_regressions.xlsx")

pe_regression("giants_pe", "giants_pysent_pe", sheetname = "giants_pysent", excel_file_name = "indiv_sports_team_pe_regressions.xlsx")
pe_regression("giants_pe", "giants_mean_roberta", sheetname = "giants_roberta", excel_file_name = "indiv_sports_team_pe_regressions.xlsx")

pe_regression("devils_pe", "devils_pysent_pe", sheetname = "jets_pysent", excel_file_name = "indiv_sports_team_pe_regressions.xlsx")
pe_regression("devils_pe", "devils_mean_roberta", sheetname = "jets_roberta", excel_file_name = "indiv_sports_team_pe_regressions.xlsx")


#### FINDING RESIDUAL LOTT TICK. SALES AND SENTIMENT SCORES ###
#### AFTER CONTROLLING FOR NUISANCE VARIABLES ###


get_residuals <- function (dv, excel_file_name) {
  # Including all nuisance variables
  formula  <- paste(dv,' ~ ', ivs)
  # Evaluate the formula using lm
  eval(parse(text=paste('resid_lm=', 'lm(as.formula(formula), data=data)')))
  summary(resid_lm)
  
  resids <- resid(resid_lm)
  #print(resid(resid_lm))
  csv_output <-  resids
  sheetname <-  dv
  write.xlsx(csv_output, file = excel_file_name, sheetName= sheetname, append=TRUE,row.names = TRUE)
}

resid_dvs <- c("norm_sum_pysent", "norm_sum_roberta", "purchase", "next_day_purchase", "next_day_log_purchase" )

# Export residuals DV values regressing on  just thenuisance variables 
lapply(resid_dvs, get_residuals,  excel_file_name =  "residual_dvs.xlsx")













### GET COEFFICIENT TABLES FOR REGRESSIONS THAT WE'VE REPORTED

get_nice_coefficients <- function(dv, iv, file_name, table_title, data){
  
  # Create lm formula
  formula  <- paste(dv,' ~ ',iv, ivs)
  # Evaluate linear model
  df <- data
  model <- lm(as.formula(formula), data = df)
  #eval(parse(text=paste('model=', 'lm(as.formula(formula), data=df)')))
  # Gather summary statistics
  stats.table <- as.data.frame(summary(model)$coefficients)
  # Get the confidence interval (CI) of the regression coefficient
  #CI <- confint(model)
  # Add a row to join the variables names and CI to the stats
  stats.table <- cbind(row.names(stats.table), stats.table)
  # Rename the columns appropriately
  names(stats.table) <- c("Term", "B", "SE", "t", "p")
  my_table <- nice_table(stats.table, title = c(table_title), highlight = TRUE)
  
  # Output as a word doc
  path_dir <- paste("/cloud/project/",file_name,".docx" )
  save_as_docx(my_table, path = path_dir)
}


# Sentiment p.e. vs sports p.e. #

#get_nice_coefficients(dv = "norm_sum_pysent", iv = "sum_pe", file_name = "Sent p.e. vs Sports p.e.",
#                      table_title = "Table 1: Linear regressions results of sentiment based prediction errors vs. sports predictions errors, controlling for nuisance variables",
#                      data = data)

# Surprise vs sports p.e.
#get_nice_coefficients(dv = "norm_sum_roberta", iv = "sum_pe", file_name = "Surprise vs Sports p.e.",
#                      table_title = "Table 2: Linear regressions results of daily mean suprise scores vs. sports predictions errors, controlling for nuisance variables",
#                      data = data)


# Next day log purchases vs Sentiment p.e.
#get_nice_coefficients(dv = "next_day_log_purchase", iv = "norm_sum_pysent", file_name = "Lott vs Sports p.e.",
#                      table_title = "Table 3: Linear regressions results of Log of next day per capita citywide lottery ticket sales vs. sentiment based p.e., controlling for nuisance variables",
#                      data = data)


# Next day log purchases vs surprise scores
#get_nice_coefficients(dv = "next_day_log_purchase", iv = "norm_sum_roberta", file_name = "Lott vs surprise",
                      table_title = "Table 4: Linear regressions results of Log of next day per capita citywide lottery ticket sales vs. daily mean suprise scores, controlling for nuisance variables",
                      data = data)


# Sentiment p.e. vs sports p.e. (data without zero sports p.e.)
#get_nice_coefficients(data = data_no_zeros, dv = "norm_sum_pysent", iv = "sum_pe", file_name = "No zeros - Sentiment p.e. vs Sports p.e.",
                      table_title = "Table 5: (Exluding dates with zero sports p.e.) Linear regressions results of sentiment based prediction errors vs. sports predictions errors, controlling for nuisance variables")

# Surprise vs sports p.e. (data without zero sports p.e.)
#get_nice_coefficients(data = data_no_zeros, dv = "norm_sum_roberta", iv = "sum_pe", file_name = "No zeros - Surprise vs Sports p.e.",
                      table_title = "Table 6: (Exluding dates with zero sports p.e.)  Linear regressions results of surprise scores vs. sports predictions errors, controlling for nuisance variables")


