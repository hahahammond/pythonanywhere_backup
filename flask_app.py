# Import libraries
import os
from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import lxml.html
import requests
import re
import operator

# Initialize the Flask application
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

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

        # Figure out if URL includes number or term text, then find and clean MeSH Heading
        root = lxml.html.fromstring(r.content)
        term_text = '?term='
        if term_text in url:
            mesh = root.xpath('//h1/span/text()')
        else:
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

@app.route('/pmidfinder')
def pmidfinder():
    return render_template('pmidfinder.html')

@app.route('/pmidfinderresult',methods = ['POST', 'GET'])
def pmidfinderresult():
    if request.method == 'POST':

        # Get URL for BU Profile page from the form
        page_url = request.form['page_url']

        # Make request and extract all URLS from page and person's name
        r = requests.get(page_url)
        tree = lxml.html.fromstring(r.content)
        all_urls = tree.xpath('//span/a/@href')
        person = tree.xpath('//span[@id="ctl00_lbl_main_heading"]/text()')[0]

        # Initiate PubMed URL list
        pubmed_url_list = []

        # Find URLs pointing to PubMed articles and add to list
        for url in all_urls:
            pubmed_url = re.findall('//www.ncbi.nlm.nih.gov/pubmed/.*$', url)
            if pubmed_url:
                pubmed_url_list.append(pubmed_url[0])

        # Initiate PMID counter and PMID list
        pmid_counter = 0
        pmid_list = []

        # Find PMIDs in PubMed article URLs and update PMID counter
        for raw_pubmed_url in pubmed_url_list:
            clean_pubmed_url = raw_pubmed_url.replace('//www.ncbi.nlm.nih.gov/pubmed/', '')
            pmid_list.append(clean_pubmed_url)
            pmid_counter += 1

        return render_template("pmidfinderresult.html", person=person, page_url=page_url, pmid_counter=pmid_counter, pmid_list=pmid_list)

@app.route('/meshminer')
def meshminer():
    return render_template('meshminer.html')

@app.route('/meshminerresult',methods = ['POST', 'GET'])
def meshminerresult():
    if request.method == 'POST':
        # Create empty dictionary for MeSH terms
        mesh_tally = {}

        # Get PMID list from form input
        if request.form['pmid_entry'] != '':
            pmid_str = request.form['pmid_entry']
        else:

            test_file = request.files['pmid_file']
            file_content = test_file.read()
            pmid_str=file_content.decode('utf8').replace('\n', ' ')

            # with open(file_content, 'r') as input_file:
            #     pmid_str=input_file.read().replace('\n', ' ')

        pmid_list = re.findall(r'\d+', pmid_str)

        for pmid in pmid_list:
            # Assemble URLs for articles
            url = 'https://www.ncbi.nlm.nih.gov/pubmed/' + str(pmid)

            # Make request
            r = requests.get(url)
            root = lxml.html.fromstring(r.content)

            # Find MeSH terms
            mesh_terms = root.xpath('//li/a[@alsec="mesh"]/text()')
            for term in mesh_terms:
                if '/' in term:
                    term = term.rsplit('/')[0]
                if '*' in term:
                    term = term.rsplit('*')[0]
                if term in mesh_tally.keys():
                    mesh_tally[term] += 1
                else:
                    mesh_tally[term] = 1

        # Sort mesh_tally dictionary by value in ascending order
        sorted_mesh_tally = sorted(mesh_tally.items(), key=lambda x: (x[1],x[0]), reverse=True)

        return render_template("meshminerresult.html", sorted_mesh_tally=sorted_mesh_tally)


if __name__ == '__main__':
    app.run(debug = True)