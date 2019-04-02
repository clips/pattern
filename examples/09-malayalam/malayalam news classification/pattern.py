#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 02:17:22 2019

@author: abhijithneilabraham
"""


from pattern.web import Bing, SEARCH, plaintext,Google
from ulmfit import ULMFiT
engine = Google(license='AIzaSyCND8YQhyxQZU1E4y4gCzg8V61NQ61BYtw')
searched=[]

for result in engine.search('സഞ്ജു സാംസൺ', type=SEARCH, start=1):
    print(repr(plaintext(result.text)))
    searched.append(repr(plaintext(result.text)))
print(len(searched))    

model = ULMFiT("news/")
for i in searched:
    x=model.predict(i)
    
    print(x['intent'])
    