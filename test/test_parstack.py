
import random
import unittest
import multiprocessing
import time
from collections import defaultdict
import numpy as num
from pyrocko import util, trace, autopick

from pyrocko.parstack import parstack


def numeq(a, b, eps):
    return (num.all(num.asarray(a).shape == num.asarray(b).shape and
            num.abs(num.asarray(a) - num.asarray(b)) < eps))


def g(l, a):
    return num.array([getattr(x, a) for x in l])


class ParstackTestCase(unittest.TestCase):

    def test_parstack(self):
        for i in xrange(100):
            narrays = random.randint(1, 5)
            arrays = [
                num.random.random(random.randint(5, 10))
                for j in xrange(narrays)
            ]
            offsets = num.random.randint(-5, 6, size=narrays).astype(num.int32)
            nshifts = random.randint(1, 10)
            shifts = num.random.randint(
                -5, 6, size=(nshifts, narrays)).astype(num.int32)
            weights = num.random.random((nshifts, narrays))

            for method in (0, 1):
                for nparallel in xrange(1, 5):
                    r1, o1 = parstack(
                        arrays, offsets, shifts, weights, method,
                        impl='openmp',
                        nparallel=nparallel)

                    r2, o2 = parstack(
                        arrays, offsets, shifts, weights, method, impl='numpy')

                    assert o1 == o2
                    assert numeq(r1, r2, 1e-9)

    def test_parstack_limited(self):
        for i in xrange(10):
            narrays = random.randint(1, 5)
            arrays = [
                num.random.random(random.randint(5, 10))
                for j in xrange(narrays)
            ]
            offsets = num.random.randint(-5, 6, size=narrays).astype(num.int32)
            nshifts = random.randint(1, 10)
            shifts = num.random.randint(
                -5, 6, size=(nshifts, narrays)).astype(num.int32)
            weights = num.random.random((nshifts, narrays))

            for nparallel in xrange(1, 5):
                r1, o1 = parstack(
                    arrays, offsets, shifts, weights, 0,
                    nparallel=nparallel,
                    impl='openmp')

                for impl in ['openmp', 'numpy']:
                    r2, o2 = parstack(
                        arrays, offsets, shifts, weights, 0,
                        lengthout=r1.shape[1],
                        offsetout=o1,
                        nparallel=nparallel,
                        impl=impl)

                    assert o1 == o2
                    assert numeq(r1, r2, 1e-9)

                    n = r1.shape[1]
                    for k in xrange(n):
                        r3, o3 = parstack(
                            arrays, offsets, shifts, weights, 0,
                            lengthout=n,
                            offsetout=o1-k,
                            nparallel=nparallel,
                            impl=impl)

                        assert o3 == o1-k
                        assert numeq(r1[:, :n-k], r3[:, k:], 1e-9)

                    for k in xrange(n):
                        r3, o3 = parstack(
                            arrays, offsets, shifts, weights, 0,
                            lengthout=n,
                            offsetout=o1+k,
                            nparallel=nparallel,
                            impl=impl)

                        assert o3 == o1+k
                        assert numeq(r1[:, k:], r3[:, :n-k], 1e-9)

                    for k in xrange(n):
                        r3, o3 = parstack(
                            arrays, offsets, shifts, weights, 0,
                            lengthout=n-k,
                            offsetout=o1,
                            nparallel=nparallel,
                            impl=impl)

                        assert o3 == o1
                        assert numeq(r1[:, :n-k], r3[:, :], 1e-9)

    def test_parstack_cumulative(self):
        for i in xrange(10):
            narrays = random.randint(1, 5)
            arrays = [
                num.random.random(random.randint(5, 10))
                for i in xrange(narrays)
            ]
            offsets = num.random.randint(-5, 6, size=narrays).astype(num.int32)
            nshifts = random.randint(1, 10)
            shifts = num.random.randint(
                -5, 6, size=(nshifts, narrays)).astype(num.int32)
            weights = num.random.random((nshifts, narrays))

            for method in (0,):
                for nparallel in xrange(1, 4):
                    result, offset = parstack(
                        arrays, offsets, shifts, weights, method,
                        result=None,
                        nparallel=nparallel,
                        impl='openmp')

                    result1 = result.copy()
                    for k in xrange(5):
                        result, offset = parstack(
                            arrays, offsets, shifts, weights, method,
                            result=result,
                            nparallel=nparallel,
                            impl='openmp')

                        assert numeq(result, result1*(k+2), 1e-9)

    def benchmark(self):

        for nsamples in (10, 100, 1000, 10000):
            nrepeats = max(10, 1000 / nsamples)

            narrays = 20
            arrays = []
            for iarray in xrange(narrays):
                arrays.append(num.arange(nsamples, dtype=num.float))

            offsets = num.arange(narrays, dtype=num.int32)

            nshifts = 100
            shifts = num.zeros((nshifts, narrays), dtype=num.int32)
            weights = num.ones((nshifts, narrays))

            confs = [('numpy', 1)]
            for nparallel in xrange(1, multiprocessing.cpu_count() + 1):
                confs.append(('openmp', nparallel))

            for (impl, nparallel) in confs:
                t0 = time.time()
                for j in xrange(nrepeats):
                    r, o = parstack(
                        arrays, offsets, shifts, weights, 0,
                        impl=impl, nparallel=nparallel)

                t1 = time.time()

                t = t1-t0
                score = nsamples * narrays * nshifts * nrepeats / t / 1e9
                print '%s, %i, %i, %g' % (impl, nparallel, nsamples, score)

    def off_test_synthetic(self):

        from pyrocko import gf

        km = 1000.
        nstations = 10
        edepth = 5*km
        store_id = 'crust2_d0'

        swin = 2.
        lwin = 9.*swin
        ks = 1.0
        kl = 1.0
        kd = 3.0

        engine = gf.get_engine()
        snorths = (num.random.random(nstations)-1.0) * 50*km
        seasts = (num.random.random(nstations)-1.0) * 50*km
        targets = []
        for istation, (snorths, seasts) in enumerate(zip(snorths, seasts)):
            targets.append(
                gf.Target(
                    quantity='displacement',
                    codes=('', 's%03i' % istation, '', 'Z'),
                    north_shift=float(snorths),
                    east_shift=float(seasts),
                    store_id=store_id,
                    interpolation='multilinear'))

        source = gf.DCSource(
            north_shift=50*km,
            east_shift=50*km,
            depth=edepth)

        store = engine.get_store(store_id)

        response = engine.process(source, targets)
        trs = []

        station_traces = defaultdict(list)
        station_targets = defaultdict(list)
        for source, target, tr in response.iter_results():
            tp = store.t('any_P', source, target)
            t = tp - 5 * tr.deltat + num.arange(11) * tr.deltat
            if False:
                gauss = trace.Trace(
                    tmin=t[0],
                    deltat=tr.deltat,
                    ydata=num.exp(-((t-tp)**2)/((2*tr.deltat)**2)))

                tr.ydata[:] = 0.0
                tr.add(gauss)

            trs.append(tr)
            station_traces[target.codes[:3]].append(tr)
            station_targets[target.codes[:3]].append(target)

        station_stalta_traces = {}
        for nsl, traces in station_traces.iteritems():
            etr = None
            for tr in traces:
                sqr_tr = tr.copy(data=False)
                sqr_tr.ydata = tr.ydata**2
                if etr is None:
                    etr = sqr_tr
                else:
                    etr += sqr_tr

            autopick.recursive_stalta(swin, lwin, ks, kl, kd, etr)
            etr.set_codes(channel='C')

            station_stalta_traces[nsl] = etr

        trace.snuffle(trs + station_stalta_traces.values())
        deltat = trs[0].deltat

        nnorth = 50
        neast = 50

        size = 400*km

        north = num.linspace(-size/2., size/2., nnorth)
        north2 = num.repeat(north, neast)
        east = num.linspace(-size/2., size/2., neast)
        east2 = num.tile(east, nnorth)
        depth = 5*km

        def tcal(target, i):
            try:
                return store.t(
                    'any_P',
                    gf.Location(
                        north_shift=north2[i],
                        east_shift=east2[i],
                        depth=depth),
                    target)

            except gf.OutOfBounds:
                return 0.0

        nsls = sorted(station_stalta_traces.keys())

        tts = num.fromiter((tcal(station_targets[nsl][0], i)
                           for i in xrange(nnorth*neast)
                           for nsl in nsls), dtype=num.float)

        arrays = [
            station_stalta_traces[nsl].ydata.astype(num.float) for nsl in nsls]
        offsets = num.array(
            [int(round(station_stalta_traces[nsl].tmin / deltat))
             for nsl in nsls], dtype=num.int32)
        shifts = -num.array(
            [int(round(tt / deltat))
             for tt in tts], dtype=num.int32).reshape(nnorth*neast, nstations)
        weights = num.ones((nnorth*neast, nstations))

        print shifts[25*neast + 25] * deltat

        print offsets.dtype, shifts.dtype, weights.dtype

        print 'stack start'
        mat, ioff = parstack(arrays, offsets, shifts, weights, 1)
        print 'stack stop'

        mat = num.reshape(mat, (nnorth, neast))

        from matplotlib import pyplot as plt

        fig = plt.figure()

        axes = fig.add_subplot(1, 1, 1, aspect=1.0)

        axes.contourf(east/km, north/km, mat)

        axes.plot(
            g(targets, 'east_shift')/km,
            g(targets, 'north_shift')/km, '^')
        axes.plot(source.east_shift/km, source.north_shift/km, 'o')
        plt.show()


if __name__ == '__main__':
    util.setup_logging('test_parstack', 'warning')
    unittest.main()
