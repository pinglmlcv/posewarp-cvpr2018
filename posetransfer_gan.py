import tensorflow as tf
import os
import numpy as np
import sys
import cv2
import datareader
import preprocess
import networks
import scipy.io as sio
import param
from keras.models import load_model,Model
from keras.optimizers import Adam

batch_size = 8
gpu = '/gpu:3'
test_interval = 200
save_interval = 5000

n_test_vids = 13
vid_pth = '../../datasets/golfswinghd/videos/'
info_pth = '../../datasets/golfswinghd/videoinfo/'
n_end_remove = 5
img_sfx = '.jpg'
n_train_examples = 100000
n_test_examples = 1000

params = param.getParam()

def train():	
	config = tf.ConfigProto()
	config.gpu_options.allow_growth = True
	config.allow_soft_placement = True

	ex_train,ex_test = datareader.makeTransferExampleList(
		vid_pth,info_pth,n_test_vids,n_end_remove,img_sfx,n_train_examples,n_test_examples)

	train_feed = preprocess.transferExampleGenerator(ex_train,batch_size,params)
	test_feed = preprocess.transferExampleGenerator(ex_test,batch_size,params)
	
	with tf.Session(config=config) as sess:

		sess.run(tf.global_variables_initializer())
		coord = tf.train.Coordinator()
		threads = tf.train.start_queue_runners(coord=coord)

		with tf.device(gpu):
			generator = networks.network1(params)
			discriminator = networks.discriminator(params)
			gan = networks.gan(generator,discriminator,params)
	
		step = 0	
		while(True):
			X_img,X_pose,X_tgt = next(train_feed)			

			with tf.device(gpu):
				X_gen = generator.predict([X_img,X_pose])
	
			networks.make_trainable(discriminator,True)

			X_img_disc = np.concatenate((X_img,X_gen))
			X_pose_disc = np.concatenate((X_pose[:,:,:,0:n_joints],X_pose[:,:,:,n_joints:]))
			y1 = np.zeros([2*batch_size,2])
			y1[0:batch_size,1] = 1
			y1[batch_size:,0] = 1		

			with tf.device(gpu):
				d_loss = discriminator.train_on_batch([X_img_disc, X_pose_disc],y1])

			networks.make_trainable(discriminator,False)

			X_img,X_pose,X_tgt = next(train_feed)			
	
			y2 = np.zeros([batch_size,2])
			y2[:,1] = 1

			gan_loss = gan.train_on_batch([X_img,X_pose],[X_tgt,y2])
	
			'''
			if(step % test_interval == 0):
				n_batches = 8
	
				test_loss = 0		
				for j in xrange(n_batches):	
					X_img,X_pose,X_tgt = next(test_feed)
					pred_val = model.predict([X_img,X_pose,V],batch_size=batch_size)
					test_loss += np.sum((pred_val-X_tgt)**2)/(batch_size)
	
				test_loss /= (n_batches*params['IMG_HEIGHT']*params['IMG_WIDTH']*3)
				print "1," + str(test_loss)
				sys.stdout.flush()

				sio.savemat('../results/outputs/network1_small/' + str(step) + '.mat',
         		{'X_img': X_img,'X_tgt': X_tgt, 'pred': pred_val})	
	
			if(step % save_interval==0): # and step > 0):
				model.save('../results/networks/network1_small/' + str(step) + '.h5')			

			step += 1	
			'''
if __name__ == "__main__":
	train()

