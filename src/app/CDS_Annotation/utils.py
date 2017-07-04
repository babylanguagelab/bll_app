import cPickle
import wave
import os


def save_data(obj, filename):
	with open(filename, 'wb') as f:
		cPickle.dump(obj, f, cPickle.HIGHEST_PROTOCOL)


def load_data(filename):
	with open(filename, 'rb') as f:
		data = cPickle.load(f)
	return data


def merge_clips(clips):
	raw_data = ''
	for clip in clips:
		f = wave.open(clip, 'rb')
		raw_data += f.readframes(-1)
		if clip == clips[0]:
			n_channels, sample_width, sample_rate, _, _, _ = f.getparams()
		f.close()

	return raw_data, n_channels, sample_width, sample_rate


def merge_coders_data(path, datafiles):
	data = {}
	for dfile in datafiles:
		coder = dfile.strip('.pkl')
		with open(os.path.join(path, dfile), 'rb') as f:
			data[coder] = cPickle.load(f)
	return data


