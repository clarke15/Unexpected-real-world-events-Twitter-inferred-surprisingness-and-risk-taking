library(lme4)
library(effects)


DV = 'affect_mean ~ '
year = 2013

fixed_terms = 'dni_pe + TUE + WED + THU + FRI + SAT + SUN + JAN + FEB + MAR + APR + MAY + JUN + JUL + AUG + SEP + OCT + NOV + INDEPENDENCEDAY + THANKSGIVING + DAYAFTERCHRISTMAS + NEWYEARSEVE +EASTER + NEWYEARSDAY + MEMORIALDAY +  VALENTINESDAY' 

random_terms = 'raw_dni_pe | msa/county'
    
sent = read.csv( paste('../data/regress/sent_regress_input/all_msa_sent_regress_', year, '.csv', sep='') )

print(c('n:', dim(sent)[1]))

test_formula = paste(DV,paste(fixed_terms,collapse='+'), '+ (1 +',random_terms,')')
eval(parse(text= paste('test_regress_obj=', 'lmer(as.formula(test_formula), data=sent, weights=county_msa_weight, control = lmerControl(calc.derivs = FALSE))',sep='')))


fixed_terms = paste(as.vector(names(fixef(test_regress_obj)[2:length(fixef(test_regress_obj))])), collapse=' + ')
random_terms = paste(as.vector(names(fixef(test_regress_obj)[2:length(fixef(test_regress_obj))])), collapse=' + ') 

formula = paste(DV,paste(fixed_terms,collapse='+'), '+ (1 +',random_terms,'| msa/county )')

print(formula)


eval(parse(text= paste('regress_obj=', 'lmer(as.formula(formula), data=sent, weights=county_msa_weight,control = lmerControl(calc.derivs = FALSE))',sep='')))

    
eff_df = data.frame(effect('raw_dni_pe', regress_obj,xlevels=list(raw_dni_pe = seq( min(sent[!is.na(sent$raw_dni_pe),]$raw_dni_pe)-1, max(sent[!is.na(sent$raw_dni_pe),]$raw_dni_pe)+1, .25))))


if(DV == 'affect_mean ~ '){
 write.csv(eff_df, paste('../data/regress/effect_plot_df/all_msa_irradiance_sent_',year,'.csv',sep=''), row.names=FALSE)
  save.image(paste('../data/regress/lmer_objects/all_msa_',year,'_irradiance_sent.RData',sep=""))
  } else {
  write.csv(eff_df, paste('../data/regress/effect_plot_df/all_msa_irradiance_sent_',year,'_num_tweets.csv',sep=''), row.names=FALSE)
    save.image(paste('../data/regress/lmer_objects/all_msa_',year,'_irradiance_num_tweets.RData',sep=""))
}



