class Files:
    """
    This class provides helper functions for working with file sets
    """
    def __init__(self, max_open=0):
        """

        :param max_open: number of maximum parallel opened files
        """
        self._files = {}
        self._initialized = set()
        self.max_open = max_open

    def __getitem__(self, item):
        """
        Array index function for file access

        This function returns a file handle to the wanted file. The file handle could be cached with respect to the
        maximum number of open files
        :param item: filename
        :return: file handle
        """
        if item not in self._files:
            if len(self._files) > self.max_open:
                pop_file_name, pop_file = self._files.popitem()
                pop_file.close()
            if item in self._initialized:
                self._files[item] = open(item, "a")
            else:
                self._initialized.add(item)
                self._files[item] = open(item, "w")
        return self._files[item]

    def close(self):
        """
        closes all files
        :return:
        """
        for file_name in self._files:
            self._files[file_name].close()
            self._files[file_name] = None
