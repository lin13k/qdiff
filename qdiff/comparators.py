class FieldComparator:
    pass


class ValueComparator:
    """Comparator is used to compare the given data and find the differences"""

    def __init__(self, dataReader1, dataReader2,
                 writer1=None, writer2=None,
                 ignoredFields1=[], ignoredFields2=[]):
        self.dataReader1 = dataReader1
        self.dataReader2 = dataReader2
        self.ignoredFields1 = ignoredFields1
        self.ignoredFields2 = ignoredFields2
        self.writer1 = writer1
        self.writer2 = writer2

    # get the mask of the given columns and ignoredFields
    # for example, when
    #   columns=['col1', 'col2', 'col3']
    #   ignoredFields=['col2', 'col3']
    #   output will be [True, False, False]
    def getMask(self, columns, ignoredFields):
        result = []
        for col in columns:
            if col in ignoredFields:
                result.append(False)
            else:
                result.append(True)
        return result

    def compare(self):
        dataList1 = sorted(self.dataReader1.getRowsList())
        dataList2 = sorted(self.dataReader2.getRowsList())
        mask1 = self.getMask(
            self.dataReader1.getColumns(),
            self.ignoredFields1)
        mask2 = self.getMask(
            self.dataReader2.getColumns(),
            self.ignoredFields2)
        index1, index2 = 0, 0
        tempDict1 = {}
        tempDict2 = {}
        while index1 < len(dataList1) and index2 < len(dataList2):
            item1 = dataList1[index1]
            item2 = dataList2[index2]

            # TODO, apply ignoreFields in hash
            h1 = hash(tuple(item1[i] for i in range(len(item1)) if mask1[i]))
            h2 = hash(tuple(item2[i] for i in range(len(item2)) if mask2[i]))
            # h1 = hash(item1)
            # h2 = hash(item2)
            if h1 == h2:
                index1 += 1
                index2 += 1
            elif h1 in tempDict2 or h2 in tempDict1:
                if h1 in tempDict2:
                    tempDict2.pop(h1)
                    self.writer2.writeAll(tempDict2.values())
                    tempDict2 = {}
                    index1 += 1
                if h2 in tempDict1:
                    tempDict1.pop(h2)
                    self.writer1.writeAll(tempDict1.values())
                    tempDict1 = {}
                    index2 += 1
            else:
                tempDict1[h1] = item1
                tempDict2[h2] = item2
                index1 += 1
                index2 += 1

        if len(tempDict2) > 0:
            self.writer2.writeAll(tempDict2.values())
            tempDict2 = {}
        if len(tempDict1) > 0:
            self.writer1.writeAll(tempDict1.values())
            tempDict1 = {}

        if index1 != len(dataList1):
            self.writer1.writeAll(dataList1[index1:])

        if index2 != len(dataList2):
            self.writer2.writeAll(dataList2[index2:])
