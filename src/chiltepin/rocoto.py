import io
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import re
#import xmltodict
#import yaml
#from datetime import datetime, timedelta


class Workflow:

    def __init__(self, xmlfile):
        self.xmlfile = xmlfile
        self.tree = ET.parse(xmlfile)
        self.root = self.tree.getroot()
        for m in self.root.findall("./metatask"):
            self.expand_metatask(m, self.root, [])
        #self.xmldict = dict(xmltodict.parse(ET.tostring(tree.getroot())))
        #self.cycledefs = {}
        #self.tasks = {}


    def __str__(self):
        # Use minidom to sanitize XML string returned by ElementTree
        ugly_string = ET.tostring(self.root, 'utf-8')
        pretty_string = minidom.parseString(ugly_string).toprettyxml(indent="    ")
        stripped_string = re.sub("^\s+$","", pretty_string, flags=re.MULTILINE)
        return "\n".join([s for s in stripped_string.splitlines() if s])
    
    
    def dump(self, xmlfile):
        if isinstance(xmlfile, str):
            with open(xmlfile, "w") as f:
                f.write(str(self))
        elif isinstance(xmlfile, io.IOBase):
            xmlfile.write(str(self))
        else:
            raise TypeError("Only strings and file objects are allowed")
    

    def expand_metatask(self, element, parent, metatask_list):
        # Make sure this is a metatask node
        assert(element.tag == "metatask")

        # Get this metatask's name
        name = element.attrib["name"]

        # Expand this metatask's metatasks
        for e in element.findall("./metatask"):
            self.expand_metatask(e, element, metatask_list + [name])

        # Extract this metatask's <var> lists
        vartags = element.findall("./var")
        varlists = {}
        varsize = None
        for vartag in vartags:
            varlist = vartag.text.split()
            if varsize == None:
                varsize = len(varlist)
            # Make sure all <var> lists are the same length
            assert len(varlist) == varsize
            varlists[vartag.attrib["name"]] = varlist

        # Expand this metatask's tasks
        tasks = element.findall("./task")
        newtasks = []
        for i in range(varsize):
            for task in tasks:
                taskstr = ET.tostring(task, encoding="unicode")
                for varname, value in varlists.items():
                    taskstr = re.sub(rf"#{varname}#", varlists[varname][i], taskstr)
                newtask = ET.XML(taskstr)
                newtask.set("metatasks", " ".join(metatask_list))
                newtasks.append(newtask)
        
        # Get the insertion point for the new tasks
        metatask_idx = list(parent).index(element)

        # Insert new tasks at metatask index
        for task in reversed(newtasks):
            parent.insert(metatask_idx, task)

        # Remove the metatask
        parent.remove(element)


    #def parse(self):
    #    for c in self.xmldict["workflow"]["cycledef"]:
    #        group = c["@group"]
    #        spec = c["#text"].split()
    #        self.cycledefs[group] = CycleDef(group, spec)
    #
    #    for t in self.xmldict["workflow"]["task"]:
    #        name = t["@name"]
    #        spec = t
    #        self.tasks[name] = Task(name, spec)
                           
                           
#class CycleDef:
#
#    def __init__(self, group, spec):
#        self.group = group
#        self.start = datetime.strptime(spec[0], "%Y%m%d%H%M")
#        self.stop = datetime.strptime(spec[1], "%Y%m%d%H%M")
#        self.interval = timedelta()
#        factor = [1, 60, 3600, 86400]
#        for i, t in enumerate(reversed(spec[2].split(":"))):
#            self.interval += timedelta(seconds=int(t) * factor[i])
#
#            
#    def __str__(self):
#        return f"""CycleDef("{self.group}", "{self.start}", "{self.stop}", "{self.interval}")"""
#
#
#    __repr__ = __str__
#
#
#class Task:
#
#    def __init__(self, name, spec):
#        self.name = name
#        self.command = spec["command"]
#        
#
#    def __str__(self):
#        return f"""Task("{self.name}")"""
#
#
#    __repr__ = __str__
