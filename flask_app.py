# Import libraries
from flask import Flask, render_template, request
import lxml.html
import requests
import re

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/meshmash')
def meshmash():
    return render_template('meshmash.html')

@app.route('/meshmashresult',methods = ['POST', 'GET'])
def meshmashresult():
    if request.method == 'POST':
        # Get URL for MeSH page from form
        url = request.form['raw_url']

        # Remove ezproxy from URL if necessary
        ezproxy = 'https://www-ncbi-nlm-nih-gov.ezproxy.bu.edu/'
        no_ezproxy = 'https://www.ncbi.nlm.nih.gov/'

        if ezproxy in url:
            url = url.replace(ezproxy, no_ezproxy)

        # Make request
        r = requests.get(url)

        # Find and clean MeSH Heading
        root = lxml.html.fromstring(r.content)
        mesh = root.xpath('//h1/text()')
        clean_mesh = mesh[0].replace("'", "")

        # Find Entry Terms
        entry_terms = root.xpath('//li/text()')

        # Compile output string
        ored_output = '"' + clean_mesh + '"[Mesh]'

        for entry_term in entry_terms:
            clean_entry_term = entry_term.replace("'", "")
            ored_output += ' OR ' + clean_entry_term

        return render_template("meshmashresult.html",url=url, clean_mesh=clean_mesh, ored_output=ored_output)

if __name__ == '__main__':
    app.run(debug = True)