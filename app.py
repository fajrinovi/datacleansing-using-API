from flask import Flask, render_template, request, flash
from flask import request, url_for, redirect, jsonify, send_from_directory
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
import pandas as pd
import re
import sqlite3
from cleansing import cleanse_text

#connect ke database dan file csv
conn = sqlite3.connect('datacleansing.db',check_same_thread=False)
cur = conn.cursor()

#mendefinisikan dan mengeksekusi query untuk tabel data kalau belum ada
#tabel data berisi kolom text kotor dan yang sudah dibersihkan 
conn.execute('''CREATE TABLE IF NOT EXISTS record(id_text INTEGER AUTO INCREMENT, text varchar(255), text_clean varchar(255), PRIMARY KEY (id_text));''')

flask_application = Flask(__name__)

flask_application.json_encoder = LazyJSONEncoder
swagger_template = dict(
info = {
    'title' : LazyString(lambda: 'API Dokumentasi Data Preprocessing'),
    'version' : LazyString(lambda: '1.0.0'),
    'description' : LazyString(lambda: 'Dokumentasi preprocessing data text dan file'),    
},
    host = LazyString(lambda: request.host)
)

swagger_config ={
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json'
        }
    ],
    "static_url_path": "/flassger_static",
    "swagger_ui": True,
    "specs_route":"/docs/"
}

swagger = Swagger(flask_application, template=swagger_template, config=swagger_config)

@flask_application.route("/", methods=['GET','POST'])
def home():
	return render_template("index.html", content="Guys")

@flask_application.route('/text', methods=['POST'])
@swag_from("docs/text_processing.yml", methods=['POST'])
def text_preprocessing():
    
    #mendapatkan inputan text
    text = request.form.get('text')
    #proses cleansing dengan regex
    text_clean = cleanse_text(text)
    #\s untuk whitespace character [ \t\r\n\f]
    #\d untuk angka
    #\W untuk simbol

    #mendefinisikan dan melakukan eksekusi query dari original text ke yang sudah bersih
    conn.execute("INSERT INTO record (text, text_clean) VALUES (?,?)",(text,text_clean))
    conn.commit()

    #Define response API
    json_response={
        'status_code': 200,
        'description': 'text cleansing',
        'data': text_clean, 
    }

    response_data = jsonify(json_response)
    return response_data

@flask_application.route("/upload", methods=['GET','POST'])
def upload_file():
    #import file
    if request.method == 'POST':
        uploadcsv = pd.read_csv(request.files['uploadcsv'], encoding='latin-1',on_bad_lines='skip') 
        uploadcsv = uploadcsv.iloc[:, 0]
        uploadcsv = uploadcsv.dropna()
        text_array = []
        
        #proses cleaning dengan memanggil fungsi cleance_text
        for text in uploadcsv:
            cleaned_text = cleanse_text(text)
            obj_text = {
                'cleaned_text': cleaned_text,
                'original_text': text
            }
            text_array.append(obj_text)
            #hasil cleaning diinsert ke dalam db
            conn.cursor().execute("insert into record (text, text_clean) values(?, ?)", (text, cleaned_text))
            conn.commit()

    return render_template("upload.html")

@flask_application.route("/dictionary", methods=['GET','POST'])
#fungsi untuk menampilkan text yang belum di cleaning dan yang sudah
def show_list():
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM record")

    rows = cur.fetchall();
    return render_template("dictionary.html", rows=rows)


if __name__ == '__main__':
	flask_application.run()