class Files:
    def __init__(self, max_open=0):
        self._files = {}
        self.max_open = max_open

    def __getitem__(self, item):
        if item not in self._files:
            if len(self._files) > self.max_open:
                pop_file = self._files.popitem()
                pop_file.close()
            self._files[item] = open(item, "w")
        return self._files[item]
