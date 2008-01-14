"""Generator for Distribution"""

from numpy import *
from shogun.Distribution import *

import fileop
import featop
import dataop
from config import DISTRIBUTION, C_DISTRIBUTION

def _get_outdata (name, params):
	"""Return data to be written into the testcase's file.

	After computations and such, the gathered data is structured and
	put into one data structure which can conveniently be written to a
	file that will represent the testcase.
	
	@param name Distribution method's name
	@param params Gathered data
	@return Dict containing testcase data to be written to file
	"""

	ddata=DISTRIBUTION[name]
	outdata={
		'name':name,
		'data_train':matrix(params['data']['train']),
		'data_test':matrix(params['data']['test']),
		'data_class':ddata[0][0],
		'data_type':ddata[0][1],
		'feature_class':ddata[1][0],
		'feature_type':ddata[1][1],
		'distribution_accuracy':ddata[2],
	}

	if ddata[1][0]=='string' or (ddata[1][0]=='simple' and ddata[1][1]=='Char'):
		outdata['alphabet']='DNA'
		outdata['seqlen']=dataop.LEN_SEQ
	elif ddata[1][0]=='string_complex':
		if params.has_key('order'):
			outdata['order']=params['order']
		else:
			outdata['order']=featop.WORDSTRING_ORDER

		if params.has_key('alphabet'):
			outdata['alphabet']=params['alphabet']
		else:
			outdata['alphabet']='DNA'

		outdata['gap']=featop.WORDSTRING_GAP
		outdata['reverse']=featop.WORDSTRING_REVERSE
		outdata['seqlen']=dataop.LEN_SEQ
		outdata['feature_obtain']=ddata[1][2]

	optional=['N', 'M', 'pseudo', 'examples',
		'derivatives', 'likelihood',
		'best_path', 'best_path_state']
	for opt in optional:
		if params.has_key(opt):
			outdata['distribution_'+opt]=params[opt]

	return outdata

def _get_derivatives (distribution, num_vec):
	"""Return the sum of all log_derivatives of a distribution.

	@param distribution Distribution to query
	@param num_vec Number of feature vectors
	@return Sum of all log_derivatives
	"""

	num_param=distribution.get_num_model_parameters()
	derivatives=0

	#print 'num_examples ', num_examples
	#print 'num_param ', num_param
	for i in xrange(num_param):
		#print "i ", i
		for j in xrange(num_vec):
			#print "j ", j
			val=distribution.get_log_derivative(i, j)
			if val!=-inf and val!=nan: # only consider sparse matrix!
				derivatives+=val

	return derivatives

def _run (name):
	"""Run generator for a specific distribution method.

	@param name Name of the distribtuion method
	"""

	params={
		'data':dataop.get_dna(),
	}
	feats=featop.get_string_complex('Word', params['data'])

	fun=eval(name)
	distribution=fun(feats['train'])
	distribution.train()

	params['likelihood']=distribution.get_log_likelihood_sample()
	params['derivatives']=_get_derivatives(
		distribution, feats['train'].get_num_vectors())

	outdata=_get_outdata(name, params)
	fileop.write(C_DISTRIBUTION, outdata)

def _run_hmm ():
	"""Run generator for Hidden-Markov-Model."""

	params={
		'N':3,
		'M':6,
		'examples':4,
		'pseudo':1e-10,
		'order':1,
		'alphabet':'CUBE',
	}

	params['data']=dataop.get_cubes(params['examples'])
	feats=featop.get_string_complex(
		'Word', params['data'], eval(params['alphabet']), params['order'])
	hmm=HMM(feats['train'], params['N'], params['M'], params['pseudo'])
	hmm.train()
	hmm.baum_welch_viterbi_train(BW_NORMAL)

	params['likelihood']=hmm.get_log_likelihood_sample()
	# ShogunException in get_log_derivatives after iteration 9; whatever
	# that means
	params['derivatives']=_get_derivatives(
		hmm, feats['train'].get_num_vectors())


	params['best_path']=0
	params['best_path_state']=0
	for i in xrange(params['examples']):
		params['best_path']+=hmm.best_path(i)
		for j in xrange(params['N']):
			params['best_path_state']+=hmm.get_best_path_state(i, j)

	outdata=_get_outdata('HMM', params)
	fileop.write(C_DISTRIBUTION, outdata)

def run ():
	"""Run generator for all distribution methods."""

	#_run('Histogram')
	#_run('LinearHMM')
	_run_hmm()
