import config

from common.log import *
set_log("Path")

class Path(object):


    def __init__(self, obj, idx, spd, vars, phase=None):
        self.data_keys = vars.keys()
        self.obj, self.idx, self.phase, self.spd = obj, idx, phase, spd
        try:
            self.idx = int(self.idx)
        except:
            pass

        if(not vars.has_key("loop")): vars["loop"] = False

        self.__dict__.update(vars)

        if(not self.phase):
            self.phase = config.cmdcenter.time()


    def do(self, t):
        pass


    def stop(self):
        if(self in config.state.paths):
            config.state.paths.remove(self)
    

    def __repr__(self):
        vars = dict((k, getattr(self, k)) for k in self.__dict__.keys() if k in self.data_keys)
        return "%s('%s', '%s', %f, %s, %f)" % (type(self).__name__, self.obj, str(self.idx), self.spd, str(vars), self.phase)
