library(lme4)
library(effects)


DV = 'affect_mean ~ '
year = 2012

fixed_terms = 'TUE + WED + THU + FRI + SAT + SUN + JAN + FEB + MAR + APR + MAY + JUN + JUL + AUG + SEP + OCT + NOV + INDEPENDENCEDAY + THANKSGIVING + DAYAFTERCHRISTMAS + NEWYEARSEVE +EASTER + NEWYEARSDAY + MEMORIALDAY +  VALENTINESDAY' 

random_terms = 'dni_pe | msa/county'

    
sent = read.csv( paste('regress/sent_regress_input/all_msa_sent_regress_', year, '.csv', sep='') )


print(c('n:', dim(sent)[1]))

test_formula = paste(DV,paste(fixed_terms,collapse='+'), '+ (1 +',random_terms,')')
eval(parse(text= paste('test_regress_obj=', 'lmer(as.formula(test_formula), data=sent, weights=county_msa_weight, control = lmerControl(calc.derivs = FALSE))',sep='')))


fixed_terms = paste(as.vector(names(fixef(test_regress_obj)[2:length(fixef(test_regress_obj))])), collapse=' + ')
random_terms = paste(as.vector(names(fixef(test_regress_obj)[2:length(fixef(test_regress_obj))])), collapse=' + ') 

formula = paste(DV,paste(fixed_terms,collapse='+'), '+ (1 +',random_terms,'| msa/county )')

print(formula)


eval(parse(text= paste('regress_obj=', 'lmer(as.formula(formula), data=sent, weights=county_msa_weight,control = lmerControl(calc.derivs = FALSE))',sep='')))

    
save.image(paste('regress/lmer_objects/all_msa_',year,'_affect_nuisance_full.RData',sep=""))
sent$resid_sent = resid(regress_obj)
write.csv(sent, paste('regress/sent_resid/resid_all_msa_',year,'_full.csv',sep=''), row.names=FALSE)

