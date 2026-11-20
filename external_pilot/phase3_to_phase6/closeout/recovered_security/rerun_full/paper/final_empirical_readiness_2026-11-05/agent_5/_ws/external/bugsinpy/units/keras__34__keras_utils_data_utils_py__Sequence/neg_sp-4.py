from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from abc import abstractmethod

class Sequence(object):

    @abstractmethod
    def __getitem__(self, index):
        raise NotImplementedError

    @abstractmethod
    def __len__(self):
        raise NotImplementedError

    def on_epoch_end(self):
        pass

    def __iter__(self):
        while True:
            for item in (self[i] for i in range(len(self))):
                yield item