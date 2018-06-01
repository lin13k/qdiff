class Comparator:
    """Comparator is used to compare the given data and find the differences"""

    def __init__(self, data_reader1, data_reader2,
                 writer1=None, writer2=None, ignore_fields=[]):
        self.data_reader1 = data_reader1
        self.data_reader2 = data_reader2
        self.ignore_fields = ignore_fields
        self.writer1 = writer1
        self.writer2 = writer2

    # TODO, apply ignore_fields in hash
    def compare(self):
        iter1 = iter(sorted(self.data_reader1.getRowsList()))
        iter2 = iter(sorted(self.data_reader2.getRowsList()))
        temp_dict1 = {}
        temp_dict2 = {}
        item1 = None
        item2 = None
        try:
            while True:
                item1 = tuple(next(iter1))
                item2 = tuple(next(iter2))
                # TODO, apply ignore_fields in hash
                h1 = hash(item1)
                h2 = hash(item2)
                if h1 == h2:
                    item1 = None
                    item2 = None
                    continue
                elif h1 in temp_dict2 or h2 in temp_dict1:
                    if h1 in temp_dict2:
                        temp_dict2.pop(h1)
                        self.writer2.writeAll(temp_dict2.values())
                    if h2 in temp_dict1:
                        temp_dict1.pop(h2)
                        self.writer1.writeAll(temp_dict1.values())
                else:
                    temp_dict1[h1] = item1
                    temp_dict2[h2] = item2

        except StopIteration as e:
            if item1:
                # iter1 is empty
                self.writer1.writeAll([item1] + temp_dict1.values())
            else:
                self.writer1.writeAll(temp_dict1.values())

            if item2:
                # iter2 is empty
                self.writer2.writeAll([item2] + temp_dict2.values())
            else:
                self.writer2.writeAll(temp_dict2.values())
