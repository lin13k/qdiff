class Comparator:
    """Comparator is used to compare the given data and find the differences"""

    def __init__(self, data_reader1, data_reader2,
                 writer1=None, writer2=None, ignore_fields=[]):
        self.data_reader1 = data_reader1
        self.data_reader2 = data_reader2
        self.ignore_fields = ignore_fields
        self.writer1 = writer1
        self.writer2 = writer2

    def compare(self):
        data_list1 = sorted(self.data_reader1.getRowsList())
        data_list2 = sorted(self.data_reader2.getRowsList())
        index1, index2 = 0, 0
        temp_dict1 = {}
        temp_dict2 = {}
        while index1 < len(data_list1) and index2 < len(data_list2):
            item1 = data_list1[index1]
            item2 = data_list2[index2]

            # TODO, apply ignore_fields in hash
            h1 = hash(item1)
            h2 = hash(item2)
            if h1 == h2:
                index1 += 1
                index2 += 1
            elif h1 in temp_dict2 or h2 in temp_dict1:
                if h1 in temp_dict2:
                    temp_dict2.pop(h1)
                    self.writer2.writeAll(temp_dict2.values())
                    temp_dict2 = {}
                    index1 += 1
                if h2 in temp_dict1:
                    temp_dict1.pop(h2)
                    self.writer1.writeAll(temp_dict1.values())
                    temp_dict1 = {}
                    index2 += 1
            else:
                temp_dict1[h1] = item1
                temp_dict2[h2] = item2
                index1 += 1
                index2 += 1

        if len(temp_dict2) > 0:
            self.writer2.writeAll(temp_dict2.values())
            temp_dict2 = {}
        if len(temp_dict1) > 0:
            self.writer1.writeAll(temp_dict1.values())
            temp_dict1 = {}

        if index1 != len(data_list1):
            self.writer1.writeAll(data_list1[index1:])

        if index2 != len(data_list2):
            self.writer2.writeAll(data_list2[index2:])
