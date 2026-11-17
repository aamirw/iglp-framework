#--------------Fringe-related functions---------------------------
# traversalMethod = ""
# fringe = None
# 
# def setTraversalMethod(method):
#    global traversalMethod
#    traversalMethod = method
# 
# def printFringe():
#    print(fringe)
#    pass
# 
# def initFringe():
#     '''Since the initialization can vary depending on the traversal method'''
#     global fringe
#     fringe = []
# 
# 
# def insert(stateSet):
#    if traversalMethod == "BFS":
#     fringe.append(stateSet)
#    
# 
# def pop():
#    global fringe
#    return fringe.pop(0)
# 
# def isEmpty():
#    if len(fringe)==0:
#       return True
#    return False

class Fringe():
    def __init__(self):
        self.traversalMethod = ""
        self.fringe = []

    def set_traversal_method(self, method):
        self.traversalMethod = method

    def print_fringe(self):
        print(self.fringe)

    def init_fringe(self):
        '''Since the initialization can vary depending on the traversal method'''
        self.fringe = []

    def insert(self, stateSet):
        if self.traversalMethod == "BFS":
            self.fringe.append(stateSet)

    def pop(self):
        return self.fringe.pop(0) if self.fringe else None

    def is_empty(self):
        return len(self.fringe) == 0
