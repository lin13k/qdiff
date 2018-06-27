from difflib import Differ
import re


class FieldComparator:
    def __init__(self, dataReader1, dataReader2,
                 ignoredFields1=[], ignoredFields2=[], taskModel=None):
        self._dataReader1 = dataReader1
        self._dataReader2 = dataReader2
        self._ignoredFields1 = ignoredFields1
        self._ignoredFields2 = ignoredFields2
        self._model = taskModel

    def isSame(self):
        # get fields schema
        schema1 = self._dataReader1.getSchema()
        schema2 = self._dataReader2.getSchema()
        # compare field by field
        # check if fieldname are the same, respect to the ignored lists
        fields1 = schema1['fields']
        fields2 = schema2['fields']
        ignoreList1 = self._ignoredFields1
        ignoreList2 = self._ignoredFields2
        for index in range(len(fields1) - 1, -1, -1):
            if fields1[index]['name'] in ignoreList1:
                fields1.pop(index)
        for index in range(len(fields2) - 1, -1, -1):
            if fields2[index]['name'] in ignoreList2:
                fields2.pop(index)

        fields1 = [str(i) for i in sorted(fields1, key=lambda x: x.items())]
        fields2 = [str(i) for i in sorted(fields2, key=lambda x: x.items())]
        # fields2 = sorted(list(fields1.items()))
        d = Differ()
        diff = d.compare(fields1, fields2)
        result = [line for line in diff if re.match('^[-+] ', line)]
        if len(result) > 0:
            if self._model:
                self._model.result = 'Fields are inconsistent!'
                self._model.result_detail = '<@#$>'.join(result)
                self._model.save()
            return False
        return True


class ValueComparator:
    """Comparator is used to compare the given data and find the differences"""

    def __init__(self, dataReader1, dataReader2,
                 writer1=None, writer2=None,
                 ignoredFields1=[], ignoredFields2=[], taskModel=None):
        self._dataReader1 = dataReader1
        self._dataReader2 = dataReader2
        self._ignoredFields1 = ignoredFields1
        self._ignoredFields2 = ignoredFields2
        self._writer1 = writer1
        self._writer2 = writer2
        self._model = taskModel

    # get the mask of the given columns and ignoredFields
    # for example, when
    #   columns=['col1', 'col2', 'col3']
    #   ignoredFields=['col2', 'col3']
    #   output will be [True, False, False]
    def _getMask(self, columns, ignoredFields):
        result = []
        for col in columns:
            if col in ignoredFields:
                result.append(False)
            else:
                result.append(True)
        return result

    def isSame(self):
        dataList1 = sorted(
            self._dataReader1.getRowsList(),
            key=lambda x: str(x))
        dataList2 = sorted(
            self._dataReader2.getRowsList(),
            key=lambda x: str(x))
        mask1 = self._getMask(
            self._dataReader1.getColumns(),
            self._ignoredFields1)
        mask2 = self._getMask(
            self._dataReader2.getColumns(),
            self._ignoredFields2)
        index1, index2 = 0, 0
        tempDict1 = {}
        tempDict2 = {}
        isSame = True
        diffCount = 0
        while index1 < len(dataList1) and index2 < len(dataList2):
            item1 = dataList1[index1]
            item2 = dataList2[index2]

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
                    diffCount += len(tempDict2)
                    self._writer2.writeAll(tempDict2.values())
                    tempDict2 = {}
                    index1 += 1
                if h2 in tempDict1:
                    tempDict1.pop(h2)
                    diffCount += len(tempDict1)
                    self._writer1.writeAll(tempDict1.values())
                    tempDict1 = {}
                    index2 += 1
            else:
                isSame = False
                tempDict1[h1] = item1
                tempDict2[h2] = item2
                index1 += 1
                index2 += 1

        if len(tempDict2) > 0:
            diffCount += len(tempDict2)
            isSame = False
            self._writer2.writeAll(tempDict2.values())
        if len(tempDict1) > 0:
            diffCount += len(tempDict1)
            isSame = False
            self._writer1.writeAll(tempDict1.values())

        if index1 != len(dataList1):
            isSame = False
            diffCount += len(dataList1[index1:])
            self._writer1.writeAll(dataList1[index1:])

        if index2 != len(dataList2):
            isSame = False
            diffCount += len(dataList2[index2:])
            self._writer2.writeAll(dataList2[index2:])

        if isSame is False:
            if self._model:
                self._model.result = 'Record difference found!'
                self._model.result_detail = (
                    'Found total %s differences.' % diffCount)
                self._model.save()
            return False
        if self._model:
            count = len(dataList1) + len(dataList2)
            self._model.result = 'No difference found, congrats'
            self._model.result_detail = (
                'Searched total %s records' % (count))
            self._model.save()
        return True
