from flask import Flask, request, Response, send_file
from rossmann.Rossmann import Rossmann
from reports.Reports import Reports
import pandas as pd
import pickle
import os

# loading model
model = pickle.load( open('model/model_rossmann_raw.pkl', 'rb') )

app = Flask(__name__)

@app.route( '/predict', methods=['POST'] )
def rossmann_predict():
    
    raw_predict = request.get_json()    
    if raw_predict:  
        raw_data = pd.DataFrame(raw_predict)        
        rossmann = Rossmann()
        data = rossmann.data_cleaning(raw_data)
        data = rossmann.feature_engineering(data)
        data_predict = rossmann.data_preparation(data)
        data_predicted = rossmann.prediction(model, data, data_predict)
        
        return data_predicted        
    else:
        
        return Response('{}',status=200,mimetype='application/json')

@app.route( '/reports', methods=['POST'] )
def rossmann_reports():

    raw_reports = request.get_json()    
    if raw_reports:
        raw_data = pd.DataFrame(raw_reports)    
        reports = Reports()
        data = reports.data_transformation(raw_data)
        reports.plots(data=data)

        return send_file('plots.png', mimetype='image/png')

    else:
        return Response('{}',status=200,mimetype='application/json')    
    
if __name__ == '__main__':
    port = os.environ.get('PORT',5000)
    app.run(host='0.0.0.0',port=port)