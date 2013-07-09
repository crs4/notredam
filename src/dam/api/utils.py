import hashlib

def _get_final_parameters(api_key, secret, user_id, kwargs = None):
    if  not kwargs:
        kwargs = {}
    kwargs['api_key'] = api_key
    kwargs['user_id'] = user_id
    to_hash = secret
    parameters = []
    
    for key,  value in kwargs.items():
        if isinstance(value,  list):
            value.sort()
            for el in value:
                parameters.append(str(key)+str(el))
        else:                    
            parameters.append(str(key)+str(value))
    
    parameters.sort()
    for el in parameters:
        to_hash += el
        
    hashed_secret = hashlib.sha1(to_hash).hexdigest()
    kwargs['checksum'] = hashed_secret 
    return kwargs
