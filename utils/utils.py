import pandas as pd

def get_top_cats(property_df):

    """Returns a df displaying top values for each city of columns below."""
    columns = ['city', 'bedrooms', 'bathrooms', 'propertySubType', 'listingUpdate']
    df_short = property_df[columns].reset_index(drop=True)
    df_short[['bedrooms', 'bathrooms']] = df_short[['bedrooms', 'bathrooms']].astype('category') 
    listing_update_expanded = pd.DataFrame(df_short.listingUpdate.to_list())
    df_expanded = pd.concat([df_short.drop('listingUpdate', axis=1), listing_update_expanded['listingUpdateReason']], axis=1)
    df_summary = df_expanded.groupby('city').describe(include='all')
    df_summary_top_vals = df_summary.xs('top', level=1, axis=1).reset_index()
    return df_summary_top_vals

    