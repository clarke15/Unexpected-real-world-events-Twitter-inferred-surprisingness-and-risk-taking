from random import choice

font = {'family' : 'Helvetica', 
        'weight':'normal',
        'size'   : 16}
matplotlib.rc('font', **font)

ANALYSIS_YEAR = 2013
PE_TYPE = 'sports' # 'irradiance' #

MSA_NAMES = {'sfbay':'SF Bay', 
             'chicago':'Chicago', 
             'boston':'Boston', 
             'dfw':'DFW', 
             'nyc_metro':'NYC', 
             'la': 'LA'}


all_betas = DataFrame.from_csv('./regress/effect_plot_df/all_msa_'+PE_TYPE + '_county_effects_df_'+str(ANALYSIS_YEAR) + '.csv')

msas = ['sfbay', 'chicago', 'boston', 'dfw', 'nyc_metro', 'la'] 

fig= figure()
num_colors = len(msas)
cm = get_cmap('Paired')
ax = fig.add_subplot(111)
ax.set_color_cycle([cm(1.*i/num_colors) for i in array(range(num_colors))+3])


effects = []

y_pos = arange(-.5, -1*len(unique(all_betas.msa)), -.5)


for msa in msas:
    print msa, [cm(1.*i/num_colors) for i in range(num_colors)][msas.index(msa)]

    msa_eff = all_betas[all_betas.msa==msa].iloc[0].msa_eff

    effects.append(all_betas[all_betas.msa==msa].county_eff)

    vlines( msa_eff,y_pos[msas.index(msa)], 0, 
            color=[cm(1.*i/num_colors) for i in range(num_colors)][msas.index(msa)],         
            linestyles='dashed')
    text(msa_eff, y_pos[msas.index(msa)], 
         msa ,
         color=[cm(1.*i/num_colors) for i in range(num_colors)][msas.index(msa)],#'black',
         fontsize=11,horizontalalignment='center')

    
hist(effects,9, normed=0, histtype='bar', stacked=True, label= map(lambda x:MSA_NAMES[x], msas), color=[cm(1.*i/num_colors) for i in range(num_colors)] , rwidth=.9,
     linewidth = 0)

vlines( 0,-4, ylim()[1],   color='black',        linestyles='dotted')


[xmin,xmax] = xlim()
plot([xmin,xmax], [0, 0], color='black')
legend(prop={'size':12}, title='MSA', loc='best')
xlabel('effect size (a.u.)')
ylabel('number of counties')
show()
