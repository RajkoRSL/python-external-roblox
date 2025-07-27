import struct

class vec2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

class vec3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

class quat:
    def __init__(self, x=0.0, y=0.0, z=0.0, w=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

class matrix:
    def __init__(self, data=None):
        self.data = data if data else [0.0] * 16

class instance:
    def __init__(self, address=0, memory=None):
        self.address = address
        self.memory = memory

    def readstring(self, address):
        if not self.memory or not address:
            return ""
        string = ""
        for offset in range(200):
            try:
                char = self.memory.process.read_bytes(address + offset, 1)[0]
                if char == 0:
                    break
                string += chr(char)
            except:
                break
        return string

    def readstring2(self, addr):
        if not self.memory or not addr:
            return ""
        try:
            length = self.memory.readint(addr + 0x18)
            if length >= 16:
                newaddr = self.memory.readptr(addr)
                return self.readstring(newaddr)
            else:
                return self.readstring(addr)
        except:
            return ""

    def getclass(self):
        try:
            offset = self.memory.getoffset("ClassDescriptor")
            desc = self.memory.readptr(self.address + offset)
            ptr = self.memory.readptr(desc + 0x8)
            if ptr:
                return self.readstring2(ptr)
        except Exception as e:
            pass
        return "unknown"

    def getname(self):
        try:
            offset = self.memory.getoffset("Name")
            ptr = self.memory.readptr(self.address + offset)
            return self.readstring2(ptr)
        except Exception as e:
            return ""

    def getchildren(self):
        children = []
        try:
            offset = self.memory.getoffset("Children")
            endoffset = self.memory.getoffset("ChildrenEnd")
            list = self.memory.readptr(self.address + offset)
            start = self.memory.readptr(list)
            end = self.memory.readptr(list + endoffset)
            i = start
            while i < end:
                addr = self.memory.readptr(i)
                if addr:
                    children.append(instance(addr, self.memory))
                i += 0x10
        except Exception as e:
            pass
        return children

    def findclass(self, classname):
        for child in self.getchildren():
            if child.getclass() == classname:
                return child
        return instance(0, self.memory)

    def findchild(self, name):
        for child in self.getchildren():
            if child.getname() == name:
                return child
        return instance(0, self.memory)

    def getmodel(self):
        if not self.address:
            return instance(0, self.memory)
        try:
            offset = self.memory.getoffset("ModelInstance")
            character = self.memory.readptr(self.address + offset)
            if character:
                return instance(character, self.memory)
        except Exception as e:
            pass
        return instance(0, self.memory)

    def getpos(self):
        if not self.address:
            return vec3()
        try:
            primoffset = self.memory.getoffset("Primitive")
            posoffset = self.memory.getoffset("Position")
            prim = self.memory.readptr(self.address + primoffset)
            if prim:
                data = self.memory.process.read_bytes(prim + posoffset, 12)
                x, y, z = struct.unpack('fff', data)
                return vec3(x, y, z)
        except Exception as e:
            pass
        return vec3()

    def getsize(self):
        if not self.address:
            return vec3()
        try:
            primoffset = self.memory.getoffset("Primitive")
            sizeoffset = self.memory.getoffset("PartSize")
            prim = self.memory.readptr(self.address + primoffset)
            if prim:
                data = self.memory.process.read_bytes(prim + sizeoffset, 12)
                x, y, z = struct.unpack('fff', data)
                return vec3(x, y, z)
        except Exception as e:
            pass
        return vec3()

    def gethealth(self):
        if not self.address:
            return 0.0
        try:
            offset = self.memory.getoffset("Health")
            one = self.memory.readptr(self.address + offset)
            two = self.memory.readptr(self.memory.readptr(self.address + offset))
            conv = one ^ two
            return struct.unpack('f', struct.pack('Q', conv))[0]
        except Exception as e:
            return 0.0

    def getmaxhealth(self):
        if not self.address:
            return 0.0
        try:
            offset = self.memory.getoffset("MaxHealth")
            one = self.memory.readptr(self.address + offset)
            two = self.memory.readptr(self.memory.readptr(self.address + offset))
            conv = one ^ two
            return struct.unpack('f', struct.pack('Q', conv))[0]
        except Exception as e:
            return 0.0

class utils:
    def __init__(self, memory):
        self.memory = memory

    def worldtoscreen(self, pos, matrix, dims):
        try:
            q = quat()
            q.x = (pos.x * matrix.data[0]) + (pos.y * matrix.data[1]) + (pos.z * matrix.data[2]) + matrix.data[3]
            q.y = (pos.x * matrix.data[4]) + (pos.y * matrix.data[5]) + (pos.z * matrix.data[6]) + matrix.data[7]
            q.z = (pos.x * matrix.data[8]) + (pos.y * matrix.data[9]) + (pos.z * matrix.data[10]) + matrix.data[11]
            q.w = (pos.x * matrix.data[12]) + (pos.y * matrix.data[13]) + (pos.z * matrix.data[14]) + matrix.data[15]
            
            if q.w < 0.1:
                return vec2(-1, -1)
            
            ndc = vec3()
            ndc.x = q.x / q.w
            ndc.y = q.y / q.w
            ndc.z = q.z / q.w
            
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
            width = screen.width()
            height = screen.height()
            
            x = (width / 2.0) * (1.0 + ndc.x)
            y = (height / 2.0) * (1.0 - ndc.y)
            
            return vec2(x, y)
        except Exception as e:
            return vec2(-1, -1)

    def getmatrix(self, addr):
        try:
            offset = self.memory.getoffset("viewmatrix")
            data = self.memory.process.read_bytes(addr + offset, 64)
            floats = list(struct.unpack('16f', data))
            return matrix(floats)
        except Exception as e:
            return matrix()

    def getdims(self, addr):
        try:
            offset = self.memory.getoffset("Dimensions")
            data = self.memory.process.read_bytes(addr + offset, 8)
            x, y = struct.unpack('ff', data)
            return vec2(x, y)
        except Exception as e:
            print(f"Error getting dimensions: {e}")
            return vec2(800, 600)

    def getplayers(self, dm):
        players = []
        try:
            service = dm.findchild("Players")
            if service.address:
                children = service.getchildren()
                for child in children:
                    if child.getclass() == "Player":
                        players.append(child)
        except Exception as e:
            print(f"Error getting players: {e}")
        return players

    def printplayers(self, dm):
        try:
            players = self.getplayers(dm)
            print(f"\n=== Found {len(players)} Players ===")
            for i, player in enumerate(players):
                try:
                    name = player.getname()
                    classname = player.getclass()
                    character = player.getmodel()
                    print(f"Player {i+1}:")
                    print(f"  Name: {name}")
                    print(f"  Class: {classname}")
                    print(f"  Address: 0x{player.address:X}")
                    print(f"  Character Address: 0x{character.address:X}")
                    if character.address:
                        humanoid = character.findclass("Humanoid")
                        if humanoid.address:
                            health = humanoid.gethealth()
                            maxhealth = humanoid.getmaxhealth()
                            print(f"  Health: {health:.1f}/{maxhealth:.1f}")
                        head = character.findchild("Head")
                        if head.address:
                            pos = head.getpos()
                            print(f"  Head Position: ({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f})")
                    print()
                except Exception as e:
                    print(f"  Error reading player {i+1}: {e}")
        except Exception as e:
            print(f"Error in printplayers: {e}")

    def getcharacters(self, dm):
        characters = []
        try:
            workspace = dm.findchild("Workspace")
            if workspace.address:
                children = workspace.getchildren()
                for child in children:
                    if child.getclass() == "Model":
                        humanoid = child.findclass("Humanoid")
                        if humanoid.address:
                            characters.append(child)
        except Exception as e:
            print(f"Error getting characters: {e}")
        return characters

    def printcharacters(self, dm):
        try:
            characters = self.getcharacters(dm)
            print(f"\n=== Found {len(characters)} Characters in Workspace ===")
            for i, character in enumerate(characters):
                try:
                    name = character.getname()
                    classname = character.getclass()
                    print(f"Character {i+1}:")
                    print(f"  Name: {name}")
                    print(f"  Class: {classname}")
                    print(f"  Address: 0x{character.address:X}")
                    humanoid = character.findclass("Humanoid")
                    if humanoid.address:
                        health = humanoid.gethealth()
                        maxhealth = humanoid.getmaxhealth()
                        print(f"  Health: {health:.1f}/{maxhealth:.1f}")
                    head = character.findchild("Head")
                    root = character.findchild("HumanoidRootPart")
                    if head.address:
                        pos = head.getpos()
                        print(f"  Head Position: ({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f})")
                    elif root.address:
                        pos = root.getpos()
                        print(f"  Root Position: ({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f})")
                    print()
                except Exception as e:
                    print(f"  Error reading character {i+1}: {e}")
        except Exception as e:
            print(f"Error in printcharacters: {e}")

class scheduler:
    def __init__(self, memory):
        self.memory = memory

    def getaddr(self):
        try:
            offset = self.memory.getoffset("task_scheduler_offset")
            return self.memory.readptr(self.memory.base + offset)
        except Exception as e:
            print(f"Error getting scheduler address: {e}")
            return 0

    def getsize(self):
        try:
            offset = self.memory.getoffset("task_scheduler_offset")
            return self.memory.readptr(self.memory.base + offset + 0x8)
        except Exception as e:
            print(f"Error getting scheduler array size: {e}")
            return 0

    def getjobname(self, addr):
        try:
            offset = self.memory.getoffset("job_name")
            ptr = addr + offset
            length = self.memory.readint(ptr + 0x18)
            if length >= 16:
                ptr = self.memory.readptr(ptr)
            bytes = self.memory.process.read_bytes(ptr, min(length, 100))
            return bytes.decode('utf-8', errors='ignore').rstrip('\x00')
        except Exception as e:
            print(f"Error getting job name for 0x{addr:X}: {e}")
            return ""

    def getjobs(self):
        jobs = []
        try:
            base = self.getaddr()
            end = self.getsize()
            i = 0
            while (base + i) < end:
                job = self.memory.readptr(base + i)
                if job and self.getjobname(job):
                    jobs.append(job)
                i += 0x10
        except Exception as e:
            print(f"Error getting scheduler job array: {e}")
        return jobs

    def getjob(self, name):
        for job in self.getjobs():
            if name in self.getjobname(job):
                return job
        return 0

    def getrenderview(self):
        job = self.getjob("RenderJob(EarlyRendering")
        offset = self.memory.getoffset("renderview_ptr")
        return self.memory.readptr(job + offset)

    def getvisual(self):
        job = self.getjob("RenderJob(EarlyRendering")
        rvoffset = self.memory.getoffset("renderview_ptr")
        veoffset = self.memory.getoffset("visualengine_ptr")
        rv = self.memory.readptr(job + rvoffset)
        return self.memory.readptr(rv + veoffset)

    def getdm(self):
        job = self.getjob("RenderJob(EarlyRendering")
        dmoffset = self.memory.getoffset("datamodel_ptr")
        offset = self.memory.getoffset("datamodel_offset")
        dm = self.memory.readptr(job + dmoffset)
        return dm + offset