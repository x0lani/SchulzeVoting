#TODO:  allow voting for ties
#TODO:  show and tabulate ties
#TODO:  make weight part of ballot, maybe not a good idea
#TODO:  PathStrength class

import datetime

class Ballot(object):
    def __init__(self,orderedCandidates=None):
        self._tally={}
        if orderedCandidates is None:
            # Empty ballot.
            self._candidates=[]
            return
        if len(orderedCandidates) != len(set(orderedCandidates)):
            raise ValueError("Duplicate candidates on ballot")
        self._candidates=list(map((lambda x: x.casefold()),orderedCandidates))
        for i in range(len(self._candidates)-1):
            for j in range(i+1, len(self._candidates)):
                self._set(self._candidates[i],self._candidates[j],1)
        return

    def _set(self,primary,secondary,votes):
        ''' Internal function. Not intended for use outside of class.'''
        primary=primary.casefold()
        secondary=secondary.casefold()
        self._tally[(primary,secondary)]=votes
        if not primary in self._candidates:
            self._candidates.append(primary)
        if not secondary in self._candidates:
            self._candidates.append(secondary)
        return

    def get(self,primary,secondary):
        return self._tally.get((primary.casefold(),secondary.casefold()),0)

    def __str__(self):
        return str(dict(self._tally.items()))

    def __add__(self,other):
        if len(set.symmetric_difference(set(self._candidates),
                                        set(other._candidates))) !=0:
            raise ValueError("Candidates on ballots do not match")
        result=Ballot()
        result._candidates=self._candidates.copy()
        preferences=set(list(self._tally.keys()) + list(other._tally.keys()))
        for matchup in preferences:
            result._tally[matchup]=self.get(matchup[0],matchup[1]) + \
                                   other.get(matchup[0],matchup[1])
        return result

    def __mul__(self,other):
        result=Ballot()
        for k in self._tally:
            result._tally[k]=self._tally[k]*other
        result._candidates=self.candidates()
        return result

    def __rmul__(self,other):
        return self * other

    def candidates(self):
        return self._candidates.copy()

    def delCandidate(self,candidate):
        matchups=list(self._tally.keys())
        for matchup in matchups:
            if candidate in matchup:
                del self._tally[matchup]
        self._candidates.remove(candidate)
        return

    def extend(self,candidates,weight=1):
        ''' Add weak candidate to the candidate list. The weak
            candidate will lose to all other candidates by weight.'''
        candidates=[x.casefold() for x in candidates]
        new=list(set.difference(set(candidates),set(self._candidates)))
        for n in new:
            for c in self._candidates:
                self._tally[(c,n)]=weight
        self._candidates.extend(new)

    def printMatrix(self):
        candidates=sorted(self.candidates())
        if len(candidates)==0:
            return
        n = len(candidates)
        print('\t*,',end='')
        print('\t*,'.join(candidates))
        for c in candidates:
            print(c+',*',end='\t')
            for col in candidates:
                if col==c:
                    print('X\t',end='')
                else:
                    print(self.get(c,col),end='\t')
            print()
        return

    def copy(self):
        '''create shallow copy of Ballot'''
        returnBallot=Ballot()
        returnBallot._candidates=self._candidates.copy()
        returnBallot._tally=self._tally.copy()
        return returnBallot

    def prune(self):
        '''Drop candidates which beat no other candidates and return deleted candidates'''
        candidates=self.candidates()
        delList=[]
        for i in candidates:
            remove = True
            for j in candidates:
                if i !=j :
                    if self.get(i,j) > self.get(j,i):
                        remove = False
                        break
            if remove:
                delList.append(i)
        for i in delList:
            self.delCandidate(i)
        return delList

def calcPaths(ballots):
    if not hasattr(ballots,'__iter__'):
        ballots=[ballots]
    total=ballots[0].copy()
    for ballot in ballots[1:]:
        total+=ballot
    candidates=total.candidates()
    graph=Ballot()
    print("\tEliminating weak pairwise preferences...")
    for i in candidates:
        for j in candidates:
            if i != j:
                if total.get(i,j) > total.get(j,i):
                    graph._set(i,j,total.get(i,j))
                else:
                    graph._set(i,j,0)
    print("\tTotal candidates =",len(graph.candidates()))
    print("\tCalculating strongest paths...")
    print("\tCandidates evaluated...")
    count=0
    for i in candidates:
        # user feedback
        if count%10==0:
            print('\t\t',count,'\t',str(datetime.datetime.now()),sep='')

        # Floyd–Warshall algorithm for strongest path
        for j in candidates:
            if i != j:
                for k in candidates:
                    if i != k and j != k:
                        graph._set(j,k,\
                                        max(graph.get(j,k), \
                                            min(graph.get(j,i),\
                                                graph.get(i,k))))
        count+=1
    return graph

def rank(paths):
    candidates=paths.candidates()
    results=[candidates[0]]
    candidates=candidates[1:]
    for contender in candidates:
        j=0
        while j < len(results):
            incumbent=results[j]
            if paths.get(contender,incumbent)>paths.get(incumbent,contender):
                break
            # Uncomment following to catch ties
##            elif paths.get(contender,incumbent)==paths.get(incumbent,contender):
##                print("current ladder =",results)
##                raise ValueError('Tie occurred between '+contender+' and '+ incumbent)
            j+=1
        results=results[:j]+[contender]+results[j:]
    return results

if __name__=='__main__':
    test=Ballot('bcd')
    test.extend('a')
    print("test is : " ,test)
    print("test's candidates are : ",test.candidates())
    test2=Ballot('ab')
    test2.extend('cd')
    print("test2 is : " ,test2)
    print("test2's candidates are : ",test2.candidates())
    total=test+test2
    print("total candidates are : ",total.candidates())    
    total.printMatrix()

    test3=5 * Ballot('ACBED') + 5 * Ballot('ADECB') + \
           8 * Ballot('BEDAC') + 3 * Ballot('CABED') + 7 * Ballot('CAEBD') + \
           2 * Ballot('CBADE') + 7 * Ballot('DCEBA') + 8 * Ballot('EBADC')
    print(test3)
    print('** computing test3 strengths **')
    p=calcPaths(test3)
    r=rank(p)


