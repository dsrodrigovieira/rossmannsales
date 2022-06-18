from flask import Response, request, Flask
import pandas as pd
import requests
import json
import os

TOKEN = ''
REPLY_OPTIONS = ('See details','Search other store', 'Leave')

def parse_message( message ):    

    chat_id = message['message']['chat']['id']
    text = message['message']['text']

    text = text.replace('/','')

    try:
        text = int(text)

    except ValueError:
        if REPLY_OPTIONS.__contains__(text):
            text
        elif text != 'start':
            text = 'error'
        else: text

    return chat_id, text

def load_dataset( store_id ):
    # loading test dataset
    df_test_raw = pd.read_csv('data/test.csv')
    df_store_raw = pd.read_csv('data/store.csv')

    # merge test + store datasets
    data = pd.merge(df_test_raw, df_store_raw, how='left', on='Store')

    # choose store for prediction
    data = data[data['Store'] == store_id]

    if data.empty:
        data = 'error'
    else:
        # remove closed days
        data = data[(data['Open'] != 0) & (~data['Open'].isnull())]
        data = data.drop('Id', axis=1)

        # convert Dataframe to json
        data = json.dumps(data.to_dict(orient='records'))

    return data

def predict( data ):
    # API call
    url = 'https://dsr-rossmannsales.herokuapp.com/predict'
    header = {'Content-type': 'application/json'}
    data = data

    r = requests.post(url, data=data, headers=header)

    return pd.DataFrame(r.json(), columns=r.json()[0].keys())

def plots( data ):    
    # API call
    url = 'https://dsr-rossmannsales.herokuapp.com/reports'
    header = {'Content-type': 'application/json'}

    r = requests.post(url, data=data, headers=header)

    file = open('reports/plots.png', 'wb')
    file.write(r.content)
    file.close()

    return None

def send_message( text, chat_id ): 
    payload = { 'chat_id': chat_id, 'text': text }    

    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TOKEN)
    r = requests.post( url, data=payload )

    return None

def send_photo( chat_id ):
    payload = {
        'chat_id': chat_id,        
        'caption': "Here's detailed info"
    }

    file = {
        'photo': open('reports/plots.png', 'rb')
    }

    url = 'https://api.telegram.org/bot{}/sendPhoto'.format(TOKEN)
    r = requests.post( url, data=payload, files=file )

    return None

def reply_message( chat_id ):

    header = {'Content-type': 'application/json'}
    
    payload = {'chat_id': chat_id, 'text': 'Select an option below',
                'reply_markup': { 'keyboard':
                                [[{'text':REPLY_OPTIONS[0]}],
                                    [{'text':REPLY_OPTIONS[1]}],
                                    [{'text':REPLY_OPTIONS[2]}]],
                                    'resize_keyboard': True,
                                    'one_time_keyboard':True }}

    data = json.dumps(payload)

    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TOKEN)
    r = requests.post( url, headers=header, data=data)

    return r.json()

def reply_image( chat_id ):

    header = {'Content-type': 'application/json'}
    
    payload = {'chat_id': chat_id, 'text': 'Select an option below',
                'reply_markup': { 'keyboard':
                                [[{'text':REPLY_OPTIONS[1]}],
                                    [{'text':REPLY_OPTIONS[2]}]],
                                    'resize_keyboard': True,
                                    'one_time_keyboard':True }}

    data = json.dumps(payload)

    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TOKEN)
    r = requests.post( url, headers=header, data=data)

    return r.json()

# API initialize
app = Flask( __name__ )
@app.route('/',methods=['GET','POST'])

def index():
    if request.method == 'POST':
        
        message = request.get_json() 
        
        chat_id, store_id = parse_message(message)

        if str(store_id).isnumeric():
            # loading data
            data = load_dataset(store_id)
            if data != 'error':
                send_message('Loading data...', chat_id)
                # prediction
                pred = predict(data)
                pred.to_csv('data/pred.csv',index=False)                
                # calculation
                _pred = pred[['store','prediction']].groupby('store').sum().reset_index()
                # send message
                msg = 'Store number {} will sell US${:,.2f} in the next 2 weeks'.format(_pred['store'].values[0], _pred['prediction'].values[0]) 
                send_message(msg, chat_id)
                reply_message(chat_id)
                return Response('OK', status=200)
            else:
                send_message('An error ocurred. Please try other store.',chat_id)
                return Response('OK', status=200)
        else:
            if store_id == 'start':
                send_message('Send store ID', chat_id )  
                return Response('OK', status=200)  
            if store_id == REPLY_OPTIONS[0]:
                data = json.dumps(pd.read_csv('data/pred.csv').to_dict(orient='records'))
                plots(data)
                send_message('Sending image...', chat_id )
                send_photo(chat_id)
                reply_image(chat_id)
                return Response('OK', status=200)
            if store_id == REPLY_OPTIONS[1]:
                send_message('Send store ID', chat_id )
                return Response('OK', status=200)
            if store_id == REPLY_OPTIONS[2]:
                send_message('Thanks for using this application!', chat_id ) 
                return Response('OK', status=200)             
            else:
                send_message('Are you sure this is a store ID?', chat_id )
            return Response('OK', status=200)   

    else:
        send_message(chat_id, '<h1>Rossmann Telegram BOT</h1>')
        return Response('OK', status=200)

if __name__ == '__main__':
    port = os.environ.get('PORT',5000)
    app.run(host='0.0.0.0', port=port)