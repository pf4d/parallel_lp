from pylab           import *
from scipy.sparse    import csr_matrix
from multiprocessing import Queue, cpu_count
from src.pLPSolve    import solveProcess

#===============================================================================
# load the data :
import pickle
f  = open('data/operators_2000m.p', 'rb')
op = pickle.load(f)

data    = op['data']
indices = op['indices']
indptr  = op['indptr']
vec     = op['vec']

# convert the data :
matSp    = csr_matrix((data, indices, indptr))
m, n     = shape(matSp)

fluxDivCnst = matSp[:2*n,:]
fluxDivData = fluxDivCnst.data
fluxDivVec  = vec[:2*n]
identCnst   = matSp[2*n:4*n,:]
identData   = identCnst.data
identVec    = vec[2*n:4*n]
gradCnst    = matSp[4*n:,:]
gradData    = gradCnst.data
gradVec     = vec[4*n:] 


def condition_variables(cnstMat, vec):
  '''
  convert a sparse constraint matrix and constraint array to format used 
  by the solver.
  '''
  row, col = cnstMat.nonzero()
  data     = cnstMat.data
  m, n     = shape(cnstMat)
  G = []
  for i in range(m):
    G.append((int(row[i]), int(col[i]), data[i]))
  h = vec.tolist()
  return (m,n), G, h

# get variables used by solver :
shp, G, h = condition_variables(matSp, vec)
m = shp[0]
n = shp[1]

# split the problem into equal parts numbering the processor count :
cs      = identity(n)
numCpus = cpu_count()
cs      = array_split(cs, numCpus)


#===============================================================================
# create a min solver for each processor and begin solving each :
solversMin = []
minQueue   = []
for i in range(numCpus):
  q = Queue()
  minQueue.append(q)
  solverMin = solveProcess(q, (m,n), G, cs[i], h, False)
  solversMin.append(solverMin)
  solverMin.start()

# wait until the min solver finishes :
for mn in solversMin:
  mn.join()

# create a max solver for each processor and begin solving each :
solversMax = []
maxQueue   = []
for i in range(numCpus):
  q = Queue()
  maxQueue.append(q)
  solverMax = solveProcess(q, (m,n), G, cs[i], h, True)
  solversMax.append(solverMax)
  solverMax.start()

# wait until the max solver finishes :
for mx in solversMax:
  mx.join()


#===============================================================================
# retrieve the min results :
minSol = []
for mq in minQueue:
  while mq.empty() == False:
    minSol.append(mq.get())
minSol    = array(minSol)
minStatus = minSol[:,2]
notOptMin = minStatus[where(minStatus != 'opt')[0]]  # array of non-optimal soln
if len(notOptMin) != 0:
  print 'One or more minimum solutions are not optimal'

# retrieve the max results :
maxSol = []
for mq in maxQueue:
  while mq.empty() == False:
    maxSol.append(mq.get())
maxSol    = array(maxSol)
maxStatus = maxSol[:,2]
notOptMax = maxStatus[where(maxStatus != 'opt')[0]]  # array of non-optimal soln
if len(notOptMax) != 0:
  print 'One or more maximum solutions are not optimal'


#===============================================================================
# plot the results :

ymin = minSol[:,1]
ymax = maxSol[:,1]
x    = range(len(ymax))

plot(x, ymin, lw=.5, label='min')
plot(x, ymax, lw=.5, label='max')
xlabel('index')
ylabel(r'$H$')
legend()
grid()
#savefig('image.png', dpi=150)
show()



