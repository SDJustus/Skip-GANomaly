""" This file contains Visualizer class based on Facebook's visdom.

Returns:
    Visualizer(): Visualizer class to display plots and images
"""

##
import os
import time
import numpy as np
import torchvision.utils as vutils
from .plot import plot_confusion_matrix
from .evaluate import get_values_for_pr_curve

##
class Visualizer():
    """ Visualizer wrapper based on Visdom.

    Returns:
        Visualizer: Class file.
    """
    # pylint: disable=too-many-instance-attributes
    # Reasonable.

    ##
    def __init__(self, opt):
        # self.opt = opt
        self.win_size = 256
        self.name = opt.name
        self.opt = opt
        self.writer = None
        # use tensorboard for now
        if self.opt.display:
            from tensorboardX import SummaryWriter
            self.writer = SummaryWriter(log_dir=os.path.join("../tensorboard/skip_ganomaly/", opt.outf))

        # --
        # Dictionaries for plotting data and results.
        self.plot_data = None
        self.plot_res = None

        # --
        # Path to train and test directories.
        self.img_dir = os.path.join(opt.outf, opt.name, 'train', 'images')
        self.tst_img_dir = os.path.join(opt.outf, opt.name, 'test', 'images')
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)
        if not os.path.exists(self.tst_img_dir):
            os.makedirs(self.tst_img_dir)
        # --
        # Log file.
        self.log_name = os.path.join(opt.outf, opt.name, 'loss_log.txt')
        # with open(self.log_name, "a") as log_file:
        #     now = time.strftime("%c")
        #     log_file.write('================ Training Loss (%s) ================\n' % now)
        now  = time.strftime("%c")
        title = f'================ {now} ================\n'
        info  = f'Anomalies, {opt.nz}, {opt.w_adv}, {opt.w_con}, {opt.w_lat}\n'
        self.write_to_log_file(text=title + info)


    ##
    @staticmethod
    def normalize(inp):
        """Normalize the tensor

        Args:
            inp ([FloatTensor]): Input tensor

        Returns:
            [FloatTensor]: Normalized tensor.
        """
        return (inp - inp.min()) / (inp.max() - inp.min() + 1e-5)

    ##
    def plot_current_errors(self, epoch, total_steps, errors):
        """Plot current errros.

        Args:
            epoch (int): Current epoch
            counter_ratio (float): Ratio to plot the range between two epoch.
            errors (OrderedDict): Error for the current epoch.
        """
        self.writer.add_scalars("Loss over time", errors, global_step=total_steps)
        

    ##
    def plot_performance(self, epoch, counter_ratio, performance):
        """ Plot performance

        Args:
            epoch (int): Current epoch
            counter_ratio (float): Ratio to plot the range between two epoch.
            performance (OrderedDict): Performance for the current epoch.
        """
        
        self.writer.add_scalars("Performance Metrics", {k:v for k,v in performance.items() if (k != "conf_matrix" and k != "Avg Run Time (ms/batch)")}, global_step=epoch)
            
        
    def plot_current_conf_matrix(self, epoch, cm):
        plot = plot_confusion_matrix(cm, normalize=False, savefig=False)
        self.writer.add_figure("Confusion Matrix", plot, global_step=epoch)
        

    ##
    def print_current_errors(self, epoch, errors):
        """ Print current errors.

        Args:
            epoch (int): Current epoch.
            errors (OrderedDict): Error for the current epoch.
            batch_i (int): Current batch
            batch_n (int): Total Number of batches.
        """
        # message = '   [%d/%d] ' % (epoch, self.opt.niter)
        message = '   Loss: [%d/%d] ' % (epoch, self.opt.niter)
        for key, val in errors.items():
            message += '%s: %.3f ' % (key, val)

        print(message)
        with open(self.log_name, "a") as log_file:
            log_file.write('%s\n' % message)

    ##
    def write_to_log_file(self, text):
        with open(self.log_name, "a") as log_file:
            log_file.write('%s\n' % text)

    ##
    def print_current_performance(self, performance, best):
        """ Print current performance results.

        Args:
            performance ([OrderedDict]): Performance of the model
            best ([int]): Best performance.
        """
        message = '   '
        #print(performance)
        for key, val in performance.items():
            if key == "conf_matrix":
                message += '%s: %s ' % (key, val)
            else:
                message += '%s: %.3f ' % (key, val)
        message += 'max AUC: %.3f' % best

        print(message)
        self.write_to_log_file(text=message)

    def display_current_images(self, reals, fakes, fixed, train_or_test="train", global_step=0):
        """ Display current images.

        Args:
            epoch (int): Current epoch
            counter_ratio (float): Ratio to plot the range between two epoch.
            reals ([FloatTensor]): Real Image
            fakes ([FloatTensor]): Fake Image
            fixed ([FloatTensor]): Fixed Fake Image
        """
        reals = self.normalize(reals.cpu().numpy())
        fakes = self.normalize(fakes.cpu().numpy())
        # fixed = self.normalize(fixed.cpu().numpy())
        self.writer.add_images("Reals from {} step: ".format(str(train_or_test)), reals, global_step=global_step)
        self.writer.add_images("Fakes from {} step: ".format(str(train_or_test)), fakes, global_step=global_step)
        
    def plot_pr_curve(self, labels, scores, thresholds, global_step):
        tp_counts, fp_counts, tn_counts, fn_counts, precisions, recalls, n_thresholds = get_values_for_pr_curve(labels, scores, thresholds)
        self.writer.add_pr_curve_raw("Precision_recall_curve", true_positive_counts=tp_counts, false_positive_counts=fp_counts, true_negative_counts=tn_counts, false_negative_counts= fn_counts,
                                             precision=precisions, recall=recalls, num_thresholds=n_thresholds, global_step=global_step)
        
    def save_current_images(self, epoch, reals, fakes, fixed):
        """ Save images for epoch i.

        Args:
            epoch ([int])        : Current epoch
            reals ([FloatTensor]): Real Image
            fakes ([FloatTensor]): Fake Image
            fixed ([FloatTensor]): Fixed Fake Image
        """
        vutils.save_image(reals, '%s/reals.png' % self.img_dir, normalize=True)
        vutils.save_image(fakes, '%s/fakes.png' % self.img_dir, normalize=True)
        vutils.save_image(fixed, '%s/fixed_fakes_%03d.png' %(self.img_dir, epoch+1), normalize=True)
