library(lme4)
library(effects)

args = commandArgs(TRUE)
msa = c(args[1])
year = 2013

input_file = paste('regress/lott_sent_regress_input/',msa,'_lott_sent_regress_input_',year,'.csv', sep='')
print(paste('using:', input_file))
lott = read.csv(input_file, TRUE)

fixed_terms = 'affect_mean + TUE + WED + THU + FRI + SAT +  SUN + FEB + MAR + APR + MAY + JUN + JUL + AUG + SEP + OCT +  NOV + DEC + FIRST_OF_MONTH + FIFTEENTH_OF_MONTH + STORM + INDEPENDENCEDAY + THANKSGIVING + CHRISTMASDAY + DAYAFTERCHRISTMAS +      LABORDAY + EASTER + NEWYEARSDAY + COLUMBUSDAY + MEMORIALDAY +      BIRTHDAYOFMARTINLUTHERKINGJR + VETERANSDAY + WASHINGTONSBIRTHDAY + VALENTINESDAY'

random_terms = 'affect_mean'

test_formula = paste('log_purchase ~ ',paste(fixed_terms,collapse='+'), '+ (1 +',random_terms,'| ZIP)')
eval(parse(text= paste('test_regress_obj=', 'lmer(as.formula(test_formula), data=lott, control = lmerControl(calc.derivs = FALSE))',sep='')))

fixed_terms = paste(as.vector(names(fixef(test_regress_obj)[2:length(fixef(test_regress_obj))])), collapse=' + ')
random_terms = paste(as.vector(names(fixef(test_regress_obj)[2:length(fixef(test_regress_obj))])), collapse=' + ') 

formula = paste('log_purchase ~ ',paste(fixed_terms,collapse='+'), '+ (1 +',random_terms,'| ZIP )')
print(formula)

eval(parse(text= paste('sent_lott_regress_obj=', 'lmer(as.formula(formula), data=lott, control = lmerControl(calc.derivs = FALSE))',sep='')))

print(summary( sent_lott_regress_obj))

save.image(paste('./regress/lmer_objects/lmer_',msa,'_sent_lott_full_',year,'.RData',sep=''))

eff_df = data.frame(effect('affect_mean', sent_lott_regress_obj,xlevels=list(affect_mean = seq( min(lott[!is.na(lott$affect_mean),]$affect_mean)-2, max(lott[!is.na(lott$affect_mean),]$affect_mean)+2, .25))))
write.csv(eff_df, paste('regress/effect_plot_df/',msa,'_sent_lott_',year,'.csv',sep=''), row.names=FALSE)






