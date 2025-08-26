from collections import defaultdict

# recursive defaultdict that becomes dict on serialization
class AutoDict(defaultdict):
    def __init__(self):
        super().__init__(AutoDict)

    def to_dict(self):
        return {k: (v.to_dict() if isinstance(v, AutoDict) else v) 
                for k, v in self.items()}