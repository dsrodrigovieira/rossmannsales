import pickle
import pandas as pd
import inflection
import numpy as np
import datetime
import math

class Rossmann ( object ):
    
    def __init__( self ):      
          
        self.competition_distance_scaler   = pickle.load(open('parameter/competition_distance_scaler.pkl','rb'))
        self.year_scaler                   = pickle.load(open('parameter/year_scaler.pkl','rb'))
        self.competition_time_month_scaler = pickle.load(open('parameter/competition_time_month_scaler.pkl','rb'))
        self.promo_time_week_scaler        = pickle.load(open('parameter/promo_time_week_scaler.pkl','rb'))
        self.store_type_encoding           = pickle.load(open('parameter/store_type_encoding.pkl','rb'))
        self.model_xgb                     = pickle.load(open('model/model_rossmann_raw.pkl', 'rb') )
        
    def data_cleaning( self, data ):
        
        # rename columns
        cols_old = data.columns
        snake_case = lambda x: inflection.underscore(x)
        cols_new = list(map(snake_case,cols_old))
        data.columns = cols_new

        # data types
        data['date'] = pd.to_datetime(data['date'])

        # fillout NAs        
        data['competition_distance']         = data['competition_distance'].apply( lambda x: 200000.0 if math.isnan(x) else x )
        data['competition_open_since_month'] = data.apply(lambda x: x['date'].month if math.isnan(x['competition_open_since_month']) else x['competition_open_since_month'], axis=1 )
        data['competition_open_since_year']  = data.apply(lambda x: x['date'].year if math.isnan(x['competition_open_since_year']) else x['competition_open_since_year'], axis=1 )
        data['promo2_since_week']            = data.apply(lambda x: x['date'].week if math.isnan(x['promo2_since_week']) else x['promo2_since_week'], axis=1 )         
        data['promo2_since_year']            = data.apply(lambda x: x['date'].year if math.isnan(x['promo2_since_year']) else x['promo2_since_year'], axis=1 ) 
        month_map = { 1 : 'Jan', 2 : 'Feb', 3 : 'Mar', 4 : 'Apr', 5 : 'May', 6 : 'Jun', 7 : 'Jul', 8 : 'Aug', 9 : 'Sept', 10: 'Oct', 11: 'Nov', 12: 'Dec' } 
        data['promo_interval'].fillna(0, inplace=True)
        data['month_map'] = data['date'].dt.month.map( month_map )
        data['is_promo']  = data[['promo_interval','month_map']].apply(lambda x: 0 if x['promo_interval'] == 0 else 1 if x['month_map'] in x['promo_interval'].split(',') else 0, axis=1)

        # change types
        data['competition_open_since_month'] = data['competition_open_since_month'].astype(int)
        data['competition_open_since_year'] = data['competition_open_since_year'].astype(int)
        data['promo2_since_week'] = data['promo2_since_week'].astype(int)
        data['promo2_since_year'] = data['promo2_since_year'].astype(int)
        
        return data
    
    def feature_engineering( self, data ):
        
        data['year'] = data['date'].dt.year
        data['month'] = data['date'].dt.month
        data['day'] = data['date'].dt.day
        data['week_of_year'] = data['date'].dt.weekofyear
        data['year_week'] = data['date'].dt.strftime('%Y-%W')
        data['competition_since'] = data.apply( lambda x: datetime.datetime( year = x['competition_open_since_year'],
                                                                            month = x['competition_open_since_month'], 
                                                                              day = 1), axis=1 )
        data['competition_time_month'] = ( ( data['date'] - data['competition_since'] ) / 30 ).apply( lambda x: x.days ).astype(int)
        data['promo_since'] = data['promo2_since_year'].astype(str) + '-' + data['promo2_since_week'].astype(str)
        data['promo_since'] = data['promo_since'].apply(lambda x: datetime.datetime.strptime(x + '-1', '%Y-%W-%w') - datetime.timedelta(days=7))
        data['promo_time_week'] = ( ( data['date'] - data['promo_since'] ) / 7 ).apply( lambda x: x.days ).astype(int)
        data['assortment'] = data['assortment'].apply(lambda x: 'basic' if x == 'a' else 'extra' if x == 'b' else 'extended')
        data['state_holiday'] = data['state_holiday'].apply(lambda x: 'public_holiday' if x == 'a' else 'easter_holiday' if x == 'b' else 'christmas' if x == 'c' else 'regular_day')

        # variables filtering
        data = data[data['open'] != 0]
        cols_drop = ['open','promo_interval','month_map']
        data = data.drop(cols_drop, axis=1)
        
        return data
    
    def data_preparation( self, data ):

        # rescaling
        data['re_competition_distance'] = self.competition_distance_scaler.transform(data[['competition_distance']].values)
        data['re_year'] = self.year_scaler.transform(data[['year']].values)
        data['re_competition_time_month'] = self.competition_time_month_scaler.transform(data[['competition_time_month']].values)
        data['re_promo_time_week'] = self.promo_time_week_scaler.transform(data[['promo_time_week']].values)

        # encoding
        data = pd.get_dummies(data, prefix=['state_holiday'], columns=['state_holiday'])
        data['store_type'] = self.store_type_encoding.transform(data['store_type'])
        assortment = { 'basic': 1,'extra': 2, 'extended': 3 }
        data['assortment'] = data['assortment'].map(assortment)

        # nature transformation
        data['day_of_week_sin'] = data['day_of_week'].apply(lambda x: np.sin( x * ( 2 * np.pi / 7 ) ) )
        data['day_of_week_cos'] = data['day_of_week'].apply(lambda x: np.cos( x * ( 2 * np.pi / 7 ) ) )
       
        data['day_sin'] = data['day'].apply(lambda x: np.sin( x * ( 2 * np.pi / 30 ) ) )
        data['day_cos'] = data['day'].apply(lambda x: np.cos( x * ( 2 * np.pi / 30 ) ) )

        data['month_sin'] = data['month'].apply(lambda x: np.sin( x * ( 2 * np.pi / 12 ) ) )
        data['month_cos'] = data['month'].apply(lambda x: np.cos( x * ( 2 * np.pi / 12 ) ) )

        data['week_of_year_sin'] = data['week_of_year'].apply(lambda x: np.sin( x * ( 2 * np.pi / 52 ) ) )
        data['week_of_year_cos'] = data['week_of_year'].apply(lambda x: np.cos( x * ( 2 * np.pi / 52 ) ) )
        
        cols_selected = ['store', 'promo', 'store_type', 'assortment', 'competition_distance', 'competition_open_since_month', 'competition_open_since_year', 'promo2', 'promo2_since_week',
        'promo2_since_year', 'competition_time_month', 'promo_time_week', 're_competition_distance', 're_competition_time_month', 're_promo_time_week', 'day_of_week_sin', 'day_of_week_cos',
        'day_sin', 'day_cos', 'month_sin', 'month_cos', 'week_of_year_sin', 'week_of_year_cos']
        
        return data[cols_selected]
    
    def prediction( self, model, original_data, test_data ):

        # prediction
        pred = model.predict(test_data)        
        # join pred into the original data
        original_data['prediction'] = np.expm1(pred)
        
        return original_data.to_json(orient='records', date_format='iso')
