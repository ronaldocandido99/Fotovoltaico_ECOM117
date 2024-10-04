import pandas as pd
import numpy as np



def constant_two(VMPP,IMPP,VOC,ISC):
    return ((VMPP/VOC - 1)/np.log(1 - IMPP/ISC))

def constant_one(VMPP,IMPP,VOC,ISC):
    return (1- IMPP/ISC) * np.exp((-1*VMPP)/constant_two(VMPP,IMPP,VOC,ISC)*VOC)

#Calcula a corrente do módulo fotovoltaico(FV)
def IP(VP,VMPP,IMPP,VOC,ISC):
    return ISC*(1-constant_one(VMPP,IMPP,VOC,ISC)*np.exp(VP/constant_two(VMPP,IMPP,VOC,ISC)*VOC)-1)

#Calcula corrente de curto-circuito
def ISC(G,T,ISCS,alpha,GS = 1000, TS = 298):
    return ISCS*(G/GS)*(1+alpha*(T-TS))

#Calcula tensão de circuito aberto
def VOC(T,beta,VOCS,TS = 298):
    return VOCS + beta*(T-TS)

#Calcula Corrente no ponto de máxima potência(MPP)
def IMPP(G,T,IMPPS,alpha,GS = 1000, TS = 298):
    return IMPPS*(G/GS)*(1+alpha*(T-TS))

#Calcula Tensão no ponto de máxima potência(MPP)
def VMPP(T,beta,VMPPS,TS = 298):
    return VMPPS + beta*(T-TS)

#Calcula tensão de circuito aberto transladada para uma dada irradiância G
def VOCm(G,VMPP,IMPP,VOC,ISC,VOCS,GS=1000):
    return constant_two(VMPP,IMPP,VOC,ISC)*VOCS*np.log(1+((1-(G/GS))/constant_one(VMPP,IMPP,VOC,ISC)))

#Calcula o coeficiente de correção em função da irradiância
def delta_V(G,VMPP,IMPP,VOC,ISC,VOCS):
    return VOCS - VOCm(G,VMPP,IMPP,VOC,ISC,VOCS)

#Fórmulas de tensão mais precisas (considerando o fator de correção)
def adjusted_VOC(T,beta,VOCS,G,VMPP,IMPP,VOC,ISC):
    return VOC(T,beta,VOCS) - delta_V(G,VMPP,IMPP,VOC,ISC,VOCS)

def adjusted_VMPP(T,beta,VMPPS,G,VMPP,IMPP,VOC,ISC,VOCS):
    return VMPP(T,beta,VMPPS) - delta_V(G,VMPP,IMPP,VOC,ISC,VOCS)

#Cálculo da tensão no módulo FV (formula de IP invertida)
def VP(IP,VMPP,IMPP,VOC,VOCS,ISC):
    return constant_two(VMPP,IMPP,VOC,ISC)*VOCS*np.log(1+((1-(IP/ISC))/constant_one(VMPP,IMPP,VOC,ISC)))

#Cálculo da resistência em série em função dos parâmetros do painel 
def RS(VMPP,IMPP,VOC,ISC):
    return (constant_two(VMPP,IMPP,VOC,ISC)*(VOC/ISC))*(1/(1+constant_one(VMPP,IMPP,VOC,ISC)))