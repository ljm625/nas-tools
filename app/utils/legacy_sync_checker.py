import os
from threading import Thread
import time
import log
import json
from watchdog.events import FileCreatedEvent

class LegacySync():
    def __init__(self,timeout=10):
        self.timeout= timeout
        self.handler = None
        self.path = None
        self.recursive = False
        self.thread = None
        self.stop = False
    
    def schedule(self,handler,path,recursive):
        self.handler = handler
        self.path = path
        self.recursive = recursive
    
    def start(self):
        if self.handler and self.path and not self.thread:
            print("Start listen thread")
            self.stop = False
            self.thread = Thread(target=self.run)
            self.thread.start()
    def stop(self):
        self.stop = True
        self.thread.join()
        self.thread = None
        
    def run(self):
        old_structure = self.find_and_list_path(self.path)
        while True:
            if self.stop:
                break
            structure = self.find_and_list_path(self.path)
            result = self.compare(self.path,structure,old_structure)
            old_structure = structure
            if result:
                log.info(json.dumps(result))
                for item in result:
                    event = FileCreatedEvent(item[1])
                    action = item[2]
                    if action == "create":
                        self.handler.on_created(event)
            time.sleep(self.timeout)
    def find_and_list_path(self,path):
        structure = {}
        items = os.listdir(path)
        for item in items:
            if os.path.isdir(os.path.join(path,item)):
                structure[item]= self.find_and_list_path(os.path.join(path,item))
            else:
                structure[item]=1
        return structure
    
    def compare(self,path,new,old):
        result = []
        missing_key = old.keys()-new.keys()
        for key,value in new.items():
            if type(value)==dict:
                old_value = {}
                if old.get(key):
                    if type(old[key])==dict:
                        old_value = old[key]
                result.extend(self.compare(os.path.join(path,key),value,old_value))
            else:
                if old.get(key):
                    old_value = old[key]
                    if type(old_value)==dict:
                        result.extend(self.compare(os.path.join(path,key),{},old_value))
                    else:
                        if value !=old_value:
                            result.append([os.path.join(path,key),"modify"])
                else:
                    # NEW FILE
                    result.append([os.path.join(path,key),"create"])
        for key in missing_key:
            old_value = old[key]
            if type(old_value)==dict:
                result.extend(self.compare(os.path.join(path,key),{},old_value))
            else:
                result.append([os.path.join(path,key),"delete"])
        return result



