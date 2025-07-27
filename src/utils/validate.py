def validateNumber(value):
    if value:
        try:
            float(value)
            return True
        except ValueError: 
            return False
    else:
        return False