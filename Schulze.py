#TODO:  allow voting for ties
#TODO:  multithreading for large candidate sets
#TODO:  weight and change weight

from pprint import pprint
import datetime

class Ballot(object):
    def __init__(self,orderedCandidates=None,ID=None):
        self.ID=ID      # Tag to identify ballot. Unused internally. Could be used for serial number.
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

    def __str__(self):
        return str(dict(self._tally.items()))

    def __add__(self,other):
        if len(set.symmetric_difference(set(self._candidates),
                                        set(other._candidates))) !=0:
            raise ValueError("Unable to combine. Candidates on ballots do not match")
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

    def __eq__(self, other):
        return self._tally.items()==other._tally.items()

    def __ne__(self, other):
        return not self == other

    def candidates(self):
        return self._candidates.copy()

    def remove(self,candidate):
        ''' Remove candidate and all associated pairings '''
        if candidate not in self._candidates:
            raise KeyError('Candidate not found')
        self._candidates.remove(candidate)
        matchups=list(self._tally.keys())
        for matchup in matchups:
            if candidate in matchup:
                del self._tally[matchup]
        return

    def extend(self,candidates,weight=1):
        """
        Add candidate(s) to the candidate list such that they are all the weakest.
        Any existing candidates will be ignored.
        The new candidate(s) will lose to all existing candidates by weight.
        New candidates will all be tied with each other.
        """
        if not hasattr(candidates,'__iter__'):
            candidates=[candidates]
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
                    print('--\t',end='')
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
            self.remove(i)
        return delList

    def get(self,primary, secondary):
        """ number of voters who prefer primary to secondary """
        if primary not in self._candidates or secondary not in self._candidates:
            raise KeyError((primary, secondary))
        return self._tally.get((primary.casefold(),secondary.casefold()),0)

class Graph(object):
    verbose=True
    """Provide feedback during processing."""

    def __init__(self,ballot,verbose=True):
        self.verbose=verbose
        self._ballot=ballot.copy()
        self._ladder=[]
        self._candidates=self._ballot._candidates.copy()
        self._graphCalculated=False

        # Eliminate and rank all obvious losers from the ballot
        if self.verbose: print("\tDropping obvious weak candidates.")
        dropped=['TEMP']
        while len(dropped)>0 and len(self._ballot._candidates)>0:
            dropped=self._ballot.prune()
            if len(dropped)>0:
                # insert pruned objects at top of ladder
                if len(dropped)==1:
                    # Singleton. "De-listify" it.
                    dropped=dropped[0]
                self._ladder.insert(0,dropped)
        if self.verbose: print("\t",len(self._ballot._candidates),"candidates remain")
        if len(self._ballot._candidates)==0:
            # The ballot has been completely consumed.  Processing finished.
            self._graphCalculated=True
            del self._ballot
        return

    def ladder(self):
        """
        Return list of ranked candidates from most to least preferred.
        Ties are returned as list subsets.
        """
        if not self._graphCalculated: self._calcRankings()
        return self._ladder.copy()

    def candidates(self):
        return self._candidates.copy()

    def _calcPaths(self):
        if self._graphCalculated: return
        # copy latest copy of candidates from ballot, weakest may have already been dropped
        c=self._ballot._candidates.copy()
        graph=Ballot()
        if self.verbose: print("\tNullifying weak pairwise preferences...")
        for i in c:
            for j in c:
                if i != j:
                    if self._ballot.get(i,j) > self._ballot.get(j,i):
                        graph._set(i,j,self._ballot.get(i,j))
                    else:
                        graph._set(i,j,0)
        del self._ballot    # original copied ballot no longer required

        count=0
        now=datetime.datetime.now()
        lastT=now
        numC=len(c)
        if self.verbose:
            print("\tCalculating strongest paths...")
            print("\tCandidates evaluated...")
            print('\t\t',count,'\t',now.strftime("%Y-%m-%d %H:%M:%S"),sep='')
        for i in c:
            if self.verbose and count and count%10==0:
                print('\t\t',count,'\t',now.strftime("%Y-%m-%d %H:%M:%S"),sep='',end='')
                now=datetime.datetime.now()
                estCompletion=(now-lastT)*(numC-count)/10+now
                print('\t','est finish: ',estCompletion.strftime("%Y-%m-%d %H:%M"),sep='')
                lastT=now
            count+=1

            # Using Floyd–Warshall algorithm for strongest path
            for j in c:
                if i != j:
                    for k in c:
                        if i != k and j != k:
                            graph._set(j,k,\
                                            max(graph.get(j,k), \
                                                min(graph.get(j,i),\
                                                    graph.get(i,k))))
        self._graphCalculated=True
        self._graph=graph
        return

    def _calcRankings(self):
        """
        Determine rankings based on the strongest path matrix.
        """
        if not self._graphCalculated: self._calcPaths()
        candidates=self._graph._candidates.copy()

        while len(candidates)>0:
            # find and remove weakest candidates. If tied, remove all tied candidates.
            weakest=[]
            for c in candidates:
                remove=True
                for challenger in candidates:
                    if c!=challenger:
                        if self._graph.get(c,challenger)>self._graph.get(challenger,c):
                            remove=False
                            break
                if remove: weakest.append(c)
            # Sanity check, something must be removed with each iteration
            if len(weakest)<1: raise RuntimeError('Unable to find weakest candidate.')
            # push weakest on top of ladder and remove from graph
            for c in weakest: self._graph.remove(c)
            if len(weakest)==1: weakest=weakest[0]
            self._ladder.insert(0,weakest)
            candidates=self._graph._candidates.copy()   # refresh list
        del self._graph
        return

    def printLadder(self):
        rank=1
        for c in self.ladder():
            print("{0:3n})\t".format(rank),c,sep='')
            rank+=1
        return

if __name__=='__main__':
    # test cases

    # assignment test
    t1=Ballot('abcd')
    if t1.get('a','c')!=1 or t1.get('d','b')!=0:
        raise NotImplementedError('__init__ failed')
    del t1

    # Equality tests
    t1=Ballot('abcd')
    t2=Ballot('abcd')
    if t1 == t2:
        pass
    else:
        raise NotImplementedError('Equality method failed')
    t3=Ballot('dcba')
    if t1 == t3:
        raise NotImplementedError('Equality method failed')
    if t1 != t3:
        pass
    else:
        raise NotImplementedError('Inequality method failed')
    del t1,t2,t3

    # duplication test
    t1=Ballot('abcd')
    t2=t1.copy()
    if (t1 is t2) or (t1!=t2):
        raise NotImplementedError('Copy failed')
    del t1,t2

    # deletion test
    t1=Ballot('abcd')
    t1.remove('c')
    if t1!=Ballot('abd'):
        raise NotImplementedError('Remove method failed')
    del t1

    # addition and multiplication tests
    t1=Ballot('abcd')
    t2=Ballot('abcd')
    if t1*4 != t2+t2+t2+t2:
        raise NotImplementedError('Addition and/or multiplication methods failed')
    del t1,t2

    # extend and prune tests
    t1=Ballot('abcd')
    t1.extend('XYZ')
    if set('xyz')!=set(t1.prune()):
        raise NotImplementedError('Prune and/or extend method failed')
    del t1

    # Graph creation tests
    t1= Ballot('abcd')
    g=Graph(t1,False)
    if g._ladder != list('abcd'):
        raise NotImplementedError('Simple graph creation failed')

    t2= Ballot('ab')
    t2.extend('cd')
    t2.extend('e')
    t2.extend('fg')
    g2 = Graph(t2,False)
    if g2._ladder[:2] != ['a','b'] or set(g2._ladder[2])!=set(['c','d']):
        raise NotImplementedError('Tied graph creation failed')
    print("tied ladder t2:")
    g2.printLadder()
    del t1,g,t2,g2

    # Ranking tests
    t=Ballot('abcd')
    g=Graph(t,False)
    if g.ladder()!=['a','b','c','d']:
        raise NotImplementedError('Simple graph ranking failed')
    del t,g

    # Path tests
    test=5 * Ballot('ACBED') + 5 * Ballot('ADECB') + \
       8 * Ballot('BEDAC') + 3 * Ballot('CABED') + 7 * Ballot('CAEBD') + \
       2 * Ballot('CBADE') + 7 * Ballot('DCEBA') + 8 * Ballot('EBADC')
    graph=Graph(test,False)
    r=graph.ladder()
    if r != ['e', 'a', 'c', 'b', 'd']:
        raise NotImplementedError('ranking algorithm failed')
    del test,graph,r

    # path with tie
    A=Ballot('abcd')
    B=Ballot('dabc')
    C=Ballot('cdab')
    T=A+B+C
    g=Graph(T,False)
    if g.ladder()[0]!='a' and set(g.ladder()[1])!=set('bcd'): raise NotImplementedError('ranking algorithm with tie failed')
    del A,B,C,T,g

    # Fantasy United States presidential election, 2000
    print('\n== United States presidential election, 2000 ==')
    republican=['Bush','Buchanan','Browne','Gore','Nader']
    democrat=['Gore','Nader','Browne','Bush','Buchanan']
    green=['Nader','Browne','Gore','Bush','Buchanan']
    reform=['Buchanan','Bush','Gore','Browne','Nader']
    libertarian=['Browne','Nader','Gore','Bush','Buchanan']

    repBallot=Ballot(republican)*50456002
    demBallot=Ballot(democrat)*50999897
    greenBallot=Ballot(green)*2882955
    reformBallot=Ballot(reform)*448895
    libBallot=Ballot(libertarian)*384431

    total=repBallot+demBallot+greenBallot+reformBallot+libBallot
    total.printMatrix()

    g=Graph(total)
    g.printLadder()

