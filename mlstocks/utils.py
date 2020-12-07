import numpy as np



class SearchableDict(dict):
    def find(self,key):
        """
        Search if a `key` is present in the dictionary tree 
        print "address" to screen
        and return list of "addresses"
        """
        key=key.lower()
        addresses = []
        results  = []

        def findkey(data, root=''):
            """ find a key recursively in a dictionary (potentially dictionary of dictionaries) """
            if len(root)>0:
                root+=':'
            for key0,v0 in data.items():
                if key0 is None:
                    continue
                if key0.lower().find(key)>=0:
                    addresses.append(root+key0)
                    results.append(v0)
                    print('>>> ',root+key0+':', v0 )
                if isinstance(v0,dict):
                    # recursive call
                    findkey(v0, root=root+key0)
                elif isinstance(v0,list):
                    if len(v0)>0:
                        if isinstance(v0[0],dict):
                            for i in np.arange(len(v0)):
                                # recursive call
                                findkey(v0[i], root=root+key0+'['+str(i)+']')
        findkey(self)
        return addresses, results

    def __repr__(self):
        s='Searchable dictionary:\n'
        for k,v in self.items():
            s+=' - {:35s}: {}\n'.format(k, v)
        return s



# --------------------------------------------------------------------------------}
# --- Misc  
# --------------------------------------------------------------------------------{
def standardizeCountry(countrylist):
    countrylist= countrylist.fillna('')
    countrylist=countrylist.str.replace('United States','USA')
    countrylist=countrylist.str.replace('United Kingdom','UK')
    countrylist=countrylist.str.replace('United Arab Emirates','UAE')
    countrylist=countrylist.str.replace('Cayman Islands','Cayman')
    countrylist=countrylist.str.replace('Luxembourg','Lux.')
    countrylist=countrylist.str.replace('Switzerland','Swis.')
    countrylist=countrylist.str.replace('Argentina','Arg.')
    countrylist=countrylist.str.replace('Hong Kong','HK')
    countrylist=countrylist.str.replace('Germany','Germ.')
    countrylist=countrylist.str.replace('Bermuda','Berm.')
    countrylist=countrylist.str.replace('South Korea','Korea')
    countrylist=countrylist.str.replace('Singapour','Sing.')
    return countrylist

def standardizeSector(sectorList):
    sectorList= sectorList.fillna('')
    sectorList =sectorList.str.replace('Financial','Fin.')
    sectorList =sectorList.str.replace('Communication','Com.')
    sectorList =sectorList.str.replace('Consumer ','C.')
    sectorList =sectorList.str.replace('Technology','Tech.')
    sectorList =sectorList.str.replace('Basic ','')
    return sectorList

def standardizeQuoteType(quoteType):
    quoteType = quoteType.fillna('')
    quoteType = quoteType.str.replace('EQUITY','stock')
    quoteType = quoteType.str.replace('MUTUAL FUND','MF')
    quoteType = quoteType.str.replace('MUTUALFUND','MF')
    return quoteType


def replaceEmptyStringsAndNA(values, replvalue):
    values = values.fillna(replvalue)
    values =  np.array([v if v!='' else replvalue0 for v in values])
    return values

