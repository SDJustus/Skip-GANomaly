""" Evaluate ROC
Returns:
    auc, eer: Area under the curve, Equal Error Rate
"""

# pylint: disable=C0103,C0301

##
# LIBRARIES
from __future__ import print_function
import matplotlib
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
matplotlib.use('Agg')
import os
from sklearn.metrics import roc_curve, auc, average_precision_score, f1_score
from scipy.optimize import brentq
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from matplotlib import rc
import numpy as np
import pandas as pd
rc('font', **{'family': 'serif', 'serif': ['Computer Modern']})
rc('text', usetex=False)

def evaluate(labels, scores, metric='roc', output_directory="./", epoch=0):
    if metric == 'roc':
        return roc(labels, scores, output_directory=output_directory, epoch=epoch)
    elif metric == 'auprc':
        return auprc(labels, scores)
    elif metric == 'f1_score':
        threshold = 0.20
        scores[scores >= threshold] = 1
        scores[scores <  threshold] = 0
        return f1_score(labels, scores)
    else:
        raise NotImplementedError("Check the evaluation metric.")

##
def roc(labels, scores, saveto=True, output_directory="./", epoch = 0):
    """Compute ROC curve and ROC area for each class"""
    fpr = dict()
    tpr = dict()
    roc_auc = dict()

    labels = labels.cpu()
    scores = scores.cpu()
    #labels = labels - 1
    #print(labels)
    # True/False Positive Rates.
    fpr, tpr, t = roc_curve(labels, scores)
    roc_auc = auc(fpr, tpr)

    #threshold
    i = np.arange(len(tpr))
    roc = pd.DataFrame({'tf': pd.Series(tpr - (1 - fpr), index=i), 'threshold': pd.Series(t, index=i)})
    roc_t = roc.iloc[(roc.tf - 0).abs().argsort()[:1]]
    threshold = roc_t['threshold']
    threshold = list(threshold)[0]
    #print(list(threshold))
    # Equal Error Rate
    eer = brentq(lambda x: 1. - x - interp1d(fpr, tpr)(x), 0., 1.)

    if saveto:
        plt.figure()
        lw = 2
        plt.plot(fpr, tpr, color='darkorange', lw=lw, label='(AUC = %0.2f, EER = %0.2f)' % (roc_auc, eer))
        plt.plot([eer], [1-eer], marker='o', markersize=5, color="navy")
        plt.plot([0, 1], [1, 0], color='navy', lw=1, linestyle=':')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver operating characteristic')
        plt.legend(loc="lower right")
        plt.savefig(output_directory + "/ROC" + str(epoch) + ".png")
        plt.close()

    return roc_auc, threshold, t

def auprc(labels, scores):
    ap = average_precision_score(labels, scores)
    return ap

def get_values_for_pr_curve(labels, scores, thresholds):
    precisions = []
    recalls = []
    tn_counts = []
    fp_counts = []
    fn_counts = []
    tp_counts = []
    for threshold in thresholds:
        scores_new = [1 if ele >= threshold else 0 for ele in scores] 
        tn, fp, fn, tp = confusion_matrix(labels, scores_new).ravel()
        if len(set(scores_new)) == 1:
            print("y_preds_new did only contain the element {}... Continuing with next iteration!".format(scores_new[0]))
            continue
        
        precision, recall, _, _ = precision_recall_fscore_support(labels, scores_new, average="binary", pos_label=1)
        precisions.append(precision)
        recalls.append(recall)
        tn_counts.append(tn)
        fp_counts.append(fp)
        fn_counts.append(fn)
        tp_counts.append(tp)
        
        
    
    return np.array(tp_counts), np.array(fp_counts), np.array(tn_counts), np.array(fn_counts), np.array(precisions), np.array(recalls), len(thresholds)