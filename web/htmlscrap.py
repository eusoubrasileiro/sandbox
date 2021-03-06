#html web-scraping

import time
from requests_ntlm import HttpNtlmAuth
import re

import os, sys
import requests
from requests.adapters import HTTPAdapter

from bs4 import BeautifulSoup
from urllib.parse import urljoin

import pandas as pd
from datetime import datetime
import re


class wPage: # html  webpage scraping with soup and requests
    def __init__(self): # requests session
        self.session = requests.Session()

    def findAllnSave(self, pagefolder, tag2find='img', inner='src', verbose=False):
        if not os.path.exists(pagefolder): # create only once
            os.mkdir(pagefolder)
        for res in self.soup.findAll(tag2find):   # images, css, etc..
            try:
                if not res.has_attr(inner): # check if inner tag (file object) exists
                    continue # may not exist
                # dealing with weird resource names (RENAME it to save as a file)
                filename = re.sub('\W+', '', os.path.basename(res[inner])) # clean special chars
                # fileurl = url.scheme + '://' + url.netloc + urljoin(url.path, res.get(inner))
                fileurl = urljoin(self.url, res.get(inner))
                # rename html ref so can move html and folder of files anywhere
                res[inner] = os.path.join(os.path.basename(pagefolder), filename)
                # like a '<script' tag where the script is inplace
                filepath = os.path.join(pagefolder, filename)
                if not os.path.isfile(filepath): # was not already saved
                    with open(filepath, 'wb') as file:
                        filebin = self.session.get(fileurl)
                        file.write(filebin.content)
            except Exception as exc:
                if verbose:
                    print(exc, '\n', file=sys.stderr)

    def save(self, pagefilename='page'):
        """
        save html page and supported contents
        pagefilename  : specified folder
        """
        self.url = self.response.url # needed above findAllnSave
        self.soup = BeautifulSoup(self.response.text, features="lxml")
        pagefolder = pagefilename+'_files' # page contents
        self.findAllnSave(pagefolder, 'img', inner='src')
        self.findAllnSave(pagefolder, 'link', inner='href')
        self.findAllnSave(pagefolder, 'script', inner='src')
        with open(pagefilename+'.html', 'w') as file:
            file.write(self.soup.prettify())

    def post(self, arg, save=True, **kwargs):
        """save : save response overwriting the last"""
        resp = self.session.post(arg, **kwargs)
        if save:
            self.response = resp
        return resp

    def get(self, arg, save=True, **kwargs):
        """save : save response overwrites the last"""
        resp = self.session.get(arg, **kwargs)
        if save:
            self.response = resp
        return resp

class wPageNtlm(wPage): # overwrites original class for ntlm authentication
    def __init__(self, user, passwd):
        """ntlm auth user and pass"""
        super().__init__()
        self.user = user
        self.passwd = passwd
        self.session.auth = HttpNtlmAuth(user, passwd)


def formdataPostAspNet(response, formcontrols):
    """
    Creates a formdata dict based on dict of formcontrols to make a post request
    to an AspNet html page. Use the previous html get `response` to extract the AspNet
    states of the page.

    response : from page GET request
    formcontrols : dict from webpage with values assigned
    """
    # get the aspnet form data neeed with bsoup
    soup = BeautifulSoup(response.content, features="lxml")
    aspnetstates = ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION', '__EVENTTARGET',
                    '__EVENTARGUMENT', '__VIEWSTATEENCRYPTED' ];
    formdata = {}
    for aspnetstate in aspnetstates: # search for existing aspnet states and get its values when existent
        result = soup.find('input', {'name': aspnetstate})
        if not (result is None):
            formdata.update({aspnetstate : result['value']})

    # include aditional form controls params
    formdata.update(formcontrols)
    #return formdata
    return formdata


#### HTML PARSING DATA
# BeautifulSoup Power

# Table parsing with bs4
def tableDataText(table):
    """Parse a html segment started with tag <table>
    followed by multiple <tr> (table rows) and
    inner <td> (table data) tags
    returns: a list of rows with inner collumns
    Note: one <th> (table header/data) accepted in the first row"""
    rows = []
    trs = table.find_all('tr')
    headerow = [td.get_text(strip=True) for td in trs[0].find_all('th')] # header row
    if headerow: # if there is a header row include first
        rows.append(headerow)
        trs = trs[1:]
    for tr in trs: # for every table row
        rows.append([td.get_text(strip=True) for td in tr.find_all('td')]) # data row
    return rows


def dictDataText(soup, data_tags, strip=True):
    """
    Parse Html tags from dict `data_tags` like bellow:

    data_tags = {
        'tipo'                  : ['span',  { 'id' : 'ctl00_conteudo_lblTipoRequerimento'} ],
        'eventos'               : ['table', { 'id' : 'ctl00_conteudo_gridEventos'} ]
    }

    format
       "data name"  :    ["tagname" , { "attribute name" : "attribute value" }]

    Will be used by BeautifulSoup like
         `soup.find(data_tags['tipo'][0], data_tags['tipo'][1])`

    Return:
        dictionary of data_names with parsed data including tables using `tableDataText`

    """
    dados = {}
    for data in data_tags:
        result = soup.find(data_tags[data][0],
                                data_tags[data][1])
        if not (result is None):
            if data_tags[data][0] == 'table': # parse table if table
                result = tableDataText(result)
            else:
                result = result.text
                if strip: # strip text
                    result = result.strip()
            dados.update({data : result})
    return dados
