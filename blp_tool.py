__author__ = 'yen'
import blpapi


class BLP(object):
    def __init__(self):
        self._session = blpapi.Session()
        self._session.start()
        self._session.openService('//blp/refdata')
        self._refDataService = self._session.getService('//blp/refdata')

    def __call__(self, *args, **kwargs):
        request = self.getRequest(**kwargs)
        return self.getResponseData(request)

    def getRequest(self, **kwargs):
        '''You need to customize your own request generator here.'''
        return None

    def getResponseData(self, request):
        self._session.sendRequest(request)
        while True:
            event = self._session.nextEvent()
            for msg in event:
                if msg.hasElement('data'):
                    msg = msg.getElement('data')
                if not msg.hasElement('securityData'):
                    continue
                for fieldData in self.getFieldData(msg):
                    yield fieldData
            if event.eventType() == blpapi.Event.RESPONSE:
                break

    def getFieldData(self, msg):
        '''You need to customize your own parser here.'''
        return []


class BDP(BLP):
    def getRequest(self, codes=['2330 TT Equity'], fields=['PX_LAST'], overrideFieldValueDict=None, *args, **kwargs):
        if not overrideFieldValueDict:
            overrideFieldValueDict = dict()
        assert isinstance(codes, list), 'only "list" is allowed to "codes". '
        assert isinstance(fields, list), 'only "list" is allowed to "fields".'
        assert isinstance(overrideFieldValueDict, dict), 'only "dict" is allowed to "overrideFieldValueDict". '

        request = self._refDataService.createRequest('ReferenceDataRequest')
        [request.getElement('securities').appendValue(code) for code in codes]
        [request.getElement('fields').appendValue(field) for field in fields]

        for key, value in overrideFieldValueDict.items():
            override = request.getElement('overrides').appendElement()
            override.setElement('fieldId', key)
            override.setElement('value', value)
        return request

    def getFieldData(self, msg):
        securityDataNode = msg.getElement('securityData')
        securityNodes = [securityDataNode.getValue(i) for i in range(securityDataNode.numValues())]

        for securityNode in securityNodes:
            code = securityNode.getElementValue('security')
            fieldNode = securityNode.getElement('fieldData')
            fieldData = self.fieldNodeParser(fieldNode)
            fieldData.update({'code': code})
            yield fieldData

    def fieldNodeParser(self, fieldNode):
        fieldData = {str(fieldNode.getElement(i).name()): fieldNode.getElementValue(i) for i in range(fieldNode.numElements())}
        return fieldData


class BDH(BLP):
    def getRequest(self, codes=['2330 TT Equity'], fields=['PX_LAST'], startdate='2005-01-01', enddate='2005-01-05', periodicity='DAILY', *args, **kwargs):
        assert isinstance(codes, list), 'only "list" is allowed to "codes". '
        assert isinstance(fields, list), 'only "list" is allowed to "fields".'
        assert isinstance(startdate, str), 'only "str" is allowed to "startdate". '
        assert isinstance(enddate, str), 'only "str" is allowed to "enddate". '
        assert isinstance(periodicity, str), 'only "str" is allowed to "periodicity". '

        request = self._refDataService.createRequest('HistoricalDataRequest')
        [request.getElement('securities').appendValue(code) for code in codes]
        [request.getElement('fields').appendValue(field) for field in fields]
        request.set('startDate', startdate.replace('-', ''))
        request.set('endDate', enddate.replace('-', ''))
        request.set('periodicitySelection', periodicity)
        return request

    def getFieldData(self, msg):
        securityDataNode = msg.getElement('securityData')
        code = securityDataNode.getElementValue('security')

        fieldNodes = securityDataNode.getElement('fieldData')
        for i in range(fieldNodes.numValues()):
            fieldNode = fieldNodes.getValue(i)
            fieldData = self.fieldNodeParser(fieldNode)
            fieldData.update({'code': code})
            yield fieldData

    def fieldNodeParser(self, fieldNode):
        fieldData = {str(fieldNode.getElement(i).name()): fieldNode.getElementValue(i) for i in range(fieldNode.numElements())}
        return fieldData


class BEQS(BLP):
    def getRequest(self, screen_name, screenType='PRIVATE', overrideFieldValueDict=None):
        if not overrideFieldValueDict:
            overrideFieldValueDict = dict()
        assert isinstance(screen_name, str), 'only "str" is allowed to "screen_name". '
        assert screenType in ['GLOBAL', 'PRIVATE'], 'only  ["GLOBAL", "PRIVATE"] is allowed to "screenType". '

        request = self._refDataService.createRequest('BeqsRequest')
        request.set('screenName', screen_name)
        request.set('screenType', screenType)
        for key, value in overrideFieldValueDict.items():
            override = request.getElement('overrides').appendElement()
            override.setElement('fieldId', key)
            override.setElement('value', value)
        return request

    def getFieldData(self, msg):
        securityDataNodes = msg.getElement('securityData')
        for idx_securityData in range(securityDataNodes.numValues()):
            securityDataNode = securityDataNodes.getValue(idx_securityData)
            fieldNode = securityDataNode.getElement('fieldData')
            fieldData = self.fieldNodeParser(fieldNode)
            yield fieldData

    def fieldNodeParser(self, fieldNode):
        fieldData = {str(fieldNode.getElement(i).name()): fieldNode.getElementValue(i) for i in range(fieldNode.numElements())}
        return fieldData


bdp = BDP()
bdh = BDH()
beqs = BEQS()


if __name__ == '__main__':
    ## example 1
    parameter1 = {
        'codes': ['2330 TT Equity', '2412 TT Equity'],
        'fields': ['FUNDAMENTAL_DATABASE_DATE', 'PX_LAST', 'PE_RATIO'],
        'overrideFieldValueDict': {
            'EQY_FUND_YEAR': 2013,
            'FUND_PER': 'Q1'
        }
    }
    dataGenerator = bdp(**parameter1)
    for data in dataGenerator:
        print data
    print('--------------------------------')
    
    ## example 2
    parameter2 = {
        'codes': ['2330 TT Equity', '2412 TT Equity'],
        'fields':  ['PX_LAST', 'PX_OPEN', 'PE_RATIO', 'VOLUME'],
        'overrideFieldValueDict': {}
    }
    dataGenerator = bdp(**parameter2)
    for data in dataGenerator:
        print data
    print('--------------------------------')


    ## example 3
    parameter3 = {
        'codes': ['2330 TT Equity', '2412 TT Equity'],
        'fields': ['PX_LAST'],
        'startdate': '2014-01-01',
        'enddate': '2014-01-09',
        'periodicity': 'DAILY'
    }
    dataGenerator = bdh(**parameter3)
    for data in dataGenerator:
        print data
    print('--------------------------------')


    ## example 4
    parameter4 = {
        'screen_name': 'china_a_shares_test',
        'overrideFieldValueDict': {'AsOf': '20101231'}
    }

    dataGenerator = beqs(**parameter4)
    for data in dataGenerator:
        print data
    print('--------------------------------')