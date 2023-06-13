import redis, ast, json

def rkvs_keys(printed=True):
    '''Convert rkvs.keys() into a list of normal strings
    With printed=True, write a table of keys and values to the screen
    With printed=False, return a list containing keys as normal strings
    '''
    keys = sorted(list(x.decode('UTF-8') for x in rkvs.keys()))
    if printed is True:
        for k in keys:
            if rkvs.type(k) == b'string':
                print(f'{k:25} {rkvs.get(k).decode("UTF-8")}')
            elif rkvs.type(k) == b'list':
                this = ' '.join(x.decode('UTF-8') for x in rkvs.lrange(k, 0, -1))
                print(f'{k:25} {this}')
            else:
                #print(f'{k:25} {rkvs.get(k)}')
                pass
        return()
    else:
        return(keys)

redis_host = 'info.pdf.nsls2.bnl.gov'

rkvs = redis.Redis(host=redis_host, port=6379, db=0)

my_config = {'auto_mask': False,
    'user_mask': '/nsls2/data/pdfhack/legacy/processed/xpdacq_data/user_data/my_mask_xrd.npy',
    'method': 'splitpixel'} 

def read_index_data_smart(filename,junk=None,backjunk=None,splitchar=None, do_not_float=False, shh=True, use_idex=[0,1]):
    with open(filename,'r',encoding="utf8") as infile:
        datain = infile.readlines()
    
    if junk == None:
        for i in range(len(datain)):
            try:
                for j in range(10):
                    x1,y1 = float(datain[i+j].split(splitchar)[use_idex[0]]), float(datain[i+j].split(splitchar)[use_idex[1]])
                junk = i
                break
            except:
                pass #print ('nope')
                
    if backjunk == None:
        for i in range(len(datain),-1,-1):
            try:
                x1,y1 = float(datain[i].split(splitchar)[use_idex[0]]), float(datain[i].split(splitchar)[use_idex[1]])
                backjunk = len(datain)-i-1
                break
            except:
                pass
                #print ('nope')
    
    if backjunk == 0:
        datain = datain[junk:]
    else:
        datain = datain[junk:-backjunk]
    
    xin = np.zeros(len(datain))
    yin = np.zeros(len(datain))
    
    if do_not_float:
        xin = []
        yin = []
    
    if shh == False:
        print ('length '+str(len(xin)))
    if do_not_float:
        if splitchar==None:
            for i in range(len(datain)):
                xin.append(datain[i].split()[use_idex[0]])
                yin.append(datain[i].split()[use_idex[1]])
        else:
            for i in range(len(datain)):
                xin.append(datain[i].split(splitchar)[use_idex[0]])
                yin.append(datain[i].split(splitchar)[use_idex[1]])    
    else:        
        if splitchar==None:
            for i in range(len(datain)):
                xin[i]= float(datain[i].split()[use_idex[0]])
                yin[i]= float(datain[i].split()[use_idex[1]])
        else:
            for i in range(len(datain)):
                xin[i]= float(datain[i].split(splitchar)[use_idex[0]])
                yin[i]= float(datain[i].split(splitchar)[use_idex[1]])   
        
    return xin,yin    



def stow_background(x, y):
    rkvs.set('PDF:bgd:x',str(list(x)))
    rkvs.set('PDF:bgd:y',str(list(y)))

def retrieve_background():
    x = ast.literal_eval(rkvs.get('PDF:bgd:x').decode('utf-8'))
    y = ast.literal_eval(rkvs.get('PDF:bgd:y').decode('utf-8'))
    return x,y

def stow_sample_number(sample_num):
    rkvs.set('PDF:xpdacq:sample_number', sample_num)

def retrieve_sample_number():
    return int(rkvs.get('PDF:xpdacq:sample_number').decode('utf-8'))

def stow_exposure_time(exposure_time):
    rkvs.set('PDF:desired_exposure_time',exposure_time)

def retrieve_exposure_time():
    return float(rkvs.get('PDF:desired_exposure_time').decode('utf-8'))

def stow_sample_info(sample_num):
    info =dict(bt.samples[list(bt.samples.keys())[sample_num]])
    j_info = json.dumps(info)
    rkvs.set('PDF:xpdacq:sample_info',j_info)

def retrieve_sample_info():
    j_info = rkvs.get('PDF:xpdacq:sample_info')
    return json.loads(j_info)

def stow_scanplan_num(scanplan_num):
    rkvs.set('PDF:xpdacq:scanplan_num', scanplan_num)

def retrieve_scanplan_num():
    return int(rkvs.get('PDF:xpdacq:scanplan_num').decode('utf-8'))

def redis_aware_scan(sample_num=0, exposure=5, my_config=my_config, scanplan_num=0):
   #goto_sample pos
   #update info in redis
   stow_sample_info(sample_num)
   stow_sample_number(sample_num)
   stow_pdfstream_config(my_config)
   stow_exposure_time(exposure)
   stow_scanplan_num(scanplan_num)
   xrun(sample_num, scanplan_num, user_config=my_config)
 
