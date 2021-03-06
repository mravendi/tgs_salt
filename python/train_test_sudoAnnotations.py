# train test
import configs
from utils import utils_train_test
import numpy as np
configs.showModelSummary=True

#%%

# =============================================================================
# load data    
# =============================================================================
Y,ids_train=utils_train_test.load_data_sudoAnnotations(configs,"test")
X,_,ids_train=utils_train_test.load_data(configs,"test")
X,_=utils_train_test.histogramEqualization(X,None,configs.histeq)
X,Y=utils_train_test.padArrays(X,Y,configs.padSize)
utils_train_test.array_stats(X)
utils_train_test.array_stats(Y)
utils_train_test.disp_imgs_masks(X,Y)


# =============================================================================
# pick nonzero images and masks
# =============================================================================
X,Y=utils_train_test.separateLargeMasks(X,Y,configs)
    
# =============================================================================
# train for n-Folds
# =============================================================================
evalMatric_nfolds=utils_train_test.trainNfolds(X,Y,configs)


# =============================================================================
# store/update evaluation metrics in configs
# =============================================================================
utils_train_test.updateRecoredInConfigs(configs.path2configs,"nFoldsMetrics",evalMatric_nfolds)
utils_train_test.updateRecoredInConfigs(configs.path2configs,"avgMetric",np.mean(evalMatric_nfolds))

# =============================================================================
# Obtain and store predictions of Ensemble model for train data
# =============================================================================
X,Y,ids_train=utils_train_test.load_data(configs,"train")
X,_=utils_train_test.histogramEqualization(X,None,configs.histeq)
X,Y=utils_train_test.padArrays(X,Y,configs.padSize)
Y_pred=utils_train_test.getOutputAllFolds(X,configs,binaryMask=False)
Y_pred=utils_train_test.unpadArray(Y_pred,configs.padSize)
#utils_train_test.storePredictions(configs,Y_pred,"train")
utils_train_test.storePredictionsWithIds(configs,Y_pred,ids_train,"train")



# =============================================================================
# leaderboard data
# =============================================================================
X_leaderboard,_,ids_leaderboard=utils_train_test.load_data(configs,"test")
X_leaderboard,_=utils_train_test.histogramEqualization(X_leaderboard,None,configs.histeq)

X_leaderboard,_=utils_train_test.padArrays(X_leaderboard,None,configs.padSize)
#X_leaderboard,_=utils_train_test.data_resize(X_leaderboard,None,configs.img_height,configs.img_width)
utils_train_test.array_stats(X_leaderboard)

# =============================================================================
# get output for leaderboard data
# =============================================================================
Y_leaderboard=utils_train_test.getOutputAllFolds(X_leaderboard,configs,binaryMask=False)
Y_leaderboard=utils_train_test.unpadArray(Y_leaderboard,configs.padSize)
#Y_leaderboard,_=utils_train_test.data_resize(Y_leaderboard,None,101,101)
utils_train_test.array_stats(Y_leaderboard)

# =============================================================================
# store predictions of Ensemble model for Leaderboard data
# =============================================================================
#utils_train_test.storePredictions(configs,Y_leaderboard,"test")
utils_train_test.storePredictionsWithIds(configs,Y_leaderboard,ids_leaderboard,"test")

# =============================================================================
# convert outputs to Run Length Dict
# =============================================================================
rlcDict=utils_train_test.converMasksToRunLengthDict(Y_leaderboard>=configs.maskThreshold,ids_leaderboard)    
  

# =============================================================================
# crate submission
# =============================================================================
utils_train_test.createSubmission(rlcDict,configs)




