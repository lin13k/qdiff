class FieldComparator:
    pass


class ValueComparator:
    """Comparator is used to compare the given data and find the differences"""

    def __init__(self, data_reader1, data_reader2,
                 writer1=None, writer2=None,
                 ignored_fields1=[], ignored_fields2=[]):
        self.data_reader1 = data_reader1
        self.data_reader2 = data_reader2
        self.ignored_fields1 = ignored_fields1
        self.ignored_fields2 = ignored_fields2
        self.writer1 = writer1
        self.writer2 = writer2

    # get the mask of the given columns and ignored_fields
    # for example, when
    #   columns=['col1', 'col2', 'col3']
    #   ignored_fields=['col2', 'col3']
    #   output will be [True, False, False]
    def getMask(self, columns, ignored_fields):
        result = []
        for col in columns:
            if col in ignored_fields:
                result.append(False)
            else:
                result.append(True)
        return result

    def compare(self):
        data_list1 = sorted(self.data_reader1.getRowsList())
        data_list2 = sorted(self.data_reader2.getRowsList())
        mask1 = self.getMask(
            self.data_reader1.getColumns(),
            self.ignored_fields1)
        mask2 = self.getMask(
            self.data_reader2.getColumns(),
            self.ignored_fields2)
        index1, index2 = 0, 0
        temp_dict1 = {}
        temp_dict2 = {}
        while index1 < len(data_list1) and index2 < len(data_list2):
            item1 = data_list1[index1]
            item2 = data_list2[index2]

            # TODO, apply ignore_fields in hash
            h1 = hash(tuple(item1[i] for i in range(len(item1)) if mask1[i]))
            h2 = hash(tuple(item2[i] for i in range(len(item2)) if mask2[i]))
            # h1 = hash(item1)
            # h2 = hash(item2)
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
