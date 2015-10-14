
import os, sys
# include ../.. in path to be able to import lib
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(CURRENT_DIR)))

from lib import run_demo_base
from lib.run_demo_base import RunDemoBase

from lib import run_demo_base


class RunDemo(RunDemoBase):
  
  #-----------------------------------------------------------------------------
  def __init__(self, base_dir, work_dir):
    RunDemoBase.__init__(self,base_dir, work_dir)
    self.commands=[
       "edges   -r $th_fded -p $th_fded -s $th_fded -m $sigma $n $tzc "+
               " -l $sigma2 $n2 $tzc2 -h $rho input_0.sel.png" ]

  #-----------------------------------------------------------------------------
  def run_algo(self, timeout=False):
    """
    the core algo runner
    could also be called by a batch processor
    """
    
    # convert parameters to variables
    for k in self.algo_params:
      exec("{0} = {1}".format(k,repr(self.algo_params[k])))
    
    # if run several commands, is it in series?
    cmds = self.commands[0].split()
    # replace variables
    for i,p in enumerate(cmds):
      if p[0]=='$':
        cmds[i] = str(eval(p[1:]))
    
    p = self.run_proc(cmds)
    self.wait_proc(p)

 