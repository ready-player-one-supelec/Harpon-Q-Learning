# -*- coding: utf-8 -*-
"""
Created on Tue Dec  4 13:18:27 2018

@author: Loic
"""
import random as rd 
import numpy as np
import matplotlib.pyplot as plt 
import time


#%% Programme :

# R doit être un dictionnaire indéxé par les états S.
# IMPORTANT On peut remplir seulement les valeurs non nulles
# Q doit être un dictionnaire indéxé par les états S et les actions A. (On peut indexer par des fonctions et c'est cool !)
# IMPOTANT On peut initialiser Q vide et on prendra dans ce cas comme valeur par défaut 0
# ATTENTION Si on run sans recacluler Q cela ne marchera plus car on aura redefini les fonctions de A donc on ne pourra plus acceder à Q
# Il faut donc soit le recalcalculer soit ne pas refefinir les fonctions de A
# On n'a pas en fait besoin de connaitre S ce qui est bien car on ne le connait en général pas 

def frontprop(A,s0,R,Q,choose,opt = 1): 
    s = s0
    lS = [s0]
    lA = []
    try:
        rs = R[s0]
    except KeyError:
        rs = 0 #R n'est pas forcément rempli 
    while rs == 0: 
        mouvs = A
        #mouvs = []
        #for a in A: #Cette étape peut rallonger fortement le programme il faudra réflechir à l'enlever 
        #    if a(R,Q,A,s) != -1:
        #        mouvs.append(a)
        aa = choose(s,R,Q,mouvs,opt)
        lA.append(aa)
        s = aa(R,Q,A,s)
        lS.append(s)
        try:
            rs = R[s]
        except KeyError:
            rs = 0
    return [lS,lA]

def backprop(A,lS,lA,R,Q,la = 0.4,g = 0.3):
    n = len(lS)
    for i in range(n-2,-1,-1):
        s = lS[i]
        ss = lS[i+1]
        a = lA[i]
        try:
            rss = R[ss]
        except KeyError:
            rss = 0
        try:
            qsa = Q[s,a]
        except KeyError:
            qsa = 0
        maxss = 0
        for aa in A:
            try:
                qssaa = Q[ss,aa]
            except KeyError:
                qssaa = 0
            if qssaa > maxss: maxss = qssaa
        Q[s,a] = la*(rss + g*maxss)+(1-la)*qsa
    return Q

def chooseMax(s,R,Q,A,opt):
    res = A[0]
    resval = 0
    for a in A:
        try:
            qsa = Q[s,a]
        except KeyError:
            qsa = 0
        if qsa > resval:
            res =a 
            resval = qsa             
    return res

def chooseBoltz(s,R,Q,A,T):
    summ = 0
    for a in A:
        try:
            qsa = Q[s,a]
        except KeyError:
            qsa = 0
        summ += np.exp(qsa/T)
    rand = rd.random()*summ
    b = 0
    for a in A:
        try:
            qsa = Q[s,a]
        except KeyError:
            qsa = 0
        b += np.exp(qsa/T)
        if rand < b :
            return a
        
def chooseEpsilon(s,R,Q,A,opt): # Pas à jour et pas forcément utile 
    return s 
    
#%% Deep Q Learning 

import Perceptron_Q_Learning as per 

def batch_training(L_inputs,L_th_outputs,reseau,weights,bias,rate,iterations,activation = per.tanh,derivee = per.dtanh): 
    for k in range(iterations):
        delta_weight = [weights[k]*0 for k in range(len(weights))]
        delta_bias = [bias[k]*0 for k in range(len(bias))]
        for data in range(len(L_inputs)):
            gw,gb,cost = per.backprop(L_inputs[data],L_th_outputs[data],reseau,weights,bias,activation,derivee)
            for col in range(len(gw)):
                delta_weight[col] += gw[col]*rate/len(L_inputs)
                delta_bias[col] += gb[col]*rate/len(L_inputs)
        for col in range(len(weights)):
            weights[col] += -delta_weight[col]
            bias[col] += -delta_bias[col]  
    return weights,bias

def phibase(l): #Dans le cas vraiment basique pas besoin de faire de traitement on retient donc les arcs (s,a,r,ss)
    return l[-1] # apres on pert le corrélation entre les arcs donc c'est plutot mauvais 

def sample(D):
    res = []
    for i in range(32):
        elt = D[rd.randint(0,len(D)-1)]
        if elt != []:
            res.append(elt)
    return res
            
        

def ajoute(D,elt):
    D[rd.randint(0,len(D)-1)] = elt
    return D

# A est l'ensemble des actions possible (fonctions)
# s0 est l'état de départ 
# choose est la fonction de choix qui prends en entrée s R qw QB A et opt opt étant ce que l'on veut
# R est les resutlats. C'est une fonction : état s --> r(s) Attention il faut faire des try Error a chaque utilisation 
# memoire est la taille de la liste D  de mémoire des arcs on peut la prendre de l'ordre de 1 milion pour un jeu complexe. 
# it est le nombre d'apprentissages (arcs --> echec ou reussite) que l'on réalise
# neural_it est le nombre d'itérations que fait le réseau de neurones a chaque apprentissage
# reseau est le preceprton voulu sans l'entrée  ni la sortie !!!!!!
# Tlimest le temps maximum d'un arc ( pour eviter qu'il tourne en boucle ) attention si le jeu tourne encore apres Tlim alors il va se passer un truc louche 
# phi est la fonction de pré-traitement (s,R,(QW,QB),A,opt)

def deepQlearning(A,s0,R,choose,memoire,it,neural_it,reseau,Tlim = 10e9,phi = phibase,gamma = 0.5,rate = 0.001,opt = 0,modify = lambda x: x):
    reseau.append(len(A))
    inputs = s0 #A voir  --> Implementation ATARI pour s0
    (QW,QB) = per.random_w_b(inputs,reseau)
    D = [[] for i in range(memoire)]
    for i in range(it):
        print(i)
        lAS = [s0]
        s = s0
        p = phi(lAS)
        r = 0
        j = 0 #Evite une boucle inifnie mais doit etre élevé pour ne pas bloquer le jeu 
        while j<Tlim and abs(r) < 1 : # Etat final 
            ta = time.clock()
            j += 1
            opt = modify(opt) #opt peut etre tout les arguments suplémentaires odnt on a besoin pour le choix 
            a = choose(p,R,(QW,QB),reseau,A,opt) #Modify permet de faire evoluer opt par exemple si opt = epsilon on peut le faire décroitre... 
            ss = a(R,(QW,QB),A,s) #ici on fait l'action --> implementation ATARI
            lAS = lAS + [a,ss]
            pp = phi(lAS)
            try:
                r = R(ss)
            except KeyError:
                r = 0
            D  = ajoute(D,(p,a,r,pp)) #!!
            batch = sample(D)
            inputs = [batch[i][-1] for i in range(len(batch))]
            tb = time.clock()
            y = [0 for k in range(len(batch))] # Calcul de Theorical output 
            for k in range(len(batch)): # On doit d'abbord calculer les sorties que l'on connait 
                (sk,ak,rk,ssk) = batch[k]
                if abs(rk) >= 1: #Etat final 
                    y[k] = rk
                else:
                    maxk = max(per.front_prop(ssk,reseau,QW,QB,per.tanh)[-1])
                    y[k] = rk + gamma*maxk
            front = [[] for ii in range(len(inputs))] #On crée front pour avoir les valeurs de Q(s,a') pour les a' que l'on ne connait pas 
            for ii in range(len(inputs)):
                front[ii] = per.front_prop(inputs[ii],reseau,QW,QB,per.tanh)[-1]
            for k in range(len(y)) : #On change la forme de y c'est pas l'ideal mais ca a été fait comme ca 
                front[k][A.index(a)] = y[k]
                y[k] = front[k]
            tc = time.clock()
            (QW,QB) = batch_training(inputs,y,reseau,QW,QB,rate,neural_it)
            td = time.clock()
            #print("temps 1:" + str(round(abs(100*(ta-tb)))))
            #print("temps 2:" + str(round(abs(100*(tc-tb)))))
            #print("temps 3:" + str(round(abs(100*(tc-td)))))
            #print("")
            s = ss
            p = pp
    print(reseau)
    return QW,QB
            


        
        
        
#%% Jeu des batons 

def deepBatons(it = 50):
    A = [un_deep,deux_deep]
    s0 = [1 for i in range(11)]
    memoire = 1000
    neural_it = 10
    reseau = [8,4]
    QW,QB = deepQlearning(A,s0,R,chooseDeepBaton,memoire,it,neural_it,reseau,Tlim = 10e9,phi = phibase,gamma = 0.6,rate = 0.0005,opt = 0.8,modify = lambda x: (100*x+0.1)/101)
    res = 0
    for i in range(1000):
        ss = frontprop_deep(A,s0,R,(QW,QB),reseau,chooseDeepBaton,0)[0][-1]
        if ss[0] == 2:
            res += 1
    res = res /1000
    print(res)
    return QW,QB,res

        

def R(p):
    if p[0] == -1: return -1
    elif p[0] == 2: return 1
    else : return 0



def chooseDeepBaton(p,R,Q,reseau,A,opt):
    (QW,QB) = Q
    r = rd.random()
    if r < opt :
        rr = rd.randint(0,len(A)-1)
        return A[rr]
    else:
        fp = per.front_prop(p,reseau,QW,QB,per.tanh)[-1]
        res = fp.argmax()
        return A[res]
        
   
def deux_deep(R,Q,A,p):
    s= sum(p)
    if s-2 < 1:
        return [-1 for i in range(11)]
    else:
        e = ennemi(R,Q,A,s)
        res = s-2-e
        if res < 1:
            return [2 for i in range(11)]
        else:
            pp = [0 for i in range(11)]
            for j in range(res):
                pp[j] = 1
            return pp
        
def un_deep(R,Q,A,p):
    s= sum(p)
    if s-1 < 1:
        return [-1 for i in range(11)]
    else:
        e = ennemi(R,Q,A,s)
        res = s-1
        -e
        if res < 1:
            return [2 for i in range(11)]
        else:
            pp = [0 for i in range(11)]
            for j in range(res):
                pp[j] = 1
            return pp
    
def ennemi(R,Q,A,s): #Stategie gagnante 
    if s%3 == 1: return rd.randint(1,2)
    if s%3 == 0: return 2
    if s%3 == 2: return 1
    
#%%
    
def frontprop_deep(A,s0,R,Q,reseau,choose,opt = 1): 
    s = s0
    lS = [s0]
    lA = []
    rs = 0 
    while rs == 0: 
        mouvs = A
        #mouvs = []
        #for a in A: #Cette étape peut rallonger fortement le programme il faudra réflechir à l'enlever 
        #    if a(R,Q,A,s) != -1:
        #        mouvs.append(a)
        aa = choose(s,R,Q,reseau,mouvs,opt)
        lA.append(aa)
        s = aa(R,Q,A,s)
        lS.append(s)
        try:
            rs = R(s)
        except KeyError:
            rs = 0
    return [lS,lA]

def courbeBaton(nb = 10):
    res = []
    for i in range(1,nb):
        A,B,taux = deepBatons(i*50)
        res.append(taux)
    plt.plot(res)
    return res
        

#A,B,taux = deepBatons(10)
#res = courbeBaton(20)
#%%
#reseau = [8,4,2]
#print(1)
#print(per.front_prop([1,0,0,0,0,0,0,0,0,0,0],reseau,A,B,per.tanh)[-1])
#print(2)
#print(per.front_prop([1,1,0,0,0,0,0,0,0,0,0],reseau,A,B,per.tanh)[-1])
#print(3)
#print(per.front_prop([1,1,1,0,0,0,0,0,0,0,0],reseau,A,B,per.tanh)[-1])
#print(5)
#print(per.front_prop([1,1,1,1,1,0,0,0,0,0,0],reseau,A,B,per.tanh)[-1])

#%% 
def deux(R,Q,A,s):
    if s-2 < 1:
        return "d"
    else:
        e = ennemi(R,Q,A,s)
        res = s-2-e
        if res < 1:
            return "v"
        else:
            return res
        
def un(R,Q,A,s): 
    if s-1 < 1:
        return "d"
    else:
        e = ennemi(R,Q,A,s)
        res = s-1-e
        if res < 1:
            return "v"
        else:
            return res    
    
def jeuBatons(training): #marche
    S = ["d",1,2,3,4,5,6,7,8,9,10,11,"v"]
    A = [un,deux]
    R = {"d" :-1,"v":1}
    Q = {}
    s0=11
    for j in range(training):
        [lS,lA] = frontprop(A,s0,R,Q,chooseBoltz)
        Q = backprop(A,lS,lA,R,Q)
    return (Q,S)

def afficherBatons(Q):
    for k in range(11,0,-1):
        try:
            print(k, ": ", Q[k,un],Q[k,deux])
        except KeyError:
            print(k, ": ", "etat non atteignable")
    return None


def tauxVictoire(training):
    A = [un,deux]
    R = {"d" :-1,"v":1}
    Q=jeuBatons(training)[0]
    taux=0
    s0=11
    for i in range(1000):
        [lS,lA] = frontprop(A,s0,R,Q,chooseMax)
        if 1 not in lS:
            taux+=1/10
    return taux, "% de reussite"
    

#%% Essai simple 
l = 3

def haut(R,Q,A,s):
    if s < l :
        return -1
    else:
        return s-l
    
def bas(R,Q,A,s):
    if s > (l-1)*l-1 :
        return -1
    else:
        return s+l
    
def gauche(R,Q,A,s):
    if s%l == 0 :
        return -1
    else:
        return s-1

def droite(R,Q,A,s):
    if s%l == l-1 :
        return -1
    else:
        return s+1

def test(i):
    S = [i for i in range(l*l)]
    A = np.array([gauche,droite,haut,bas])
    R = {}    #[0,-10,10,0,-10,0,0,0,0]
    R[2] = 10
    R[1] = -10
    R[4] = -10
    Q = {}
    s0 = 0
    for j in range(i):
        [lS,lA] = frontprop(A,s0,R,Q,chooseBoltz,99)
        Q = backprop(A,lS,lA,R,Q,0.5,0.5)
    return (Q,S)


def affiche(Q):
    print("")
    print(" (0)  "+str(round(Q[0,droite]))+"→←"+"0"+"  (1)  "+"0"+"→←"+"0"+"  (2)")
    print("")
    print(str(round(Q[3,haut]))+"↑↓"+str(round(Q[0,bas]))+"        "+"0"+"↑↓"+"0"+"        "+str(round(Q[5,haut]))+"↑↓"+"0")
    print("")
    print(" (3)  "+str(round(Q[3,droite]))+"→←"+"0"+"  (4)  "+"0"+"→←"+str(round(Q[5,gauche]))+"  (5)")
    print("")
    print(str(round(Q[6,haut]))+"↑↓"+str(round(Q[3,bas]))+"        "+str(round(Q[7,haut]))+"↑↓"+"0"+"        "+str(round(Q[8,haut]))+"↑↓"+str(round(Q[5,bas])))
    print("")
    print(" (6)  "+str(round(Q[6,droite]))+"→←"+str(round(Q[7,gauche]))+"  (7)  "+str(round(Q[7,droite]))+"→←"+str(round(Q[8,gauche]))+"  (8)")
    print("")

#(Q,S) = test(10000)
#affiche(Q)
    


#%%
def deux_dur(R,Q,A,s): 
    if s-2 < 1:
        return "d"
    else:
        e = ennemi_dur(R,Q,A,s-2)
        res = s-2-e
        if res < 1:
            return "v"
        else:
            return res
        
def un_dur(R,Q,A,s): 
    if s-1 < 1:
        return "d"
    else:
        e = ennemi_dur(R,Q,A,s-1)
        res = s-1-e
        if res < 1:
            return "v"
        else:
            return res
    
def ennemi_dur(R,Q,A,s): 
    try :
        aa = chooseMax(s,R,Q,A,0)
        if aa==deux_dur:
            return 2
        if aa==un_dur:
            return 1
    except KeyError:
        return rd.randint(1,2)
    


def smartStick(training):
    S = ["d",1,2,3,4,5,6,7,8,9,10,11,"v"]
    A = [un_dur,deux_dur]
    R = {"d" :-2,"v":2}
    Q = {}
    s0=11
    for j in range(training):
        [lS,lA] = frontprop(A,s0,R,Q,chooseBoltz)
        Q = backprop(A,lS,lA,R,Q)
    for j in range(1000):
        [lS,lA] = frontprop(A,s0,R,Q,chooseMax)
    return (Q,S)


def afficherBatonsDur(Q):
    for k in range(11,0,-1):
        try:
            print(k, ": ", Q[k,un_dur],Q[k,deux_dur])
        except KeyError:
            print(k, ": ", "etat non atteignable")
    return None

def tauxVictoireSmart(training):
    A = [un_dur,deux_dur]
    R = {"d" :-1,"v":1}
    Q=smartStick(training)[0]
    taux=0
    s0=11
    for i in range(1000):
        [lS,lA] = frontprop(A,s0,R,Q,chooseMax)
        if 1 not in lS:
            taux+=1/10
    return taux, "% de reussite"
    
