
import numpy as np
from chainercv.transforms import resize
from chainer import cuda
from chainer import function
import chainer.functions as F

class GlimpseSensor(function.Function):
	def __init__(self, center, output_size, using_conv = False, depth=1, scale=2):
		if type(output_size) is not tuple:
			self.output_size = output_size
		else:
			assert output_size[0] == output_size[1],"Output dims must be same"
			self.output_size = output_size[0]
		self.center = center
		self.depth = depth
		self.scale = scale
		self.using_conv = using_conv

	def forward(self, images):
		xp = cuda.get_array_module(*images)

		n, c, h_i, w_i = images[0].shape
		assert h_i == w_i, "Image should be square"
		size_i = h_i
		size_o = self.output_size

		# [-1, 1]^2 -> [0, size_i - 1]x[0, size_i - 1]
		center = (0.5 * (self.center + 1) * (size_i - 1)).data  # center:shape -> [n X 2]

		y = xp.zeros(shape=(n, c*self.depth, size_o, size_o), dtype=np.float32)

		xmin = xp.zeros(shape=(self.depth, n), dtype=np.int32)
		ymin = xp.zeros(shape=(self.depth, n), dtype=np.int32)
		xmax = xp.zeros(shape=(self.depth, n), dtype=np.int32)
		ymax = xp.zeros(shape=(self.depth, n), dtype=np.int32)

		for depth in range(self.depth):
			xmin[depth] = xp.round(xp.clip(center[:, 0] - (0.5 * size_o * (xp.power(self.scale,depth))), 0., float(size_i - 1)))
			ymin[depth] = xp.round(xp.clip(center[:, 1] - (0.5 * size_o * (xp.power(self.scale,depth))), 0, size_i - 1))
			xmax[depth] = xp.round(xp.clip(center[:, 0] + (0.5 * size_o * (xp.power(self.scale,depth))), 0, size_i - 1))
			ymax[depth] = xp.round(xp.clip(center[:, 1] + (0.5 * size_o * (xp.power(self.scale,depth))), 0, size_i - 1))

		for i in range(n):
			for j in range(self.depth):
				cropped = images[0][i][:,xmin[j][i]:xmax[j][i]+1, ymin[j][i]:ymax[j][i]+1]
				resized = resize(cropped, (self.output_size, self.output_size))
				y[i][c*j: (c*j)+c] = resized

		if self.using_conv:
			return y,
		else:
			return y.reshape(n,-1),

	def backward(self, images, gy):
		#return zero grad
		xp = cuda.get_array_module(*images)
		n, c_in ,h_i, w_i = images[0].shape
		gx = xp.zeros(shape=(n, c_in, h_i, w_i), dtype=np.float32)
		return gx,


def getGlimpses(x, center, size, depth=1, scale=2):
	return GlimpseSensor(center, size, depth, scale)(x)



