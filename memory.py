import pymem
import pymem.process
import psutil
import json

class manager:
    def __init__(self):
        self.process = None
        self.base = None
        self.target = "RobloxPlayerBeta.exe"
        self.offsets = {}
        self.utils = None
        self.scheduler = None
        self.loadoffsets()

    def loadoffsets(self):
        try:
            with open('offsets.json', 'r') as f:
                self.offsets = json.load(f)
            self.offsets.setdefault("task_scheduler_offset", "0x69A7500")
            self.offsets.setdefault("job_name", "0x138")
            self.offsets.setdefault("renderview_ptr", "0x218")
            self.offsets.setdefault("visualengine_ptr", "0x10")
            self.offsets.setdefault("datamodel_ptr", "0x208")
            self.offsets.setdefault("datamodel_offset", "0x1B8")
        except Exception as e:
            self.offsets = {}

    def findprocess(self, name=None):
        if name is None:
            name = self.target
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == name:
                return proc.info['pid']
        return None

    def attach(self, name=None):
        try:
            if name is None:
                name = self.target
            self.process = pymem.Pymem(name)
            module = pymem.process.module_from_name(self.process.process_handle, name)
            self.base = module.lpBaseOfDll
            from classes import utils, scheduler
            self.utils = utils(self)
            self.scheduler = scheduler(self)
            return True
        except Exception as e:
            return False

    def isopen(self):
        try:
            return self.process is not None and self.process.process_handle is not None
        except:
            return False

    def getoffset(self, name):
        string = self.offsets.get(name, "0x0")
        return int(string, 16)

    def getdm(self):
        if not self.base or not self.scheduler:
            return 0
        try:
            return self.scheduler.getdm()
        except Exception as e:
            return 0

    def getvisual(self):
        if not self.base or not self.scheduler:
            return 0
        try:
            return self.scheduler.getvisual()
        except Exception as e:
            return 0

    def getworkspace(self):
        from classes import instance
        dm = self.getdm()
        if dm:
            dminstance = instance(dm, self)
            return dminstance.findchild("Workspace")
        return instance(0, self)

    def getplayers(self):
        from classes import instance
        dm = self.getdm()
        if dm:
            dminstance = instance(dm, self)
            return dminstance.findchild("Players")
        return instance(0, self)

    def getlocal(self):
        from classes import instance
        players = self.getplayers()
        if players.address:
            offset = self.getoffset("LocalPlayer")
            addr = self.readptr(players.address + offset)
            return instance(addr, self)
        return instance(0, self)

    def getlist(self):
        service = self.getplayers()
        if service.address:
            return service.getchildren()
        return []

    def readptr(self, address):
        try:
            return self.process.read_longlong(address)
        except Exception as e:
            return 0

    def readint(self, address):
        try:
            return self.process.read_int(address)
        except Exception as e:
            return 0

    def writeint(self, address, value):
        try:
            self.process.write_int(address, value)
            return True
        except Exception as e:
            return False

    def readfloat(self, address):
        try:
            return self.process.read_float(address)
        except Exception as e:
            return 0.0

    def writefloat(self, address, value):
        try:
            self.process.write_float(address, value)
            return True
        except Exception as e:
            return False

    def readbytes(self, address, size):
        try:
            return self.process.read_bytes(address, size)
        except Exception as e:
            return b'\x00' * size
