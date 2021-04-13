import numpy
import pandas as pd
import progressbar as pb

def matrix_factorization(R,P,Q,K,steps=1000,alpha=0.0002,beta=0.02):
    Q=Q.T
    for step in range(steps):
        for i in range(len(R)):
            for j in range(len(R[i])):
                if R[i][j]>0:
                    eij=R[i][j]-numpy.dot(P[i,:],Q[:,j])
    
                    for k in range(K):
                        P[i][k]=P[i][k]+alpha*(2*eij*Q[k][j]-beta*P[i][k])
                        Q[k][j]=Q[k][j]+alpha*(2*eij*P[i][k]-beta*Q[k][j])
       # eR=numpy.dot(P,Q)
        e=0
        for i in range(len(R)):
            for j in range(len(R[i])):
                if R[i][j]>0:
                    e=e+pow(R[i][j]-numpy.dot(P[i,:],Q[:,j]),2)
                    for k in range(K):
                        e = e + (beta/2) * (pow(P[i][k],2) + pow(Q[k][j],2))
        if e<0.001:
            break
    return P,Q.T

ratings=pd.read_csv("ratings.csv")
movies=pd.read_csv("movies.csv")
ratings=pd.merge(movies,ratings).drop(columns=["genres","timestamp"])
user_ratings=ratings.pivot_table(index={'userId'},columns={'title'},values={'rating'})
user_ratings=user_ratings.fillna(0)

user_ratings=numpy.array(user_ratings)
N=len(user_ratings)
M=len(user_ratings[0])
K=2
P=numpy.random.rand(N,K)
Q=numpy.random.rand(M,K)
nP,nQ=matrix_factorization(user_ratings,P,Q,K)
nR=numpy.dot(nP,nQ.T)
nR