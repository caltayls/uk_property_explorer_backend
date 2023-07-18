import pandas as pd

def get_summary_table(property_df, search_type):

    """Returns a df displaying summary for each city of columns below."""
    columns = ['city', 'bedrooms', 'bathrooms', 'propertySubType', 'listingUpdate', 'price']
    # remove unnecessary columns
    df_short = property_df[columns].reset_index(drop=True)
    df_short[['bedrooms', 'bathrooms']] = df_short[['bedrooms', 'bathrooms']].astype('category') 
    
    # Expand columns with nested data
    listing_update_expanded = pd.DataFrame(df_short.listingUpdate.to_list())
    price_exp = pd.DataFrame(df_short.price.to_list())

    # Concat expanded cols with orginal df
    df_expanded = pd.concat([
            df_short.drop('listingUpdate', axis=1), 
            listing_update_expanded['listingUpdateReason'], 
            price_exp['amount']
        ], axis=1)
    df_expanded.amount = df_expanded.amount.astype(int)
    df_expanded = df_expanded.query("amount > 100")
    df_expanded.drop('price', axis=1, inplace=True)
    df_summary = df_expanded.groupby('city').describe(include='all')
    df_summary
    if search_type == 'features':
        # Returns statistical data of house prices
        return df_summary.xs('amount', level=0, axis=1).iloc[:, 4:].astype(int).reset_index()
    
    # Returns top count for categorical data
    df_summary_top_vals = df_summary.xs('top', level=1, axis=1).reset_index()
    return df_summary_top_vals.drop(['amount'], axis=1)
