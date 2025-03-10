## IMPORTS

import pandas as pd
import streamlit as st
import ons_data_collection
import pickle

#--------------------------------------------------------------------

### LOADING DATA ###

# This code is not currently being used as was affecting online deployment
# # import our ONS data which is already saved in dataframe pkl file
# try: 
#     df = 
# except:
#     ons_data_collection.get_all_data()
#     df = pd.read_pickle('./Data/Dataframe/ons_df.pkl')

# # set a start parameter with an experimental memo cacher
# @st.experimental_memo
# def start():
#     ons_data_collection.get_all_data()
#     df = pd.read_pickle('ons_df.pkl')
#     return df

# This is a temporary piece of code to allow for deployment from static .csv
def get_test_data():
    # read in csv file
    df = pd.read_csv('ons_csv_test.csv')
    # fix the columns
    # add MultiIndex column headers and convert to time-series with datetime
    df = ons_data_collection.fix_df_columns(df)
    df = ons_data_collection.df_to_MultiIndex_time_series(df)
    return df

# start it
df = get_test_data()
 
#--------------------------------------------------------------------

### LOADING LISTS FROM PRE-BUILD PICKLE FILES ###

# get our commodity list from pkl file
open_file=open('./Data/pkl_lists/commodity_list.pkl', 'rb')
commodity_list = pickle.load(open_file)
open_file.close()

# get our partner list from pkl file
open_file=open('./Data/pkl_lists/partner_list.pkl', 'rb')
partner_list = pickle.load(open_file)
open_file.close()

#--------------------------------------------------------------------

### SETTING MAIN TITLE AND INTRO TEXT ###

# title
st.write("""
# UK Goods Exports  
#### Data: [ONS: Trade in goods: country-by-commodity exports](https://www.ons.gov.uk/economy/nationalaccounts/balanceofpayments/datasets/uktradecountrybycommodityexports)""")

#intro
st.write("""
##### This dashboard is for analysing UK goods exports to different trading partners around the world. The first section looks at the UK's total goods exports to the selected trade partner. The second section looks at UK exports to that same partner by SITC 1 digit product categories, products to be included can be turned on/off via the multi-selector. The third section compares UK exports of the selected partner and product to a range of other trading partners. By default all charts are on a 12 month rolling sum basis, but the degree of rolling can be set in the sidebar -- and set rolling as "1" for monthly values. Minimum and maximum date ranges for the charts can be set using the sliders in the sidebar. Side bar sliders controll all the visuals at once.

##### Recommend going to settings (top-right) and selecting 'Wide mode'
---
""")

#--------------------------------------------------------------------

## SETTING UP THE FIRST THREE PLOTS FOR TOTAL EXPORTS

# setting up select boxes for our list of partners and trade products
partner_select = st.selectbox('Which main trade partner do you want to analyse?', partner_list, index = partner_list.index('Whole world') )

# use these values to filter df for first two charts
plot_df = (df.xs(partner_select, axis=1, level=0)
             .xs('Total', axis=1, level=1)
          )

# rename the columns to the partner name
plot_df.columns = [partner_select]

# setting up a slider to choose rolling level
rol_val = st.sidebar.slider('Monthly Rolling Sum (set as "1" for no rolling)', min_value=1, max_value=12, value=12)
plot_df = plot_df.rolling(rol_val).sum().dropna() # edit the plotting df accordingly

# setting a yearly range to be diplayed on the axis
# set as two separate slides for min and max
min_year = st.sidebar.slider('Date Range - Minimum', 
                               min_value=plot_df.index.min().year, 
                               max_value=plot_df.index.max().year,
                               value=2016
                              )

max_year = st.sidebar.slider('Date Range - Maximum', 
                               min_value=plot_df.index.min().year, 
                               max_value=plot_df.index.max().year,
                              value=2022
                              )
# convert the min and max years to strings so can use with .loc to index plots for x-axis
min_year = str(min_year)
max_year = str(max_year)

# write a title for the first section
st.write(
f"""
---
##### Total UK Exports to {partner_select}  
This section shows the UK's total exports to the selected partner: the total value, the yoy change in £s and the yoy change in % terms.
Values can be set to rolling monthly sums using the slider in the page's sidebar.
""")

# create plotting dfs that are filtered by year range
plot_abs_df = plot_df.round(1).loc[min_year:max_year] # our plot for absolute values
plot_diff_df = plot_df.diff(12).round(1).loc[min_year:max_year] # our plot for absolute values
plot_percent_df = plot_df.pct_change(12).mul(100).dropna().round(1).loc[min_year:max_year] # our plot for yoy change

# create three separate columns
cola1, cola2, cola3 = st.columns((1,1,1))

with cola1: 
    # plot a line chart of monthly absolute values
    if rol_val > 1:
        st.write(f"UK total exports to {partner_select}, rolling {str(rol_val)}M sum, £s millions") #title
    else:
        st.write(f"UK total exports to {partner_select}, monthly, £s millions")
    st.line_chart(plot_abs_df)           #line chart

with cola2: 
    # plot a line chart of gbp yoy change
    if rol_val > 1:
        st.write(f"UK exports to {partner_select} by SITC 1 digit, rolling {str(rol_val)}M sum, £ millions change yoy") #title
    else:
        st.write(f"UK exports to {partner_select} by SITC 1 digit, monthly, £s millions change yoy")
    st.line_chart(plot_diff_df)           #line chart

with cola3:
    # plot a line of monthly yoy % change
    if rol_val > 1:
        st.write(f"UK total exports to {partner_select}, rolling {str(rol_val)}M sum, % change yoy") #title
    else:
        st.write(f"UK total exports to {partner_select}, monthly, % change yoy")
    st.line_chart(plot_percent_df)

#--------------------------------------------------------------------
   
### SETTING UP THE FIRST THREE PLOTS FOR EXPORTS BY SITC 1-DIGIT
    
# create a list of codes for the SITC one-digit categories
sitc1_list = ['1','2','3','4','5','6','7','8','9']

# index our df using the new sitc list and our selected partner
# Transpose the df, use pd index slice and transpose back
idx = pd.IndexSlice
plot_sitc1_df = df.T.loc[idx[partner_select,sitc1_list,:,:] ,:].T

# create a list of names from the comm_desc part of our multi-index with list comprehension
# set this list of names as the column names
sitc_1dig_names = [x[2] for x in plot_sitc1_df.columns]
plot_sitc1_df.columns = sitc_1dig_names

# add the page-wide rolling factor to our plot
plot_sitc1_df2 = plot_sitc1_df.rolling(rol_val).sum().dropna() # edit the plotting df accordingly

# create three new plot dfs using this newly subsetted dataframe
plot_sitc1_abs_df = plot_sitc1_df2.round(1).loc[min_year:max_year] # for plotting absolute values
plot_sitc1_diff_df = plot_sitc1_df2.diff(12).round(1).loc[min_year:max_year] # for plotting absolute values
plot_sitc1_percent_df = plot_sitc1_df2.pct_change(12).mul(100).dropna().round(1).loc[min_year:max_year] # the % change yoy

# creating a title for the second section
st.write(
f"""
---
##### UK Exports to {partner_select} by SITC 1 Digit Code  
This section shows the UK's exports to the selected partner by SITC 1 digit: the total value, the yoy change in £s and the yoy change in % terms. 
SITC 1 digit categories can be turned on/off using the multi-selector. Values can be set to rolling monthly sums using the slider in the page's sidebar.
""")

# setting up the multi-selector for which SITC 1 digit codes to include
sitc1_abs_list = st.multiselect('Select SITC 1 digit to include', sitc_1dig_names, default=sitc_1dig_names)

# create three separate columns
colb1, colb2, colb3 = st.columns((1,1,1))

# plot relevant chart in each column: 1. absolute, 2. yoy diff, 3. % change yoy
with colb1: 
    # plot a bar chart of monthly absolute values
    # handle titles depending on opage-wide rolling factor
    if rol_val > 1:
        st.write(f"UK exports to {partner_select} by SITC 1 Digit, rolling {str(rol_val)}M sum, £s millions") #title
    else:
        st.write(f"UK exports to {partner_select} by SITC 1 Digit, monthly, £s millions")   
    st.bar_chart(plot_sitc1_abs_df[sitc1_abs_list])#[sitc1_abs_list])           #line chart

with colb2: 
    # plot a bar chart of monthly absolute values
    # handle titles depending on opage-wide rolling factor
    if rol_val > 1:
        st.write(f"UK exports to {partner_select} by SITC 1 Digit, rolling {str(rol_val)}M sum, £s millions yoy change") #title
    else:
        st.write(f"UK exports to {partner_select} by SITC 1 Digit, monthly, £s millions yoy change")
    st.bar_chart(plot_sitc1_diff_df[sitc1_abs_list])           #line chart

with colb3: 
    # plot a bar chart of monthly absolute values
    # handle titles depending on opage-wide rolling factor
    if rol_val > 1:
        st.write(f"UK exports to {partner_select} by SITC 1 Digit, rolling {str(rol_val)}M sum, % yoy change") #title
    else:
        st.write(f"UK exports to {partner_select} by SITC 1 Digit, monthly, % yoy change")
    st.line_chart(plot_sitc1_percent_df[sitc1_abs_list])           #line chart

#--------------------------------------------------------------------
   
### SETTING UP THE FINAL THREE PLOTS FOR COMPARING BY CHOSEN PRODUCT

# write the title and intro for section 3
st.write(
f"""
---  
##### UK exports to selected partners, for selected product category
This section shows the UK's exports of the selected product categoory to the range of selected partners by the total value, 
the yoy change in £s and the yoy change in % terms. The product category and comparison partners can be set using the options. 
Values can be set to rolling monthly sums using the slider in the page's sidebar.
"""
)

# setup a list of starting comparitors
if partner_select != 'Whole world':
    comparitors = [partner_select, 'Whole world', 'Total EU(28)', 'Extra EU 28 (Rest of World)']
else:
    comparitors = ['Whole world', 'Total EU(28)', 'Extra EU 28 (Rest of World)']

# create a selectbox for choosing commodity to look at comparison chart for
product_select = st.selectbox('Select a product to compare across partners', commodity_list, index= commodity_list.index('Total'))

# setting up the trading partner multi-selector
multipartner_select = st.multiselect('Select trade partners to include', partner_list, default=comparitors)

# index our dataframe using our selections
# need to transpose once and then back again.
# use colons (:) to pick all instances for code and flow index
idx = pd.IndexSlice
plot_compare_df = df.T.loc[idx[multipartner_select,:,product_select,:] ,:].T

# create a list of names from the comm_desc part of our multi-index
# set this list of names as the column names
compare_names = [x[0] for x in plot_compare_df.columns]
plot_compare_df.columns = compare_names

# add the rolling factor to our plotting df
plot_compare_df = plot_compare_df.rolling(rol_val).sum().dropna() # edit the plotting df accordingly

# create three new plot dfs using this newly subsetted dataframe
plot_compare_abs_df = plot_compare_df.round(1).loc[min_year:max_year] # for plotting absolute values
plot_compare_diff_df = plot_compare_df.diff(12).dropna().round(1).loc[min_year:max_year] # for plotting absolute values
plot_compare_percent_df = plot_compare_df.pct_change(12).mul(100).dropna().round(1).loc[min_year:max_year] # the % change yoy

# create three separate columns
colc1, colc2, colc3 = st.columns((1,1,1))

# plot a separate chart in each column
with colc1: 
    # plot a line chart of monthly absolute values
    # handle titles depending on the rolling factor
    if rol_val > 1:
        st.write(f"UK {product_select} exports to {partner_select}, rolling {str(rol_val)}M sum, £s millions") #title
    else:
        st.write(f"UK {product_select} exports to {partner_select}, monthly, £s millions")
    st.line_chart(plot_compare_abs_df)           #line chart

with colc2: 
    # plot a line chart of gbp yoy change
    # handle titles depending on the rolling factor
    if rol_val > 1:
        st.write(f"UK {product_select} exports to {partner_select}, rolling {str(rol_val)}M sum, £s millions change yoy") #title
    else:
        st.write(f"UK {product_select} exports to {partner_select}, £s millions change yoy")
    st.line_chart(plot_compare_diff_df)           #line chart

with colc3:
    # plot a line of monthly yoy % change
    # handle titles depending on the rolling factor
    if rol_val > 1:
        st.write(f"UK {product_select} exports to {partner_select}, rolling {str(rol_val)}M sum, % change yoy") #title
    else:
        st.write(f"UK {product_select} exports to {partner_select}, monthly, % change yoy")
    st.line_chart(plot_compare_percent_df)

#--------------------------------------------------------------------
#ENDS#


