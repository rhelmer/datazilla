#####
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#####
import datetime
import time

from datazilla.model.Model import Model

class DatazillaModel(Model):

   @staticmethod
   def getIdString(idList):
      ####
      # idList = [1,2,3,4,5]
      #
      # Cast each element in the list to a string.
      #
      # Join the strings on a ',' and return '1,2,3,4,5'
      #####
      return ','.join( map( lambda i: str(i), idList ) )

   @staticmethod
   def getIdList(idString):
      ####
      # idString = '1,2,3,4,5'
      #
      # Split the string on a ',' to get a list.
      #
      # Cast each element in the list to an int.
      #
      # If an element generates a ValueError on the cast return an empty list.
      ####
      idList = []

      try:
         idList = map( lambda s: int(s), idString.split(',') )
      except ValueError:
         ##Cast to int failed, must not be a number##
         pass

      return idList

   @staticmethod
   def getCacheKey(itemId, itemData):
      return str(itemId) + '_' + str(itemData)

   @staticmethod
   def getTimeRanges():

      #############
      #  time.time() is used to generate the unix timestamp 
      #  associated with the json structure pushed to the database
      #  by a talos bot.  So all time ranges need to be computed in
      #  seconds since the epoch
      ############

      now = int( time.time() )

      timeRanges = { 'days_7': { 'start':now, 'stop':now - 604800  },      
                     'days_30': { 'start':now, 'stop':now - 2592000 },    
                     'days_60': { 'start':now, 'stop':now - 5184000 }, 
                     'days_90': { 'start':now, 'stop':now - 7776000 },  
                     'days_360': { 'start':now, 'stop':now - 31557600 } }

      return timeRanges

   def __init__(self, sqlFileName):

      Model.__init__(self, sqlFileName)

   def getProductTestOsMap(self):

      productTuple = self.dhub.execute(proc='graphs.selects.get_product_test_os_map',
                                       debug_show=self.DEBUG,
                                       return_type='tuple') 

      return productTuple

   def getOperatingSystems(self, keyColumn=None):

      operatingSystems = dict()
      if keyColumn:
         operatingSystems = self.dhub.execute(proc='graphs.selects.get_operating_systems',
                                     debug_show=self.DEBUG,
                                     key_column=keyColumn,
                                     return_type='dict') 
      else:
         osTuple = self.dhub.execute(proc='graphs.selects.get_operating_systems',
                                     debug_show=self.DEBUG,
                                     return_type='tuple') 

         operatingSystems = self._getUniqueKeyDict(osTuple, ['name', 'version'])

      return operatingSystems

   def getTests(self, keyColumn='name'):

      testDict = self.dhub.execute(proc='graphs.selects.get_tests',
                                  debug_show=self.DEBUG,
                                  key_column=keyColumn,
                                  return_type='dict') 

      return testDict

   def getProducts(self, keyColumn=None):

      products = dict()
      if keyColumn:
         products = self.dhub.execute(proc='graphs.selects.get_product_data',
                                           debug_show=self.DEBUG,
                                           key_column=keyColumn,
                                           return_type='dict') 
      else:
         productsTuple = self.dhub.execute(proc='graphs.selects.get_product_data',
                                           debug_show=self.DEBUG,
                                           return_type='tuple') 

         products = self._getUniqueKeyDict(productsTuple, ['product', 'branch', 'version'])

      return products 

   def getMachines(self):
      machinesDict = self.dhub.execute(proc='graphs.selects.get_machines',
                                    debug_show=self.DEBUG,
                                    key_column='name',
                                    return_type='dict') 

      return machinesDict
      
   def getOptions(self):
      optionsDict = self.dhub.execute(proc='graphs.selects.get_options',
                                    debug_show=self.DEBUG,
                                    key_column='name',
                                    return_type='dict') 

      return optionsDict

   def getPages(self):
      pagesDict = self.dhub.execute(proc='graphs.selects.get_pages',
                                    debug_show=self.DEBUG,
                                    key_column='url',
                                    return_type='dict') 

      return pagesDict

   def getAuxData(self):
      auxDataDict = self.dhub.execute(proc='graphs.selects.get_aux_data',
                                    debug_show=self.DEBUG,
                                    key_column='name',
                                    return_type='dict') 

      return auxDataDict

   def getReferenceData(self):

      referenceData = dict( operating_systems=self.getOperatingSystems(),
                            tests=self.getTests(),
                            products=self.getProducts(),
                            machines=self.getMachines(),
                            options=self.getOptions(),
                            pages=self.getPages(),
                            aux_data=self.getAuxData())

      return referenceData

   def getTestCollections(self):

      testCollectionTuple = self.dhub.execute(proc='graphs.selects.get_test_collections',
                                              debug_show=self.DEBUG,
                                              return_type='tuple') 

      testCollection = dict()
      for data in testCollectionTuple:

         if data['id'] not in testCollection:

            testCollection[ data['id'] ] = dict()
            testCollection[ data['id'] ]['name'] = data['name']
            testCollection[ data['id'] ]['description'] = data['description']
            testCollection[ data['id'] ]['data'] = []

         testCollection[ data['id'] ]['data'].append( { 'test_id':data['test_id'],
                                                        'name':data['name'],
                                                        'product_id':data['product_id'],
                                                        'operating_system_id':data['operating_system_id'] } )


      return testCollection

   def getTestReferenceData(self):

      referenceData = dict( operating_systems=self.getOperatingSystems('id'),
                            tests=self.getTests('id'),
                            products=self.getProducts('id'),
                            product_test_os_map=self.getProductTestOsMap(),
                            test_collections=self.getTestCollections())

      return referenceData

   def getTestRunSummary(self, start, end, productIds, operatingSystemIds, testIds):

      colData = { 'b.product_id':DatazillaModel.getIdString(productIds),
                  'b.operating_system_id':DatazillaModel.getIdString(operatingSystemIds),
                  'tr.test_id':DatazillaModel.getIdString(testIds) }

      rep = self.buildReplacement(colData)

      testRunSummaryTable = self.dhub.execute(proc='graphs.selects.get_test_run_summary',
                                              debug_show=self.DEBUG,
                                              replace=[ str(end), str(start), rep ],
                                              return_type='table') 

      return testRunSummaryTable

   def getAllTestRuns(self):

      testRunSummaryTable = self.dhub.execute(proc='graphs.selects.get_all_test_runs',
                                              debug_show=self.DEBUG,
                                              return_type='table') 

      return testRunSummaryTable

   def getTestRunValues(self, testRunId):

      testRunValueTable = self.dhub.execute(proc='graphs.selects.get_test_run_values',
                                            debug_show=self.DEBUG,
                                            placeholders=[ testRunId ],
                                            return_type='table') 

      return testRunValueTable

   def getTestRunValueSummary(self, testRunId):

      testRunValueTable = self.dhub.execute(proc='graphs.selects.get_test_run_value_summary',
                                            debug_show=self.DEBUG,
                                            placeholders=[ testRunId ],
                                            return_type='table') 

      return testRunValueTable

   def getPageValues(self, testRunId, pageId):

      pageValuesTable = self.dhub.execute(proc='graphs.selects.get_page_values',
                                          debug_show=self.DEBUG,
                                          placeholders=[ testRunId, pageId ],
                                          return_type='table') 

      return pageValuesTable
      
   def getSummaryCacheData(self, itemId, itemData):

      cachedData = self.dhub.execute(proc='graphs.selects.get_summary_cache',
                                     debug_show=self.DEBUG,
                                     replace=[ itemId, itemData ],
                                     return_type='tuple') 

      return cachedData

   def getAllSummaryCacheData(self):

      dataIter = self.dhub.execute(proc='graphs.selects.get_all_summary_cache_data',
                                   debug_show=self.DEBUG,
                                   chunk_size=5,
                                   chunk_source="summary_cache.id",
                                   return_type='tuple')


      return dataIter

   def setTestCollection(self, name, description):


      return id

   def setSummaryCache(self, itemId, itemData, value):

      nowDatetime = str( datetime.datetime.now() )

      self.dhub.execute(proc='graphs.inserts.set_summary_cache',
                        debug_show=self.DEBUG,
                        placeholders=[ itemId, 
                                       itemData, 
                                       value, 
                                       nowDatetime, 
                                       value, 
                                       nowDatetime ]) 

   def loadTestData(self, data, jsonData):

      ##Get the reference data##
      refData = self.getReferenceData()

      ##Get/Set reference info##
      refData['test_id'] = self._getTestId(data, refData)
      refData['option_id_map'] = self._getOptionIds(data, refData)
      refData['operating_system_id'] = self._getOsId(data, refData)
      refData['product_id'] = self._getProductId(data, refData)
      refData['machine_id'] = self._getMachineId(data, refData)

      refData['build_id'] = self._setBuildData(data, refData)
      refData['test_run_id'] = self._setTestRunData(data, refData)

      self._setOptionData(data, refData)
      self._setTestValues(data, refData)
      self._setTestAuxData(data, refData)
      self._setTestData(jsonData, refData)

   def _setTestData(self, jsonData, refData):
   
      self.setData('set_test_data', [refData['test_run_id'], jsonData])
      
   def _setTestAuxData(self, data, refData):

      if 'results_aux' in data:

         for auxData in data['results_aux']:
            auxDataId = self._getAuxId(auxData, refData)
            auxValues = data['results_aux'][auxData]

            for index in range(0, len(auxValues)):

               stringData = ""
               numericData = 0
               if self.isNumber(auxValues[index]):
                  numericData = auxValues[index]
               else:
                  stringData = auxValues[index]

               self.setData('set_aux_values', [refData['test_run_id'],
                                                index + 1,
                                                auxDataId,
                                                numericData,
                                                stringData])

   def _setTestValues(self, data, refData):

      for page in data['results']:

         pageId = self._getPageId(page, refData)
         
         values = data['results'][page]

         for index in range(0, len(values)):

            value = values[index]
            self.setData('set_test_values', [refData['test_run_id'],
                                              index + 1,
                                              pageId, 
                                              ##Need to get the value id into the json##
                                              1,
                                              value])

   def _getAuxId(self, auxData, refData):
      
      auxId = 0
      try:
         if auxData in refData['aux_data']:
            auxId = refData['aux_data'][auxData]['id']
         else:
            auxId = self.setData('set_aux_data', [refData['test_id'], auxData])
            
      except KeyError:
         raise
      else:
         return auxId
      
   def _getPageId(self, page, refData):
      
      pageId = 0
      try:
         if page in refData['pages']:
            pageId = refData['pages'][page]['id']
         else:
            pageId = self.setData('set_pages_data', [refData['test_id'], page])

      except KeyError:
         raise
      else:
         return pageId

   def _setOptionData(self, data, refData):

      for option in data['testrun']['options']:
         id = refData['option_id_map'][option]['id']
         value = data['testrun']['options'][option]
         self.setData('set_test_option_values', [refData['test_run_id'],
                                                  id,
                                                  value])
      
   def _setBuildData(self, data, refData):
      
      buildId = self.setData('set_build_data', [ refData['operating_system_id'],
                                                  refData['product_id'], 
                                                  refData['machine_id'],
                                                  data['test_build']['id'],
                                                  data['test_machine']['platform'],
                                                  data['test_build']['revision'],
                                                  ##Need to get the build_type into the json##
                                                  'debug',
                                                  ##Need to get the build_date into the json##
                                                  int(time()) ] )
      
      return buildId
      
   def _setTestRunData(self, data, refData):

      testRunId = self.setData('set_test_run_data', [ refData['test_id'],
                                                       refData['build_id'],
                                                       data['test_build']['revision'],
                                                       data['testrun']['date'] ])

      return testRunId

   def _getMachineId(self, data, refData):

      machineId = 0
      try:
         name = data['test_machine']['name']
         if name in refData['machines']:
            machineId = refData['machines'][ name ]['id']
         else:
            machineId = self.setData('set_machine_data', [ name, int(time()) ])

      except KeyError:
         raise

      else:
         return machineId

   def _getTestId(self, data, refData):
      testId = 1 
      try:
         if data['testrun']['suite'] in refData['tests']:
            testId = refData['tests'][ data['testrun']['suite'] ]['id']
         else:
            version = 1 
            if 'suite_version' in data['testrun']:
               version = int(data['testrun']['suite_version'])

            testId = self.setData('set_test', [ data['testrun']['suite'], version ])
      except KeyError:
         raise 
      else:
         return testId

   def _getOsId(self, data, refData):

      osId = 0
      try:
         osName = data['test_machine']['os']
         osVersion = data['test_machine']['osversion']
         osKey = osName + osVersion
         if osKey in refData['operating_systems']:
            osId = refData['operating_systems'][osKey]
         else:
            osId = self.setData('set_operating_system', [ osName, osVersion ])

      except KeyError:
         raise

      else:
         return osId

   def _getOptionIds(self, data, refData):
      optionIds = dict()
      try:
         for option in data['testrun']['options']:
            if option in refData['options']:
               optionIds[ option ] = refData['options'][option]
            else:
               testId = self.setData('set_option', [ option ])
               optionIds[ option ] = testId 
      except KeyError:
         raise
      else:
         return optionIds

   def _getProductId(self, data, refData):

      productId = 0

      try:
         product = data['test_build']['name']
         branch = data['test_build']['branch']
         version = data['test_build']['version']

         productKey = product + branch + version

         if productKey in refData['products']:
            productId = refData['products'][productKey]
         else:
            productId = self.setData('set_product_data', [ product, branch, version ])

      except KeyError:
         raise
      else:
         return productId

   def _getUniqueKeyDict(self, dataTuple, keyStrings):   

      dataDict = dict()
      for data in dataTuple:
         uniqueKey = ""
         for key in keyStrings:
            uniqueKey += str(data[key])
         dataDict[ uniqueKey ] = data['id']
      return dataDict

