import io
import numpy as np
import openpifpaf
import PIL
import torch
import base64
import cv2
import argparse
import csv
import logging
import time
import multiprocessing

from typing import List
from visual import CocoPart, write_on_image, visualise
from processor import Processor
from helpers import pop_and_add
from default_params import *
from writer import write_to_csv
from algorithms import *


class FallDetector:
	def __init__(self,t=DEFAULT_CONSEC_FRAMES):
		self.consecutive_frames=t
		self.args=self.cli()

	def cli(self):
	    parser = argparse.ArgumentParser(
	        description=__doc__,
	        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	    )
	    # TODO: Verify the args since they were changed in v0.10.0
	    openpifpaf.decoder.cli(parser, force_complete_pose=True,
	                           instance_threshold=0.2, seed_threshold=0.5)
	    openpifpaf.network.nets.cli(parser)
	    parser.add_argument('--resolution', default=0.4, type=float,
	                        help=('Resolution prescale factor from 640x480. '
	                              'Will be rounded to multiples of 16.'))
	    parser.add_argument('--resize', default=None, type=str,
	                        help=('Force input image resize. '
	                              'Example WIDTHxHEIGHT.'))
	    parser.add_argument('--video', default=None, type=str,
	                        help='Path to the video file.')
	    parser.add_argument('--debug', default=False, action='store_true',
	                        help='debug messages and autoreload')
	    parser.add_argument('--enable_cuda', default=False, action='store_true',
	                        help='enables cuda support and runs from gpu')

	    vis_args = parser.add_argument_group('Visualisation')
	    vis_args.add_argument('--joints', default=True, action='store_true',
	                          help='Draw joint\'s keypoints on the output video.')
	    vis_args.add_argument('--skeleton', default=True, action='store_true',
	                          help='Draw skeleton on the output video.')
	    vis_args.add_argument('--save-output', default=False, action='store_true',
	                          help='Save the result in a video file.')
	    vis_args.add_argument('--fps', default=20, type=int,
	                          help='FPS for the output video.')
	    vis_args.add_argument('--out-path', default='result.avi', type=str,
	                          help='Save the output video at the path specified. .avi file format.')
	    vis_args.add_argument('--csv-path', default='keypoints.csv', type=str,
	                          help='Save the pose coordinates into a CSV file at the path specified.')

	    args = parser.parse_args()

	    # Log
	    logging.basicConfig(level=logging.INFO if not args.debug else logging.DEBUG)

	    # Add args.device
	    args.device = torch.device('cpu')
	    print(args.enable_cuda)
	    args.pin_memory = False
	    if args.enable_cuda and torch.cuda.is_available():
	        args.device = torch.device('cuda')
	        args.pin_memory = True

	    return args




	def begin(self):
		queue=multiprocessing.Queue()
		print("Queue Made")
		process1=multiprocessing.Process(target=extract_keypoints,args=(queue,self.args,self.consecutive_frames))
		print("P1 made")
		process2=multiprocessing.Process(target=alg2,args=(queue,self.consecutive_frames))
		print("P2 made")
		process1.start()
		process2.start()
		process1.join()
		process2.join()


if __name__ == "__main__":
    f=FallDetector()
    f.begin()
