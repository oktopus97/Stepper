import multiprocessing

class Management(object):
    ##Management for all the multiprocessing operations
    def __init__(self):
        #queue for killing programs int values for process_ids
        self.manager = multiprocessing.Manager()
        self.workers = []


    def work(self, function, args=()):
        #returns the worker index
        worker = multiprocessing.Process(target=function,args=args)
        worker.start()
        self.workers.append(worker)
        return len(self.workers)-1

    def join(self,index):
        self.workers[index].join()
        self.workers.pop()


    @staticmethod
    def Queue(*args):
        return multiprocessing.Queue(*args)

    def list(self):
        return self.manager.list()
