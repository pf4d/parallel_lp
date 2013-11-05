#
#    Copyright (C) <2012>  <cummings.evan@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from multiprocessing import Process 
import glpk
import time


class solveProcess(Process):
  '''
  solver process which holds the matrix data and glpk LPX linear program 
  instance.
  INPUTS :
    queue  - queue containing all the return object values
    (m, n) - size of constraint matrix in m rows, n cols.
    G      - constraint matrix
    cs     - objective function array
    h      - constraint left hand side
    maxi   - boolean, True = maximize, False = minimize
  '''
  def __init__(self, queue, (m,n), G, cs, h, maxi):
    Process.__init__(self)
    lp = glpk.LPX()                      # Create empty problem instance
    lp.name = 'iceHeight'                # Assign symbolic name to problem
    lp.obj.maximize = maxi               # Set this as a maximization problem
    
    lp.rows.add(m)                       # Append m rows to this instance
    for row in lp.rows:                  # Iterate over all rows
      row.name = 'y%d' % row.index       # Name them y0, y1, ... , ym
      row.bounds = None, h[row.index]    # Set bound -inf < yi <= hi
    
    lp.cols.add(n)                       # Append n columns to this instance
    for col in lp.cols:                  # Iterate over all columns
      col.name = 'x%d' % col.index       # Name them x0, x1, ..., xn
      col.bounds = 0.0, 3000             # Set bound 0 <= xi < inf
    lp.matrix = G 
    
    glpk.env.term_on = False             # silence output
    
    self.q    = queue
    self.i    = 0
    self.lp   = lp
    self.cs   = cs
  
  def run(self):
    '''
    Use to start the solver Process.
    '''
    self.solveOne(0)
  
  def solveOne(self, k):
    '''
    Recursive algorithm iterates through the array of objective functions (cs)
    and solves.
    '''
    if k < len(self.cs):
      self.lp.obj[:] = self.cs[self.i].tolist()
      print 'Solving:', self.i
      t0  = time.time()
      self.lp.simplex()
      tf  = time.time()
      t   = tf - t0
      self.i += 1
      self.q.put([self.i, self.lp.obj.value, self.lp.status, t])
      return self.solveOne(k+1)



