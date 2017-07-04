#!/usr/bin/env python

import os, sys
sys.path = [os.path.dirname(os.path.abspath(__file__))] + sys.path
from liblinear import *
from liblinear import __all__ as liblinear_all
from liblinear import scipy, sparse
from ctypes import c_double

if sys.version_info[0] < 3:
	range = xrange
	from itertools import izip as zip

__all__ = ['svm_read_problem', 'load_model', 'save_model', 'evaluations',
           'train', 'predict'] + liblinear_all


def svm_read_problem(data_file_name, return_scipy=False):
	"""
	svm_read_problem(data_file_name, return_scipy=False) -> [y, x], y: list, x: list of dictionary
	svm_read_problem(data_file_name, return_scipy=True)  -> [y, x], y: ndarray, x: csr_matrix

	Read LIBSVM-format data from data_file_name and return labels y
	and data instances x.
	"""
	prob_y = []
	prob_x = []
	row_ptr = [0]
	col_idx = []
	for i, line in enumerate(open(data_file_name)):
		line = line.split(None, 1)
		# In case an instance with all zero features
		if len(line) == 1: line += ['']
		label, features = line
		prob_y += [float(label)]
		if scipy != None and return_scipy:
			nz = 0
			for e in features.split():
				ind, val = e.split(":")
				val = float(val)
				if val != 0:
					col_idx += [int(ind)-1]
					prob_x += [val]
					nz += 1
			row_ptr += [row_ptr[-1]+nz]
		else:
			xi = {}
			for e in features.split():
				ind, val = e.split(":")
				if val != 0:
					xi[int(ind)] = float(val)
			prob_x += [xi]
	if scipy != None and return_scipy:
		prob_y = scipy.array(prob_y)
		prob_x = scipy.array(prob_x)
		col_idx = scipy.array(col_idx)
		row_ptr = scipy.array(row_ptr)
		prob_x = sparse.csr_matrix((prob_x, col_idx, row_ptr))
	return (prob_y, prob_x)

def load_model(model_file_name):
	"""
	load_model(model_file_name) -> model

	Load a LIBLINEAR model from model_file_name and return.
	"""
	model = liblinear.load_model(model_file_name.encode())
	if not model:
		print("can't open model file %s" % model_file_name)
		return None
	model = toPyModel(model)
	return model

def save_model(model_file_name, model):
	"""
	save_model(model_file_name, model) -> None

	Save a LIBLINEAR model to the file model_file_name.
	"""
	liblinear.save_model(model_file_name.encode(), model)

def evaluations_scipy(ty, pv):
	"""
	evaluations_scipy(ty, pv) -> (ACC, MSE, SCC)
	ty, pv: ndarray

	Calculate accuracy, mean squared error and squared correlation coefficient
	using the true values (ty) and predicted values (pv).
	"""
	if not (scipy != None and isinstance(ty, scipy.ndarray) and isinstance(pv, scipy.ndarray)):
		raise TypeError("type of ty and pv must be ndarray")
	if len(ty) != len(pv):
		raise ValueError("len(ty) must be equal to len(pv)")
	ACC = 100.0*(ty == pv).mean()
	MSE = ((ty - pv)**2).mean()
	l = len(ty)
	sumv = pv.sum()
	sumy = ty.sum()
	sumvy = (pv*ty).sum()
	sumvv = (pv*pv).sum()
	sumyy = (ty*ty).sum()
	with scipy.errstate(all = 'raise'):
		try:
			SCC = ((l*sumvy-sumv*sumy)*(l*sumvy-sumv*sumy))/((l*sumvv-sumv*sumv)*(l*sumyy-sumy*sumy))
		except:
			SCC = float('nan')
	return (float(ACC), float(MSE), float(SCC))

def evaluations(ty, pv, useScipy = True):
	"""
	evaluations(ty, pv, useScipy) -> (ACC, MSE, SCC)
	ty, pv: list, tuple or ndarray
	useScipy: convert ty, pv to ndarray, and use scipy functions for the evaluation

	Calculate accuracy, mean squared error and squared correlation coefficient
	using the true values (ty) and predicted values (pv).
	"""
	if scipy != None and useScipy:
		return evaluations_scipy(scipy.asarray(ty), scipy.asarray(pv))
	if len(ty) != len(pv):
		raise ValueError("len(ty) must be equal to len(pv)")
	total_correct = total_error = 0
	sumv = sumy = sumvv = sumyy = sumvy = 0
	for v, y in zip(pv, ty):
		if y == v:
			total_correct += 1
		total_error += (v-y)*(v-y)
		sumv += v
		sumy += y
		sumvv += v*v
		sumyy += y*y
		sumvy += v*y
	l = len(ty)
	ACC = 100.0*total_correct/l
	MSE = total_error/l
	try:
		SCC = ((l*sumvy-sumv*sumy)*(l*sumvy-sumv*sumy))/((l*sumvv-sumv*sumv)*(l*sumyy-sumy*sumy))
	except:
		SCC = float('nan')
	return (float(ACC), float(MSE), float(SCC))

def train(arg1, arg2=None, arg3=None):
	"""
	train(y, x [, options]) -> model | ACC

	y: a list/tuple/ndarray of l true labels (type must be int/double).

	x: 1. a list/tuple of l training instances. Feature vector of
	      each training instance is a list/tuple or dictionary.

	   2. an l * n numpy ndarray or scipy spmatrix (n: number of features).

	train(prob [, options]) -> model | ACC
	train(prob, param) -> model | ACC

	Train a model from data (y, x) or a problem prob using
	'options' or a parameter param.

	If '-v' is specified in 'options' (i.e., cross validation)
	either accuracy (ACC) or mean-squared error (MSE) is returned.

	options:
		-s type : set type of solver (default 1)
		  for multi-class classification
			 0 -- L2-regularized logistic regression (primal)
			 1 -- L2-regularized L2-loss support vector classification (dual)
			 2 -- L2-regularized L2-loss support vector classification (primal)
			 3 -- L2-regularized L1-loss support vector classification (dual)
			 4 -- support vector classification by Crammer and Singer
			 5 -- L1-regularized L2-loss support vector classification
			 6 -- L1-regularized logistic regression
			 7 -- L2-regularized logistic regression (dual)
		  for regression
			11 -- L2-regularized L2-loss support vector regression (primal)
			12 -- L2-regularized L2-loss support vector regression (dual)
			13 -- L2-regularized L1-loss support vector regression (dual)
		-c cost : set the parameter C (default 1)
		-p epsilon : set the epsilon in loss function of SVR (default 0.1)
		-e epsilon : set tolerance of termination criterion
			-s 0 and 2
				|f'(w)|_2 <= eps*min(pos,neg)/l*|f'(w0)|_2,
				where f is the primal function, (default 0.01)
			-s 11
				|f'(w)|_2 <= eps*|f'(w0)|_2 (default 0.001)
			-s 1, 3, 4, and 7
				Dual maximal violation <= eps; similar to liblinear (default 0.)
			-s 5 and 6
				|f'(w)|_inf <= eps*min(pos,neg)/l*|f'(w0)|_inf,
				where f is the primal function (default 0.01)
			-s 12 and 13
				|f'(alpha)|_1 <= eps |f'(alpha0)|,
				where f is the dual function (default 0.1)
		-B bias : if bias >= 0, instance x becomes [x; bias]; if < 0, no bias term added (default -1)
		-wi weight: weights adjust the parameter C of different classes (see README for details)
		-v n: n-fold cross validation mode
		-q : quiet mode (no outputs)
	"""
	prob, param = None, None
	if isinstance(arg1, (list, tuple)) or (scipy and isinstance(arg1, scipy.ndarray)):
		assert isinstance(arg2, (list, tuple)) or (scipy and isinstance(arg2, (scipy.ndarray, sparse.spmatrix)))
		y, x, options = arg1, arg2, arg3
		prob = problem(y, x)
		param = parameter(options)
	elif isinstance(arg1, problem):
		prob = arg1
		if isinstance(arg2, parameter):
			param = arg2
		else:
			param = parameter(arg2)
	if prob == None or param == None :
		raise TypeError("Wrong types for the arguments")

	prob.set_bias(param.bias)
	liblinear.set_print_string_function(param.print_func)
	err_msg = liblinear.check_parameter(prob, param)
	if err_msg :
		raise ValueError('Error: %s' % err_msg)

	if param.flag_find_C:
		nr_fold = param.nr_fold
		best_C = c_double()
		best_rate = c_double()
		max_C = 1024
		if param.flag_C_specified:
			start_C = param.C
		else:
			start_C = -1.0
		liblinear.find_parameter_C(prob, param, nr_fold, start_C, max_C, best_C, best_rate)
		print("Best C = %lf  CV accuracy = %g%%\n"% (best_C.value, 100.0*best_rate.value))
		return best_C.value,best_rate.value


	elif param.flag_cross_validation:
		l, nr_fold = prob.l, param.nr_fold
		target = (c_double * l)()
		liblinear.cross_validation(prob, param, nr_fold, target)
		ACC, MSE, SCC = evaluations(prob.y[:l], target[:l])
		if param.solver_type in [L2R_L2LOSS_SVR, L2R_L2LOSS_SVR_DUAL, L2R_L1LOSS_SVR_DUAL]:
			print("Cross Validation Mean squared error = %g" % MSE)
			print("Cross Validation Squared correlation coefficient = %g" % SCC)
			return MSE
		else:
			print("Cross Validation Accuracy = %g%%" % ACC)
			return ACC
	else:
		m = liblinear.train(prob, param)
		m = toPyModel(m)

		return m

def predict(y, x, m, options=""):
	"""
	predict(y, x, m [, options]) -> (p_labels, p_acc, p_vals)

	y: a list/tuple/ndarray of l true labels (type must be int/double).
	   It is used for calculating the accuracy. Use [] if true labels are
	   unavailable.

	x: 1. a list/tuple of l training instances. Feature vector of
	      each training instance is a list/tuple or dictionary.

	   2. an l * n numpy ndarray or scipy spmatrix (n: number of features).

	Predict data (y, x) with the SVM model m.
	options:
	    -b probability_estimates: whether to output probability estimates, 0 or 1 (default 0); currently for logistic regression only
	    -q quiet mode (no outputs)

	The return tuple contains
	p_labels: a list of predicted labels
	p_acc: a tuple including  accuracy (for classification), mean-squared
	       error, and squared correlation coefficient (for regression).
	p_vals: a list of decision values or probability estimates (if '-b 1'
	        is specified). If k is the number of classes, for decision values,
	        each element includes results of predicting k binary-class
	        SVMs. if k = 2 and solver is not MCSVM_CS, only one decision value
	        is returned. For probabilities, each element contains k values
	        indicating the probability that the testing instance is in each class.
	        Note that the order of classes here is the same as 'model.label'
	        field in the model structure.
	"""

	def info(s):
		print(s)

	if scipy and isinstance(x, scipy.ndarray):
		x = scipy.ascontiguousarray(x) # enforce row-major
	elif sparse and isinstance(x, sparse.spmatrix):
		x = x.tocsr()
	elif not isinstance(x, (list, tuple)):
		raise TypeError("type of x: {0} is not supported!".format(type(x)))

	if (not isinstance(y, (list, tuple))) and (not (scipy and isinstance(y, scipy.ndarray))):
		raise TypeError("type of y: {0} is not supported!".format(type(y)))

	predict_probability = 0
	argv = options.split()
	i = 0
	while i < len(argv):
		if argv[i] == '-b':
			i += 1
			predict_probability = int(argv[i])
		elif argv[i] == '-q':
			info = print_null
		else:
			raise ValueError("Wrong options")
		i+=1

	solver_type = m.param.solver_type
	nr_class = m.get_nr_class()
	nr_feature = m.get_nr_feature()
	is_prob_model = m.is_probability_model()
	bias = m.bias
	if bias >= 0:
		biasterm = feature_node(nr_feature+1, bias)
	else:
		biasterm = feature_node(-1, bias)
	pred_labels = []
	pred_values = []

	if scipy and isinstance(x, sparse.spmatrix):
		nr_instance = x.shape[0]
	else:
		nr_instance = len(x)

	if predict_probability:
		if not is_prob_model:
			raise TypeError('probability output is only supported for logistic regression')
		prob_estimates = (c_double * nr_class)()
		for i in range(nr_instance):
			if scipy and isinstance(x, sparse.spmatrix):
				indslice = slice(x.indptr[i], x.indptr[i+1])
				xi, idx = gen_feature_nodearray((x.indices[indslice], x.data[indslice]), feature_max=nr_feature)
			else:
				xi, idx = gen_feature_nodearray(x[i], feature_max=nr_feature)
			xi[-2] = biasterm
			label = liblinear.predict_probability(m, xi, prob_estimates)
			values = prob_estimates[:nr_class]
			pred_labels += [label]
			pred_values += [values]
	else:
		if nr_class <= 2:
			nr_classifier = 1
		else:
			nr_classifier = nr_class
		dec_values = (c_double * nr_classifier)()
		for i in range(nr_instance):
			if scipy and isinstance(x, sparse.spmatrix):
				indslice = slice(x.indptr[i], x.indptr[i+1])
				xi, idx = gen_feature_nodearray((x.indices[indslice], x.data[indslice]), feature_max=nr_feature)
			else:
				xi, idx = gen_feature_nodearray(x[i], feature_max=nr_feature)
			xi[-2] = biasterm
			label = liblinear.predict_values(m, xi, dec_values)
			values = dec_values[:nr_classifier]
			pred_labels += [label]
			pred_values += [values]

	if len(y) == 0:
		y = [0] * nr_instance
	ACC, MSE, SCC = evaluations(y, pred_labels)

	if m.is_regression_model():
		info("Mean squared error = %g (regression)" % MSE)
		info("Squared correlation coefficient = %g (regression)" % SCC)
	else:
		info("Accuracy = %g%% (%d/%d) (classification)" % (ACC, int(round(nr_instance*ACC/100)), nr_instance))

	return pred_labels, (ACC, MSE, SCC), pred_values
