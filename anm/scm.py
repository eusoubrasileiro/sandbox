import sys
from bs4 import BeautifulSoup

sys.path.append("..") # Adds higher directory to python modules path.
from web import htmlscrap as hscrap
from datetime import datetime

class Processo:
    # static field
    scm_data_tags = { # "data name" ; soup.find fields( "tag", "attributes")
        'prioridade'            : ['span',  { 'id' : "ctl00_conteudo_lblDataPrioridade"} ],
        'area'                  : ['span',  { 'id' : 'ctl00_conteudo_lblArea'} ],
        'UF'                    : ['span',  { 'id' : 'ctl00_conteudo_lblUF'} ],
        'processos_associados'  : ['table', { 'id' : 'ctl00_conteudo_gridProcessosAssociados'} ],
        'substancias'           : ['table', { 'id' : 'ctl00_conteudo_gridSubstancias'} ],
        'eventos'               : ['table', { 'id' : 'ctl00_conteudo_gridEventos'} ],
        'municipios'            : ['table', { 'id' : 'ctl00_conteudo_gridMunicipios'} ]
    }
    def __init__(self, processostr, wpage):
        self.processostr = processostr
        self.processo_number = processostr.split('/')[0].replace('.', '')
        self.processo_year = processostr.split('/')[1]
        self.wpage = wpage

    @classmethod # not same as @staticmethod (has a self)
    def fromNumberYear(self, processo_number, processo_year, wpage):
        processostr = processo_number + r'/' + processo_year
        return self(processostr, wpage)

    @staticmethod
    def specifyData(data=['prioridade', 'UF']):
        """return scm_data_tags from specified data labels"""
        return dict(zip(data, [ Processo.scm_data_tags[key] for key in data ]))

    def dadosBasicosRetrieve(self):
        """   Get & Post na página dados do Processo do Cadastro  Mineiro (SCM)
        """
        self.wpage.get('https://sistemas.dnpm.gov.br/SCM/Intra/site/admin/dadosProcesso.aspx')
        formcontrols = {
            'ctl00$scriptManagerAdmin': 'ctl00$scriptManagerAdmin|ctl00$conteudo$btnConsultarProcesso',
            'ctl00$conteudo$txtNumeroProcesso': self.processostr,
            'ctl00$conteudo$btnConsultarProcesso': 'Consultar',
            '__VIEWSTATEENCRYPTED': ''}
        formdata = hscrap.formdataPostAspNet(self.wpage.response, formcontrols)
        self.wpage.post('https://sistemas.dnpm.gov.br/SCM/Intra/site/admin/dadosProcesso.aspx',
                      data=formdata)
        return self.wpage

    def dadosPoligonalRetrieve(self):
        formcontrols = {
            'ctl00$conteudo$btnPoligonal': 'Poligonal',
            'ctl00$scriptManagerAdmin': 'ctl00$scriptManagerAdmin|ctl00$conteudo$btnPoligonal'}
        formdata = hscrap.formdataPostAspNet(self.wpage.response, formcontrols)
        self.wpage.post('https://sistemas.dnpm.gov.br/SCM/Intra/site/admin/dadosProcesso.aspx',
                      data=formdata)
        return self.wpage

    def dadosBasicosGet(self, data_tags=None):
        if not hasattr(self, 'dados'):
            self.dadosBasicosRetrieve()
            self.dados = {}
        if data_tags is None: # data tags to fill in 'dados' with
            data_tags = self.scm_data_tags
        soup = BeautifulSoup(self.wpage.response.text, features="lxml")
        for data in data_tags:
            result = soup.find(data_tags[data][0],
                                    data_tags[data][1])
            if not (result is None):
                if data_tags[data][0] == 'table': # parse table if table
                    result = hscrap.tableDataText(result)
                else:
                    result = result.text
                self.dados.update({data : result})
        return self.dados

    def dadosBasicosGetMissing(self):
        """obtém dados faltantes (se houver) pelo processo associado (pai):
           - UF
           - substancias
        """
        if not hasattr(self, 'dados'):
            self.dadosBasicosGet()
        # cant get missing without parent
        if self.dados['processos_associados'][0][0] == "Nenhum processo associado.":
            return False
        missing = []
        if self.dados['UF'] == "":
            missing.append('UF')
        if self.dados['substancias'][0][0] == 'Nenhuma substância.':
            missing.append('substancias')
        if self.dados['municipios'][0][0] == 'Nenhum município.':
            missing.append('municipios')
        miss_data_tags = Processo.specifyData(missing)
        # processo father
        fathername = self.dados['processos_associados'][1][5]
        if fathername == self.processostr: # doesn't have father
            return False
        father = Processo(fathername, self.wpage)
        father.dadosBasicosGet(miss_data_tags)
        self.dados.update(father.dados)
        del father
        return self.dados

    def getPrioridade(self):
        if not (hasattr(self, 'dados')):
            self.dadosBasicosGet()
        self.prioridade = datetime.strptime(self.dados['prioridade'], "%d/%m/%Y %H:%M:%S")
        return self.prioridade