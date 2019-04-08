"""
Created on 18. 3. 2019
CEEF classifier plugin for ClassMark.

:author:     Martin Dočekal
:contact:    xdocek09@stud.fit.vubtr.cz
"""
from classmark.core.plugins import Classifier, PluginAttribute
from classmark.core.preprocessing import BaseNormalizer, NormalizerPlugin,\
    MinMaxScalerPlugin,StandardScalerPlugin, RobustScalerPlugin

from .evo_data_set import EvoDataSet
from .individual import Individual
from typing import List
from .selection import Selector, Rulete, Rank
import random
import copy
import numpy as np



class CEEF(Classifier):
    """
    Classification by evolutionary estimated functions (or CEEF) is classification method that uses
    something like probability density functions, one for each class, to classify input data.
    """
    SELECTION_METHODS={"RANK":Rank(), "RULETE":Rulete()}
    
    def __init__(self, normalizer:BaseNormalizer=None, generations:int=100, stopAccuracy:float=None, \
                 population:int=10, nbestToNext=1, selectionMethod:Selector="RANK", randomSeed:int=None, maxMutations=5, \
                 maxStartSlots=1,
                 crossoverProb:float=0.75, testSetSize:float=0.1, changeTestSet:bool=False):
        """
        Classifier initialization.
        
        :param normalizer: Normalizer used for input data. If none than normalization/scalling is omitted.
        :type normalizer: None | BaseNormalizer
        :param generations: Maximum number of generations.
        :type generations: int
        :param stopAccuracy: Stop evolution when accuracy reaches concrete value.
        :type stopAccuracy: None | float
        :param population: Population size.
        :type population: int
        :param nbestToNext: N best chromosomes proceeds to next generation.
        :type nbestToNext: int
        :param selectionMethod: Selection method for evolution.
        :type selectionMethod: Selector
        :param randomSeed: If not None than fixed seed is used.
        :type randomSeed: int
        :param maxMutations: Maximum number of changed genes in one mutation.
        :type maxMutations: int
        :param maxStartSlots: Maximum number of slots for start. (minimal is always 1)
        :type maxStartSlots: int
        :param crossoverProb: Probability of crossover between two selected individuals.
            If random says no crossover than one of parent is randomly chosen and its chromosome is used.
        :type crossoverProb: float
        :param testSetSize: Size of test set, that is used for fitness score calculation.
        :type testSetSize: float
        :param changeTestSet: Change test set for every generation.
        :type changeTestSet: bool
        """


        #TODO: type control must be off here (None -> BaseNormalizer) maybe it will be good if one could pass
        #object
        self._normalizer=PluginAttribute("Normalize", PluginAttribute.PluginAttributeType.SELECTABLE_PLUGIN, None,
                                         [None, NormalizerPlugin, MinMaxScalerPlugin, StandardScalerPlugin, RobustScalerPlugin])
        self._normalizer.value=normalizer
        
        self._generations=PluginAttribute("Number of generations", PluginAttribute.PluginAttributeType.VALUE, int)
        self._generations.value=generations
        
        self._stopAccuracy=PluginAttribute("Stop accuracy", PluginAttribute.PluginAttributeType.VALUE, float)
        self._stopAccuracy.value=stopAccuracy
        
        self._population=PluginAttribute("Population size", PluginAttribute.PluginAttributeType.VALUE, int)
        self._population.value=population
        
        
        self._nbestToNext=PluginAttribute("N best to next generation", PluginAttribute.PluginAttributeType.VALUE, int)
        self._nbestToNext.value=nbestToNext
        
        
        self._selectionMethod=PluginAttribute("Selection method", PluginAttribute.PluginAttributeType.SELECTABLE, None,
                                              list(self.SELECTION_METHODS.keys()))
        self._selectionMethod.value=selectionMethod

        
        self._randomSeed=PluginAttribute("Random seed", PluginAttribute.PluginAttributeType.VALUE, int)
        self._randomSeed.value=randomSeed
        
        self._maxMutations=PluginAttribute("Max changed genes in mutation", PluginAttribute.PluginAttributeType.VALUE, int)
        self._maxMutations.value=maxMutations
        
        self._maxStartSlots=PluginAttribute("Max start slots", PluginAttribute.PluginAttributeType.VALUE, int)
        self._maxStartSlots.value=maxStartSlots
        
        self._crossoverProb=PluginAttribute("Crossover probability", PluginAttribute.PluginAttributeType.VALUE, float)
        self._crossoverProb.value=crossoverProb
        
        self._testSetSize=PluginAttribute("Test set size", PluginAttribute.PluginAttributeType.VALUE, float)
        self._testSetSize.value=testSetSize
        
        self._changeTestSet=PluginAttribute("Change test set for each generation", PluginAttribute.PluginAttributeType.CHECKABLE, bool)
        self._changeTestSet.value=changeTestSet
        
        
        self._evolvedCls=None    #there the evolved classifier will be stored
        
    @staticmethod
    def getName():
        return "Classification by evolutionary estimated functions"
    
    @staticmethod
    def getNameAbbreviation():
        return "CEEF"
 
    @staticmethod
    def getInfo():
        return ""
    
    def train(self, data, labels):
        random.seed(self._randomSeed.value)
        if self._normalizer.value is not None:
            data=self._normalizer.value.fitTransform(data)
        
        self._evolvedCls=None
        
        #let's create train and test set
        dataset=EvoDataSet(data, labels,self._testSetSize.value,self._randomSeed.value,self._generations.value)
        self.trainedClasses=dataset.classes
        
        #create initial population
        population=[Individual.createInit(dataset, self._maxMutations.value, self._maxStartSlots.value) for _ in range(self._population.value)]
        
        #evaluate
        #set the best as the result
        self._evolvedCls=max(population, key=lambda i: i.score)
        
        generations=1
        while (self._stopAccuracy.value is None or self._stopAccuracy.value>self._evolvedCls.score) and \
               self._generations.value>=generations:
            print(self._evolvedCls.score)
            
            
            #get new population (in elitistic fashion)
            #    performs steps:
            #        selection
            #        crossover
            #        mutation
            #        replacement
            population=self._generateNewPopulation(population)
            
            #evaluate
            if self._changeTestSet.value:
                #ok new test set requested
                self._evolvedCls.invalidateScore()   #because of the new test set
                dataset.changeTestSet()
                
            actBest=max(population, key=lambda i: i.score)
            
            if actBest.score>=self._evolvedCls.score:
                #new best one
                self._evolvedCls=actBest
            
            generations+=1
                
    def _generateNewPopulation(self, population:List[Individual]):
        """
        Generates new population from actual population.
        Whole new population is created and the actual best one is added (elitism).
        
        :param population: Actual population.
        :type population: List[Individual]
        :return: New population
        :rtype: List[Individual]
        """

        selMethod=self.SELECTION_METHODS[self._selectionMethod.value]

        newPopulation=sorted(population, key=lambda i: i.score)[:self._nbestToNext.value]
        while(len(newPopulation)<self._population.value):
            #selection
            theChosenOnes=selMethod(population,2)   #we are selecting two parents
            
            #crossover
            if random.uniform(0,1)<=self._crossoverProb.value:
                #the crossover is requested
                newIndividual=Individual.crossover(theChosenOnes)
            else:
                #ok no crossover just choose one
                newIndividual=copy.copy(random.choice(theChosenOnes))
                
            #lets do the mutation
            newIndividual.mutate(self._maxMutations.value)
            
            newPopulation.append(newIndividual)

        return newPopulation
        
    def predict(self, data):
        if self._normalizer.value is not None:
            data=self._normalizer.value.transform(data)
            
        try:
            return self._evolvedCls.predict(data.A)
        except MemoryError:
            #ok lets try the parts
            predicted=np.empty(data.shape[0], dtype=self.trainedClasses.dtype)
            memEr=True
            partSize=data.shape[0]
            while memEr:
                memEr=False
                try:
                    partSize=int(partSize/2)
                    for offset in range(0, data.shape[0], partSize):
                        predicted[offset:offset+partSize]=self._evolvedCls.predict(data[offset:offset+partSize,:].A)
                except MemoryError:
                    memEr=True
    
            return predicted
    