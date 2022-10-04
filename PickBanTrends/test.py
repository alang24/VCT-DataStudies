import pandas as pd
import numpy as np
import plotly_express as px
import plotly.io as pio

pio.templates.default='plotly_dark'

seriesinfogen_df = pd.read_csv('data/st1_na_group_seriesinfogen.csv',index_col=0)
seriesinfomatch_df = pd.read_csv('data/st1_na_group_seriesinfomaps.csv',index_col=0)
print(seriesinfogen_df)


seriesinfogen_df.loc["20220213-OPTC-Rise",seriesinfogen_df.columns[5:]]=['Breeze','Icebox','Bind','Haven','Fracture','Split','Ascent','NaN']
seriesinfogen_df = seriesinfogen_df.drop(columns='Pick/Ban')

def maketotalDF(df):
    allbans = pd.Series(np.array(df.loc[:,df.columns[df.columns.str.contains(':Ban')]]).flatten())
    allpicks = pd.Series(np.array(df.loc[:,df.columns[(df.columns.str.contains(':Pick'))|(df.columns.str.contains("Decider"))]]).flatten())
    grouped = pd.concat([allbans.value_counts(normalize=True),allpicks.value_counts(normalize=True)],axis=1).sort_index().reset_index()
    grouped.columns = ['Map','Total Banned','Total Played']
    melted=pd.melt(grouped,id_vars=['Map'],var_name='Type',value_name = 'Percentage')
    d = px.bar(melted,x='Map',y='Percentage',color='Type',barmode='group',)
    d.write_html('agg.html')
    #return grouped_prop

def makesingleDF(df):
    firstbans = pd.Series(np.array(df.loc[:,df.columns[df.columns.str.contains(':Ban 1')]]).flatten())
    firstpicks = pd.Series(np.array(df.loc[:,df.columns[(df.columns.str.contains(':Pick'))]]).flatten())
    decider = pd.Series(np.array(df.loc[:,df.columns[(df.columns.str.contains("Decider"))]]).flatten())
    grouped= pd.concat([firstbans.value_counts(normalize=True),firstpicks.value_counts(normalize=True),decider.value_counts(normalize=True)],axis=1).sort_index().reset_index()
    grouped.columns = ['Map','First Ban','First Pick','Decider']

    melted=pd.melt(grouped,id_vars=['Map'],var_name='Type',value_name = 'Percentage')
    d = px.bar(melted,x='Map',y='Percentage',color='Type',barmode='group',)
    d.write_html('sing.html')
    #return grouped_prop

# print(maketotalDF(seriesinfogen_df.copy()))
# print(makesingleDF(seriesinfogen_df.copy()))

def isolateteam_bp(team,df,ban):
    team_df=df.loc[df.index.str.contains(team)]
    bp_list = []
    for ind,row in team_df.iterrows():
        if row['A:Name']==team:
            bp_list.append(row['A:Ban 1']) if ban else bp_list.append(row['A:Pick'])
        else:
            bp_list.append(row['B:Ban 1']) if ban else bp_list.append(row['B:Pick'])

    return bp_list
team_df = pd.DataFrame(pd.concat([seriesinfogen_df["A:Name"],seriesinfogen_df["B:Name"]]).drop_duplicates().values,columns=['Team'])

team_df['First Bans'] = team_df['Team'].apply(isolateteam_bp,args=(seriesinfogen_df.copy(),True))
team_df['Picks'] = team_df['Team'].apply(isolateteam_bp,args=(seriesinfogen_df.copy(),False))


def findmostpickban(row):
    pb_list=[]
    for pb in ['First Bans','Picks']:
        pb_series = pd.Series(row[pb])
        for lim in [5,4,3]:
            if pb_series.value_counts()[0] >= lim:
                pb_list.append(pb_series.value_counts().index[0])
            else:
                pb_list.append("Nope")
    return pb_list


def interpretmostpickban(df):
    for col in df.columns[3:]:
        nay = df[col].value_counts().loc['Nope']
        print(col,':',df.shape[0]-nay,'out of ', df.shape[0],'teams')
    return 
team_dfpb = team_df.apply(findmostpickban,axis=1,result_type='expand')
team_dfpb.columns = [occur + ' '+ name for name in ['Ban','Pick'] for occur in ['Perma','Heavy','Majority']]
team_df = pd.concat([team_df,team_dfpb],axis=1)
interpretmostpickban(team_df.copy())

def firstpickwin(row,gen_df):
    sub_gen_df = gen_df.loc[row.name,:]

    teama = sub_gen_df['A:Name']
    teamb = sub_gen_df['B:Name']
    teamapick = sub_gen_df['A:Pick']
    teambpick = sub_gen_df['B:Pick']

    if row['Map'].split('-')[0]=='3':
        return "Decider"
    else:
        mapname = row['Map'].split('-')[1]
        temp = teama if mapname == teamapick else teamb
        return "Success" if temp==row['Winner'] else "Fail"
        
seriesinfomatch_df['OwnPickWon'] = seriesinfomatch_df.apply(firstpickwin,axis=1,args=(seriesinfogen_df,))
seriesinfomatch_df['RoundDiff'] = seriesinfomatch_df.apply(lambda row: abs(row['A:Rnds']-row['B:Rnds']),axis=1)

#print(seriesinfomatch_df.loc[seriesinfomatch_df['OwnPickWon'].str.contains('Success'),:]['RoundDiff'].mean())
print(seriesinfomatch_df.groupby('OwnPickWon').agg(['mean','median'])['RoundDiff'])

