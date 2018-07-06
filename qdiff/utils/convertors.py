def listInPostDataToList(postData):
    print(postData)
    result = []
    print(list(postData.values()))
    for key in sorted(postData.keys()):
        print(key)
        if key[-2:] == '[]':
            result.append(postData.getlist(key))
    print(result)
    return result
