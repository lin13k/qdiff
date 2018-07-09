def listInPostDataToList(postData):
    result = []
    for key in sorted(postData.keys()):
        if key[-2:] == '[]':
            result.append(postData.getlist(key))
    return result
