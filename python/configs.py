# =============================================================================
# select Backend
# =============================================================================
import os
os.environ['KERAS_BACKEND'] = 'theano'

import numpy as np
import pandas as pd
from utils import utils_config
#import utils_config
import sys
import ast
import json

# =============================================================================
# Initial Configs
# =============================================================================
projectStage="0" 
agileIterationNum="8" # iteration number

img_height,img_width,img_channel=101,101,3 # image dimensions
#img_height,img_width,img_channel=128,128,1 # image dimensions
numOfInputConvFilters=48 # number of input conv filters
pre_train=False # use previous weights or start from scratch
nFolds=5 # number of folds for training
test_size=0.1 # portion of data to be used for local test during training
stratifyEnable=True # when spliting data into train-test, stratify or not?
seed = 2018 # fix random seed for reproducibility
initialLearningRate=1e-4
nonZeroMasksOnly=False
showModelSummary=False
numOfEpochs=500
maskThreshold=0.5
binaryThreshold=0.5
largeMaskThreshold=0
histeq=False
addDepthFlag=False
#padSize=(13,14) # to make image size 128*128
padSize=(0,0) # no zero padding
np.random.seed(seed)


pre_settings = dict()
pre_settings["agileIterationNum"]=agileIterationNum
pre_settings["stratifyEnable"]=stratifyEnable
pre_settings["projectStage"]=projectStage
pre_settings["test_size"]=test_size
pre_settings["nFolds"]=nFolds
pre_settings["pre_train"]=pre_train
pre_settings["image dimension"]=(img_height,img_width,img_channel)
pre_settings["numOfInputConvFilters"]=numOfInputConvFilters
pre_settings["initialLearningRate"]=initialLearningRate
pre_settings["nonZeroMasksOnly"]=nonZeroMasksOnly
pre_settings["numOfEpochs"]=numOfEpochs
pre_settings["showModelSummary"]=showModelSummary
pre_settings["maskThreshold"]=maskThreshold
pre_settings["padSize"]=padSize
pre_settings["largeMaskThreshold"]=largeMaskThreshold
pre_settings["histeq"]=histeq
pre_settings["c"]="continue"
pre_settings["e"]="Exit!"


contEx=utils_config.getInputFromUser(pre_settings,"Press c to Continue otherwise press e to Exit:")
if contEx is "Exit!":
    sys.exit()


#==============================================================================
# Store all outputs here
#==============================================================================

path2output="./output/"
path2output=os.path.abspath(path2output)
if not os.path.exists(path2output):
    os.makedirs(path2output)

path2data="../../data/"
path2allExperiments=os.path.join(path2output,'experiments/')
if not os.path.exists(path2allExperiments):
    os.makedirs(path2allExperiments)

path2data="../data/"
path2train=path2data+"train/"
path2test=path2data+"test/"


#==============================================================================
# Experiments
#==============================================================================
experiment=utils_config.getAnExperiment(path2allExperiments,agileIterationNum,projectStage)
path2experiment=os.path.join(path2allExperiments,experiment)

if  not os.path.exists(path2experiment):
    os.makedirs(path2experiment) # 0755 is for change owner, chown
    print ('experiment folder created')

# =============================================================================
# Predictions are stored here
# =============================================================================
path2predictions=os.path.join(path2experiment,"predictions")
if not os.path.exists(path2predictions):
    os.makedirs(path2predictions)
    print(path2predictions +" created!")

#==============================================================================
# Loading Configs as a data frame if exists
#==============================================================================
path2configs=os.path.join(path2experiment,'configs.csv')
try:
    configsDF=pd.read_csv(path2configs)
    print('-'*50)
    print ('Configs loaded!')
    print('-'*50)
except:
    print('-'*50)
    configsDF=None
    print('there is no default configs!')    
    print('-'*50)   


# =============================================================================
# input image size
# =============================================================================
if configsDF is None:
    if img_height<=128:
        inputStride=1
    elif img_width<=256:
        inputStride=2
else:
    img_hwc=configsDF.loc[configsDF['Name']=='img_hwc','Value'].tolist()[0]
    img_height,img_width,img_channel=ast.literal_eval(img_hwc)
    print('h,w,c loaded from configs!')
print('img_height,img_width,img_channel: %s,%s,%s' %(img_height,img_width,img_channel))    
print('-'*50)




#==============================================================================
# Normalization parameters
#==============================================================================
normTypes={
    '0': None,
    '1': 'zeroMeanUnitStd', 
    '2': 'zeroMeanUnitStdPerSample',
    '3': 'zeroMeanUnitStdGlobal',         
    '4': 'minusOneToPlusOne',
    '5': 'zero2one',
}
if configsDF is None:
    normalization_type=normTypes['2']
    normalization_type=utils_config.getInputFromUser(normTypes,"Choose Normalization type: ")
    normalizationParams={
            'normalization_type' : normalization_type,
            'meanX': None,
            'stdX' : None, 
            }
else:
    # extract normalization type
    normalizationParams=configsDF.loc[configsDF['Name']=='normalizationParams','Value'].tolist()[0]
    normalizationParams=ast.literal_eval(normalizationParams)# convert string to dict     
    normalization_type=normalizationParams['normalization_type']
    print('normalization type loaded from settings!')
    
    print('normalization params loaded from settings!')
print(json.dumps(normalizationParams,indent=4,sort_keys=True))    
print('-'*50)    


#==============================================================================
# model architecture
#==============================================================================
from utils import models
dirModels=dir(models)
modelArchs={}
mdu_i=0
for mdu in dirModels:
    if "model" in mdu:
        mdu_i+=1
        modelArchs[str(mdu_i)]=mdu

if configsDF is None:
    model_type=utils_config.getInputFromUser(modelArchs,"Select a model type:  ")
else:
    model_type=configsDF.loc[configsDF['Name']=='model_type','Value'].tolist()[0]
    print('model type was loaded from settings!')
print ('model %s selected' %model_type)   
print('-'*50)

# =============================================================================
# preprocessing parameters
# =============================================================================
# histogram equalization
if configsDF is None:
    pass
else:
    histeq=configsDF.loc[configsDF['Name']=='histeq','Value'].tolist()[0]        
    if histeq=='True':
        histeq=True
    elif histeq=='False':
        histeq=False
    else:
        raise IOError('histeq not found!')
        
    print('histeq was loaded from settings!')
print('histeq is %s' %histeq)
print('-'*50)


#==============================================================================
# Augmentation parameters
#==============================================================================
            
def preprocessing_function(x):
   
    if normalization_type=="zeroMeanUnitStdPerSample":
        x=np.array(x,'float32')
        for c in range(x.shape[0]):
            meanX=np.mean(x[c])
            stdX = np.std(x[c])
            x[c] -= meanX
            
            if stdX>0.0:
                x[c] /= stdX
    elif normalization_type==None:
        pass
    else:                
        raise IOError(normalization_type+" not found!")
    return x
thismodule = sys.modules[__name__]
pp_func=getattr(thismodule, "preprocessing_function")

if configsDF is None:
    augmentationParams = dict(samplewise_center=False,
                              samplewise_std_normalization=False,
                         rotation_range=10.,
                         width_shift_range=0.1,
                         height_shift_range=0.1,
                         horizontal_flip=True,
                         vertical_flip=True,
                         zoom_range=0.05,
                         shear_range=0.1,
                         preprocessing_function=pp_func,
                         )
else:
    augmentationParams=configsDF.loc[configsDF['Name']=='augmentationParams','Value'].tolist()[0]
    augmentationParams=ast.literal_eval(augmentationParams)    
    augmentationParams["preprocessing_function"]=pp_func
    print('augmentationParams loaded from Configs!')
    print('-'*50)


    
#==============================================================================
# Elastic Parameters
#==============================================================================
elastic_arg = {'elastic_probability': 0.3,
               'nr_of_random_transformations': 1000,  # x and y transformation are separate so total nr is N*N
               'alpha': 2.0,
               'sigma': 0.1
               }    

#==============================================================================
# an optional message
#==============================================================================
if configsDF is None:
    textX='you can enter a note/message:'
    pythonVersion=sys.version_info
    if pythonVersion[0]==2:        
        message=input(textX)
    else:
        message=input(textX)
else:
    message=configsDF.loc[configsDF['Name']=='message','Value'].tolist()[0]
    print('message loaded from Configs!')
print (message)
print('-'*50)


# =============================================================================
# Training Parameters
# =============================================================================
if configsDF is None:
    trainingParams={
            'h': img_height+sum(padSize),
            'w': img_width+sum(padSize),
            'z':img_channel,
            'learning_rate': initialLearningRate,
            #'optimizer': 'Adam',
            'optimizer': 'Nadam',
            #'loss': 'categorical_crossentropy',
            #'loss': 'binary_crossentropy',
            "loss": "custom",
            #"loss": "customCategorical",
            #"loss": "averagePrecision",
            #"loss": "iou_loss",
            'nbepoch': numOfEpochs,
            'numOfOutputs': 1,
            'initial_channels':numOfInputConvFilters,
            'dropout_rate': 0.5,
            'max_patience': 30,
            'experiment': experiment,
            'pre_train': pre_train,
            'elastic_arg': elastic_arg,
            'augmentationParams': augmentationParams,
            'batch_size': 8,
            'path2experiment': path2experiment,
            'w2reg': True, # could be None or True    
            'batchNorm': False,
            'initStride': inputStride,
            'normalizationParams': normalizationParams,
            'reshape4softmax': False,
            "data_format": 'channels_first',
            "augmentation": True,
            "cropping_padding": (13,14),
            #"cropping_padding": (0,0),
            "evalMetric": "evalMetric",
            #"cropping_padding": (0,0),
            "randomCropping": False,
            "elasticTransform": True,
            }
else:
    trainingParams=configsDF.loc[configsDF['Name']=='trainingParams','Value'].tolist()[0]
    trainingParams=ast.literal_eval(trainingParams)    
    trainingParams['path2experiment']=path2experiment # we over write weightfolder
    trainingParams['pre_train']=pre_train # we over write pre_train value
    trainingParams['normalizationParams']=normalizationParams
    trainingParams["augmentationParams"]=augmentationParams
    print('params_train loaded from settings!')
    print('-'*50)
    
#==============================================================================
# we store settings into a csv file for future reference
#==============================================================================
if configsDF is None:
    # we do want to store objects in csv
    augmentationParams_csv=augmentationParams.copy()
    augmentationParams_csv["preprocessing_function"]="preprocessing_function"
    trainingParams_csv=trainingParams.copy()
    trainingParams_csv["augmentationParams"]=augmentationParams_csv
    colsDict={
            'model_type':model_type,
            'normalizationParams':normalizationParams,
            'histeq':histeq,
            'img_hwc':(img_height,img_width,img_channel),
            'path2data':path2data,
            'seed':seed,
            'keras version':utils_config.get_version('keras'),
            'theano version':utils_config.get_version('theano'),
            'numpy version':utils_config.get_version('numpy'),
            'message':message,
            'trainingParams':trainingParams_csv,
            'augmentationParams':augmentationParams_csv,        
            'nFoldsMetrics': None,
            'avgMetric': None,
            'test_size': test_size,
            "model_version":experiment,
            "nonZeroMasksOnly": nonZeroMasksOnly,
            "pre_settings": pre_settings,
            "padSize": padSize,
            "path2predictions": path2predictions,
            }
    col1=list(colsDict.keys())
    col2=list(colsDict.values())
    configD = {'Name': col1, 'Value': col2}
    configsDF=pd.DataFrame(configD)
    
    configsDF.to_csv(path2configs)
    print('-'*50)
    print('Configs saved!')
    print('-'*50)
else:
    print('Configs exists!')
    nonZeroMasksOnly=configsDF.loc[configsDF['Name']=='nonZeroMasksOnly','Value'].tolist()[0]        
    if nonZeroMasksOnly=='True':
        nonZeroMasksOnly=True
    elif nonZeroMasksOnly=='False':
        nonZeroMasksOnly=False
    else:
        raise IOError('nonZeroMasksOnly not found!')
    
    # load pad size
    try:
        padSize=configsDF.loc[configsDF['Name']=='padSize','Value'].tolist()[0]        
        padSize=ast.literal_eval(padSize)    
    except:
        pass
