import sys
import time
import requests
import json

KNRM = "\x1B[0m"
KRED = "\x1B[31;1m"
KGRN = "\x1B[32;1m"
KYEL = "\x1B[33;1m"
KBLU = "\x1B[34;1m"
KMAG = "\x1B[35;1m"
KCYN = "\x1B[36;1m"
KWHT = "\x1B[37;1m"

def usage():
    print(KCYN + 'usage: python3 42api.py endpoint_1 endpoint_2(optional)' + KNRM)
# e.g. : python3 42api.py /v2/projects /v2/campus (configure FILTERING DATA before)

def req_api(root_ep, headers):
    #>>>>>>>>>> INITIALIZING REQUEST >>>>>>>>>>
    params = {'page' : {'number' : '1', 'size': '1'}}
    #we send a first request of size 1 to be informed by the api response header of the data total size
    r = requests.get(root_ep, headers=headers, json=params)
    #print(json.dumps(dict(r.headers), indent=4, sort_keys=True))
    #print("total:", r.headers['x-total'])
    tot = 1 if 'x-total' not in r.headers else int(r.headers['x-total'])
    #tot is the number of object, not the number of pages
    params['page']['size'] = '100'
    #we will receive 100-object chunck by api call (it's the max)
    totp = tot // int(params['page']['size'])
    totp += 1 if tot % int(params['page']['size']) else 0
    #<<<<<<<<<< INITIALIZING REQUEST <<<<<<<<<<

    #>>>>>>>>>> LOADING DATA >>>>>>>>>>
    #   REMARK
    #   requests.get 'params=' argument doesn't support nested data.
    #   an hint is to use 'json=' instead (waiting for something better)
    #   cf reponse de snicolet sur 42born2code.slack.com channel #techno_python
    data = []
    for p in range(1, totp + 1):
        params['page']['number'] = str(p)
        r = requests.get(root_ep, headers=headers, json=params)
        #handle the case where only one elem is returned
        tmp = json.loads(r.text)
        data += [tmp] if isinstance(tmp, dict) else tmp
        #api.intra.42.fr 2 requests/s limitation
        time.sleep(0.5)
    #<<<<<<<<<< LOADING DATA <<<<<<<<<<

    return data


if __name__ == '__main__':
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        usage()
        exit()

    root = "https://api.intra.42.fr"

    #>>>>>>>>>> ASKING AUTHORIZATION >>>>>>>>>>
    #where asking 42 intra for a token (ep for endpoint)
    token_ep = '/oauth/token'
    data = {
            'grant_type' : 'client_credentials',
            'client_id' : 'xx....xx',
            'client_secret' : 'xx....xx',
            'scope' : 'public projects'
    }
    token = requests.post(root + token_ep, data=data)
    #print(token.text)
    headers = {'Authorization' : 'Bearer ' + token.json()['access_token']}
    #<<<<<<<<<< ASKING AUTHORIZATION <<<<<<<<<<
   
   
    #>>>>>>>>>> REQUEST API >>>>>>>>>>
    data_1 = req_api(root + sys.argv[1], headers)
    if len(sys.argv) == 3:
        data_2 = req_api(root + sys.argv[2], headers)
    #<<<<<<<<<< REQUEST API <<<<<<<<<<
     
    
    #>>>>>>>>>> FILTERING DATA >>>>>>>>>>

    #>>>>>>> FILTERING PROJECTS (DATA_1) >>>>>>>
    #/v2/projects
        #get project_id you want to work with filtering by substring in name ("ft_ssl" for this example)
    #data_1 = [(project['id'], project['name']) for project in data_1 if "ft_ssl" in project['name']]

    #/v2/projects/:project_id/projects_users
        #keep only users who validate a given project which you know its project_id
    data_1 = [(student['user']['login'], student['user']['id']) for student in data_1 if student['validated?']]
    data_1.sort()
    #<<<<<<< FILTERING PROJECTS (DATA_1) <<<<<<<

    #>>>>>>> FILTERING CAMPUS (DATA_2) >>>>>>>
    if len(sys.argv) == 3:
        #/v2/campus
            #get the entire campus list and keep only name en ids 
        #data_2 = [(campus['id'], campus['name']) for campus in data_2]
        
        #/v2/campus/:campus_id/users 
            #cross data, in the list of student who validated a given project
            #keep only these of a specific campus
        camp_user = [student['id'] for student in data_2]
        data_2 = [student[0] for student in data_1 if student[1] in camp_user]
    #<<<<<<< FILTERING CAMPUS (DATA_2) <<<<<<<

    #<<<<<<<<<< FILTERING DATA <<<<<<<<<<


    print(json.dumps(data_1, indent=4, sort_keys=True))
    print('tot_1 =', len(data_1));
    if len(sys.argv) == 3:
        print(json.dumps(data_2, indent=4, sort_keys=True))
        print('tot_2 =', len(data_2));
