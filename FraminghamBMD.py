# ---
# jupyter:
#   jupytext:
#     formats: ipynb,Rmd,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.3.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # Analysis of Framingham BMD data 
# ## Abhijit Dasgupta

# ## The idea

# We have two cohorts, denoted *original* and *offspring*, that are followed over time. For each cohort, bone mineral density (BMD) is measured 3 times. We are interested in seeing how the BMD changes ecologically over time, hopefully in inverse relation to the known prevalence changes in hip fractures over time. 
#
# The assessment of BMD change has to be adjusted for subject age, since the biggest factor for reduction in BMD is age. The first analysis proposes to merge the original and offspring cohorts and use the full data to model the change in BMD over time adjusted for age (or age groups). We'll split the ages up by decade. 

# +
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import seaborn as sns

# %matplotlib inline

# +
original = pd.read_excel('cohortBMD_newID2.XLSX')[['newid','SEX','scdt','Exam','age','year_of_birth','TScore']]
offspring = pd.read_excel('offspringBMD_newID2.xlsx')[['newID','SEX','scdt','Exam','age','year_of_birth','TScore']]
original.columns = map(str.lower, original.columns)
offspring.columns = map(str.lower, offspring.columns)
original['cohort'] = 'original'
offspring['cohort'] = 'offspring'

full_data = pd.concat([original, offspring], ignore_index=True, axis=0)
full_data.head()
# -

# We now create some categories for age and time. In particular, we split ages into groups <= 50, 51-60, 61-70, 71-80, 80 and above, and time into half-decades. The following table gives the mean t-score per age/time combination, and the subsequent table gives the frequencies (number of subjects) per age/time combination

full_data['age_groups'] = pd.cut(full_data.age, [30,50, 60,70, 80, 101])
full_data['exam_year'] = pd.DatetimeIndex(full_data['scdt']).year
full_data['half_decs'] = pd.cut(full_data.exam_year, range(1985,2011, 5))
bl = full_data.groupby(['half_decs','age_groups'], as_index=False)['tscore'].mean()
bl2 = bl.pivot(columns='half_decs', index = 'age_groups', values='tscore')
bl2

pd.crosstab(full_data.age_groups, full_data.half_decs)

# The pattern of average t-scores by age and time is more evident in the figure below.

fig = sns.catplot(data=full_data, x = 'half_decs', y ='tscore', hue = 'age_groups',
                  kind='point', legend=False, palette='Reds_r');
plt.xlabel('Exam year');
plt.ylabel('T-Score');
plt.xticks(rotation=45);
plt.legend(title='Age groups');

# We can do a bit of modeling using OLS regression to quantify gross patterns in the t-scores. We will model the t-scores on age groups and time intervals.

full_data1 = full_data.copy()
full_data1['age_groups'] = full_data1.age_groups.astype(str)
full_data1['half_decs'] = full_data1.half_decs.astype(str)
model = smf.ols('tscore ~ age_groups + half_decs', data=full_data1)
model.fit().summary()

# In this model, the baseline reference group are subjects 50 years and under in 1986-1990. As expected, we find that t-scores get worse as age increases, but, adjusted for age, t-scores increase over time, with changes from the earliest years being statistically significant.

# ## Influence of gender

plot_data = full_data.copy()
plot_data['sex'] = plot_data.sex.replace({1:'Male', 2:'Female'})
fig = sns.catplot(data=plot_data, col='sex', x = 'half_decs', y = 'tscore', hue = 'age_groups', 
                  kind='point', legend=False, palette='Reds_r')
plt.legend(title='Age groups');
for ax in fig.axes.flat:
    ax.set_xlabel('Exam year')
    #ax.set_ylabel('T-score')
    for label in ax.get_xticklabels():
        label.set_rotation(45)
fig.axes[0,0].set_ylabel('T-score');

model2 = smf.ols('tscore ~ age_groups*sex + half_decs*sex ', data=full_data)
results = model2.fit()
table = sm.stats.anova_lm(results)
table

plot_data = full_data.copy()
plot_data['sex'] = plot_data.sex.replace({1:'Male', 2:'Female'})
fig = sns.catplot(data=plot_data, col='age_groups', x = 'half_decs', y = 'tscore', hue = 'sex', kind='point', legend=False)
plt.legend(title='Age groups');
for ax in fig.axes.flat:
    ax.set_xlabel('Exam year')
    #ax.set_ylabel('T-score')
    for label in ax.get_xticklabels():
        label.set_rotation(45)
fig.axes[0,0].set_ylabel('T-score');

# ## Individual variation
#
# I'm trying to see how the trajectories of t-scores within individuals looks like. Generally, the offspring are in better shape than the original cohort, and as you've said, the scores are relatively stable, though some do fall. See below

sns.lineplot(data=full_data, x = 'scdt', y = 'tscore', units='newid', hue="cohort", estimator=None, alpha=0.05);
plt.xlabel('Exam date')
plt.ylabel('T-Score')
plt.title('Individual t-score trajectories in Framingham cohorts');
plt.legend();

indx=full_data.groupby('newid')['scdt'].idxmin()
first_scan = full_data.loc[indx,:]
first_scan['sex'] = first_scan['sex'].astype('category')
sns.scatterplot(data=first_scan, x="scdt", y="tscore", style="sex", hue='cohort');
plt.xlabel('Exam date'); plt.ylabel('T-Score')
plt.title('Distribution of T-Scores from first scans')
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.);

# This plot is very interesting, in that is brings up some questions:
#
# 1. Some of the original cohort women are in very bad shape (t-score < -4), but almost noone in the offspring cohort is
# 1. The variability in the earliest scan of each cohort is far more variable than the subsequent rounds

first_scan.head()
sns.scatterplot(data=first_scan, x = 'scdt', y = 'tscore', hue='age_groups' , alpha=0.5,
               palette = 'Reds_r');
plt.title('First scans by date and age')
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.);
