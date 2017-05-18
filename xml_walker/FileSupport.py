class Files:
    def __init__(self, max_open=0):
        self._files = {}
        self.max_open = max_open

    def __getitem__(self, item):
        if item not in self._files:
            if len(self._files) > self.max_open:
                pop_file_name, pop_file = self._files.popitem()
                pop_file.close()
            self._files[item] = open(item, "w")
        return self._files[item]

    def close(self):
        for file_name in self._files:
            self._files[file_name].close()
            self._files[file_name] = None
