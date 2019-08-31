import numpy as np
from mps.state import MPS, TensorArray, DEFAULT_TOLERANCE
from mps.truncate import simplify
from mps.tools import log

def mpo_multiply_tensor(A, B):
    C = np.einsum('aijb,cjd->acibd',A,B)
    s = C.shape
    return C.reshape(s[0]*s[1],s[2],s[3]*s[4])

class MPO(TensorArray):
    """MPO (Matrix Product Operator) class.

    This implements a bare-bones Matrix Product Operator object with open
    boundary conditions. The tensors have four indices, A[α,i,j,β], where
    'α,β' are the internal labels and 'i,j' the physical indices ar the given
    site.

    Parameters
    ----------
    data      -- A list of the tensors that form the MPO
    simplify  -- Use the simplification algorithm after applying the MPO
                 Defaults to False
    maxsweeps, tolerance, normalize, dimension -- arguments used by
                 the simplification routine, if simplify is True.
    """

    def __init__(self, data, simplify=False, maxsweeps=16,
                 tolerance=DEFAULT_TOLERANCE,
                 normalize=False, dimension=None):
        super(MPO, self).__init__(data)
        assert data[0].shape[0] == data[-1].shape[-1] == 1
        self.maxsweeps = maxsweeps
        self.tolerance = tolerance
        self.normalize = normalize
        self.dimension = dimension
        self.simplify = simplify

    def dimensions(self):
        """Return the local dimensions of the MPO."""
        return [A.shape[1] for A in self._data]

    def tomatrix(self):
        """Return the matrix representation of this MPO."""
        D = 1 # Total physical dimension so far
        out = np.array([[[1.]]])
        for A in self._data:
            a, i, j, b = A.shape
            out = np.einsum('lma,aijb->limjb', out, A)
            D *= i
            out = out.reshape(D, D, b)
        return out[:,:,0]
    
    def apply(self, b):
        """Implement multiplication A @ b between an MPO 'A' and
        a Matrix Product State 'b'."""
        if isinstance(b, MPS):
            log(f'Total error before applying MPO {b.error()}')
            err = 0.
            b = MPS([mpo_multiply_tensor(A, B) for A,B in zip(self._data, b)],
                    error=b.error())
            if self.simplify:
                b, err, _ = simplify(b, maxsweeps=self.maxsweeps, tolerance=self.tolerance,
                                     normalize=self.normalize,
                                     dimension=self.dimension)
            log(f'Total error after applying MPO {b.error()}, incremented by {err}')
            return b
        else:
            raise Exception(f'Cannot multiply MPO with {b}')

class MPOList(object):
    """MPO (Matrix Product Operator) list.

    This implements a list of MPOs that are applied sequentially.

    Parameters
    ----------
    mpos  -- A list of the MPOs
    simplify  -- Use the simplification algorithm after applying the MPO
                 Defaults to False
    maxsweeps, tolerance, normalize, dimension -- arguments used by
                 the simplification routine, if simplify is True.
    """

    def __init__(self, mpos, simplify=False, maxsweeps=4,
                 tolerance=DEFAULT_TOLERANCE,
                 normalize=False, dimension=None,):
        self.mpos = mpos
        self.maxsweeps = maxsweeps
        self.tolerance = tolerance
        self.normalize = normalize
        self.dimension = dimension
        self.simplify = simplify

    def tomatrix(self):
        """Return the matrix representation of this MPO."""
        A = 1
        for mpo in self.mpos:
            A = A @ mpo.tomatrix()
        return A
    
    def apply(self, b):
        """Implement multiplication A @ b between an MPO 'A' and
        a Matrix Product State 'b'."""
        for mpo in self.mpos:
            log(f'Total error before applying MPOList {b.error()}')
            b = mpo.apply(b)
            err = 0.
            if self.simplify:
                b, err, _ = simplify(b, maxsweeps=self.maxsweeps, tolerance=self.tolerance,
                                   normalize=self.normalize,
                                   dimension=self.dimension)
            log(f'Total error after applying MPOList {b.error()}, incremented by {err}')
        return b
