#!/usr/bin/env python3
# encoding: utf-8

import json
from math import sqrt

from cortexutils.responder import Responder
from thehive4py.api import TheHiveApi
from mdutils.mdutils import MdUtils
from md2pdf.core import md2pdf


class TomaDecision(Responder):
    def __init__(self):
        Responder.__init__(self)
        self.localizacion = self.get_param('config.localizacion')
        self.loccss = self.get_param('config.localizacion_css')
        self.algoritmo = self.get_param('config.algoritmo')
        self.TheHive_instance = self.get_param(
                'config.TheHive_instance', '')
        self.TheHive_API_key = self.get_param(
                'config.TheHive_API_key', '')
        self.api = TheHiveApi(self.TheHive_instance, self.TheHive_API_key)
        self.COAjson = self.get_param(
                'config.lista_de_COA', '')

    """
       funcion que compara los keywords de la alerta con los de los COAs, 
       si coincide alguno el COA con ese keyword se anade a la lista
       de COAs que se va a tener en cuenta. 
       Se cuentan los keywords que coinciden por COA y se sacan por numKey.
    """
    def compKey(self, COAjson, alert_keywords):
        listCOA = []
        numKey = []
        for coa in COAjson:
            for coakey in coa['keywords']:
                if coakey in alert_keywords:
                    listCOA.append(coa)
                    break
        if not listCOA:
            listCOA = COAjson
            numKey = [1]*len(listCOA)
        else:
            for coa in listCOA:
                numK = 0
                for coakey in coa['keywords']:
                    if coakey in alert_keywords:
                        numK +=1
                numKey.append(numK)

        return listCOA, numKey
    
    """
       compara la severidad de la alerta con la severidad de los COAs.
       Si el impacto del COA es mayor a la severidad de la alerta dicho COA
       se descarta
    """
    def compSev(self,listCOA,alert_severity,numKey):
        listCOA2 = []
        numKey2 = []
        for coa in listCOA:
            if (alert_severity > coa['impacto']):
                listCOA2.append(coa)
                numKey2.append(numKey[listCOA.index(coa)])
        return listCOA2, numKey2

    """
       calcula el coste de aplicar los diferentes COAs
       devuelve un diccionario con el COA y su coste final
    """
    def calcularCoste(func):
    	def wrapper(self, listCOA, numKey, similarcases_tags, alert_severity):
            costeFinal = []
            for coa in listCOA:
                factSim = 1
                nameCOA = coa['name'].split('-')
                for tag in similarcases_tags:
                    if nameCOA[0] in tag:
                        factSim = 0.5
                costeFinal.append(func(coa, numKey, alert_severity, factSim))
            listCOA = list(zip([round(num,2) for num in costeFinal],listCOA))
            return listCOA
    	return wrapper

    #formula basica para calcular el coste de los COA
    @calcularCoste
    def formBase(coa, numKey, alert_severity, factSim):
        suma = (coa['coste'] + coa['esfuerzo'] + coa['complejidad'])
        tiempo = sqrt(coa['tiempo'])
        impact = coa['impacto']
        num = suma * tiempo * impact
        denom = alert_severity * numKey[listCOA.index(coa)]
        if denom == 0:
            denom = 0.01
        coste = (num / denom) * factSim
        return coste
    
    #calcula el coste de los COA asignando un peso mayor al impacto
    @calcularCoste
    def formImpact(coa, numKey, alert_severity, factSim):
        suma = (coa['coste'] + coa['esfuerzo'] + coa['complejidad'])
        tiempo = sqrt(coa['tiempo'])
        impact = sqrt(2) * coa['impacto']
        num = (suma + tiempo) * impact
        denom = alert_severity * numKey[listCOA.index(coa)]
        if denom == 0:
            denom = 0.01
        coste = (num / denom) * factSim                                                                                                
        return coste

    #calcula el coste de los COA asignando un peso mayor al tiempo de implementacion
    @calcularCoste
    def formTime(coa, numKey, alert_severity, factSim):
        suma = (coa['coste'] + coa['esfuerzo'] + coa['complejidad'])
        tiempo = 2 * sqrt(coa['tiempo'])
        impact = coa['impacto']
        num = suma * tiempo * impact
        denom = alert_severity * numKey[listCOA.index(coa)]
        if denom == 0:
            denom = 0.01
        coste = (num / denom) * factSim                                                                                                
        return coste

    #calcula el coste de los COA asignando un peso mayor a la complejidad 
    @calcularCoste
    def formComp(coa, numKey, alert_severity, factSim):
        suma = (coa['coste'] + coa['esfuerzo'] + 3 * coa['complejidad'])
        tiempo = sqrt(coa['tiempo'])
        impact = coa['impacto']
        num = suma * tiempo * impact
        denom = alert_severity * numKey[listCOA.index(coa)]
        if denom == 0:
            denom = 0.01
        coste = (num / denom) * factSim                                                                                                
        return coste

    #calcula el coste de los COA asignando un peso mayor al esfuerzo
    @calcularCoste
    def formEffort(coa, numKey, alert_severity, factSim):
        suma = (coa['coste'] + 3 * coa['esfuerzo'] + coa['complejidad'])
        tiempo = sqrt(coa['tiempo'])
        impact = coa['impacto']
        num = suma * tiempo * impact
        denom = alert_severity * numKey[listCOA.index(coa)]
        if denom == 0:
            denom = 0.01
        coste = (num / denom) * factSim                                                                                                
        return coste

    #calcula el coste total de los COA asignando un peso mayor al coste basico
    @calcularCoste 
    def formCost(coa, numKey, alert_severity, factSim):
        suma = (3 * coa['coste'] + coa['esfuerzo'] + coa['complejidad'])
        tiempo = sqrt(coa['tiempo'])
        impact = coa['impacto']        
        num = suma * tiempo * impact  
        denom = alert_severity * numKey[listCOA.index(coa)]
        if denom == 0:
            denom = 0.01
        coste = (num / denom) * factSim                                                                                                
        return coste

    #calcula el coste de los COA asignando un peso mayor a la gravedad de la alerta
    @calcularCoste 
    def formSevAlert(coa, numKey, alert_severity, factSim):
        suma = (coa['coste'] + coa['esfuerzo'] + coa['complejidad'])
        tiempo = sqrt(coa['tiempo'])
        impact = coa['impacto']        
        num = suma * tiempo * impact  
        denom = sqrt(2) * alert_severity * numKey[listCOA.index(coa)]
        if denom == 0:
            denom = 0.01
        coste = (num / denom) * factSim                                                                                                
        return coste


    def run(self):
        Responder.run(self)
        
        alert_keywords = self.get_param('data.tags')
        alert_title = self.get_param('data.title')
        alert_description = self.get_param('data.description')
        alert_type = self.get_param('data.type')
        alert_source = self.get_param('data.source')
        alert_severity = int(self.get_param('data.severity'))
        alert_id = self.get_param('data.id')
        response = self.api.get_alert(alert_id + '?similarity=1')
        similarcases_title = [i.get('title', None) for i in list(response.json().get("similarCases"))]
        similarcases_tags = [i.get('tags', None) for i in list(response.json().get("similarCases"))]
        similarcases = dict(zip(similarcases_title, similarcases_tags))
        observable_datatype = [i.get('dataType',None) for i in list(response.json().get("artifacts"))]
        observable_data = [i.get('data', None) for i in list(response.json().get("artifacts"))]
        observable_list = dict(zip(observable_datatype, observable_data))
        alert_dic = {'Casos similares': similarcases, 'Observables de la alerta':observable_list}
        
        with open(self.COAjson, 'r') as json_file:
            json_load = json.load(json_file)
        COAjson = json_load['COAs']
        
        global listCOA
        listCOA1, numKey = self.compKey(COAjson, alert_keywords)
        listCOA, numKey = self.compSev(listCOA1, alert_severity, numKey)
        if self.algoritmo == 2:
            listCOA = self.formImpact(listCOA, numKey, similarcases_tags, alert_severity)
        elif self.algoritmo == 3:
            listCOA = self.formTime(listCOA, numKey, similarcases_tags, alert_severity)
        elif self.algoritmo == 4:
            listCOA = self.formComp(listCOA, numKey, similarcases_tags, alert_severity)
        elif self.algoritmo == 5:
            listCOA = self.formEffort(listCOA, numKey, similarcases_tags, alert_severity)
        elif self.algoritmo == 6:
            listCOA = self.formCost(listCOA, numKey, similarcases_tags, alert_severity)
        elif self.algoritmo == 7:
            listCOA = self.formSevAlert(listCOA, numKey, similarcases_tags, alert_severity)
        else:  
            listCOA = self.formBase(listCOA, numKey, similarcases_tags, alert_severity)
        
        listCOA = sorted(listCOA, key=lambda x:x[0])
        
        
        fileOut = str(self.localizacion) + "/" + str(alert_title)

        mdFile = MdUtils(file_name=fileOut, title='')

        mdFile.new_line('---- \n')
        mdFile.new_header(level=1, title=str(alert_title))

        mdFile.new_header(level=2, title='Alerta Detectada')
        mdFile.write("- **Título:** " + str(alert_title) + "\n")
        mdFile.write("- **Descripción:** " + str(alert_description) + "\n")
        mdFile.write("- **Keywords:** " + str(alert_keywords) + "\n")
        mdFile.write("- **Tipo:** " + str(alert_type) + "\n")
        mdFile.write("- **Fuente:** " + str(alert_source) + "\n")
        mdFile.write("- **Gravedad:** " + str(alert_severity) + "\n")
        mdFile.write("- **Observables:** " + str(observable_list) + "\n")
        mdFile.write("- **Casos similares:** " + str(similarcases) + "\n")

        mdFile.new_line('')
        mdFile.write('---- \n')
        mdFile.new_line('')

        mdFile.new_header(level=2, title='COAs - Lista Ordenada')
        if len(listCOA1) == len(COAjson):
            mdFile.write("No hay palabras clave comunes \n")
        if len(listCOA) == 0:
            mdFile.write("Todos los COA suponen un impacto mayor al de la alerta \n")
        num = 1
        for coste, coa in listCOA:
            mdFile.write(str(num) + ". " + str(coa['name']) + "\n")
            num +=1

        mdFile.new_line('')
        mdFile.write('---- \n')
        mdFile.new_line('')

        mdFile.new_header(level=2, title='COAs - Información detallada')       
        ind=0
        for coste, coa in listCOA:
            ind +=1 
            mdFile.new_header(level=3, title=str(ind) + ". " + str(coa['name']))
            mdFile.write(str(coa['descripcion']) + " \n")
            mdFile.new_line("**Keywords:** " + str(coa['keywords']))
            mdFile.write('  \n')
            mdFile.write("**Complejidad:** " + str(coa['complejidad']))
            mdFile.write('  \n')
            mdFile.write("**Tiempo estimado:** " + str(coa['tiempo']) +"min")
            mdFile.write('  \n')
            mdFile.write("**Coste:** " + str(coa['coste']))
            mdFile.write('   \n')
            mdFile.write("**Esfuerzo:** " + str(coa['esfuerzo']))
            mdFile.write('   \n')
            mdFile.write("**Impacto al sistema:** " + str(coa['impacto']))
            mdFile.write('  \n')
            mdFile.write("**Coste Final:** " + str(coste))
            mdFile.write('  \n')
            mdFile.new_line(' ')

        mdFile.create_md_file()

        md2pdf(fileOut + ".pdf",
               md_content=None,
               md_file_path=fileOut + ".md",
               css_file_path=self.loccss,
               base_url=None)
               
        report = listCOA
        self.report({'report': report})
     

    def operations(self,raw):
        tagCOA = str(listCOA[0][1]['name']).split('-')
        return [self.build_operation('AddTagToAlert', tag=str(tagCOA[0])), self.build_operation('MarkAlertAsRead')]
        

if __name__ == '__main__':
    TomaDecision().run()

