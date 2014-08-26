import math
import numpy as num
from pyrocko import cake

d2r = cake.d2r
r2d = cake.r2d

def globe_cross_section():
    # modified from http://stackoverflow.com/questions/2417794/how-to-make-the-angles-in-a-matplotlib-polar-plot-go-clockwise-with-0-at-the-to

    from matplotlib.projections import PolarAxes, register_projection
    from matplotlib.transforms import Affine2D, Bbox, IdentityTransform

    class GlobeCrossSectionAxes(PolarAxes):
        '''
        A variant of PolarAxes where theta starts pointing north and goes
        clockwise and the radial axis is reversed.
        '''
        name = 'globe_cross_section'

        class GlobeCrossSectionTransform(PolarAxes.PolarTransform):

            def transform(self, tr):
                xy   = num.zeros(tr.shape, num.float_)
                t    = tr[:, 0:1]*d2r
                r    = cake.earthradius - tr[:, 1:2]
                x    = xy[:, 0:1]
                y    = xy[:, 1:2]
                x[:] = r * num.sin(t)
                y[:] = r * num.cos(t)
                return xy

            transform_non_affine = transform

            def inverted(self):
                return GlobeCrossSectionAxes.InvertedGlobeCrossSectionTransform()

        class InvertedGlobeCrossSectionTransform(PolarAxes.InvertedPolarTransform):
            def transform(self, xy):
                x = xy[:, 0:1]
                y = xy[:, 1:]
                r = num.sqrt(x*x + y*y)
                theta = num.arctan2(y, x)*r2d
                return num.concatenate((theta, cake.earthradius-r), 1)

            def inverted(self):
                return GlobeCrossSectionAxes.GlobeCrossSectionTransform()

        def _set_lim_and_transforms(self):
            PolarAxes._set_lim_and_transforms(self)
            self.transProjection = self.GlobeCrossSectionTransform()
            self.transData = (
                self.transScale + 
                self.transProjection + 
                (self.transProjectionAffine + self.transAxes))
            self._xaxis_transform = (
                self.transProjection +
                self.PolarAffine(IdentityTransform(), Bbox.unit()) +
                self.transAxes)
            self._xaxis_text1_transform = (
                self._theta_label1_position +
                self._xaxis_transform)
            self._yaxis_transform = (
                Affine2D().scale(num.pi * 2.0, 1.0) +
                self.transData)
          
            try:
                rlp = getattr(self, '_r_label1_position')
            except AttributeError:
                rlp = getattr(self, '_r_label_position')
            
            self._yaxis_text1_transform = (
                rlp +
                Affine2D().scale(1.0 / 360.0, 1.0) +
                self._yaxis_transform)

    register_projection(GlobeCrossSectionAxes)


tango_colors = {
'butter1': (252, 233,  79),
'butter2': (237, 212,   0),
'butter3': (196, 160,   0),
'chameleon1': (138, 226,  52),
'chameleon2': (115, 210,  22),
'chameleon3': ( 78, 154,   6),
'orange1': (252, 175,  62),
'orange2': (245, 121,   0),
'orange3': (206,  92,   0),
'skyblue1': (114, 159, 207),
'skyblue2': ( 52, 101, 164),
'skyblue3': ( 32,  74, 135),
'plum1': (173, 127, 168),
'plum2': (117,  80, 123),
'plum3': ( 92,  53, 102),
'chocolate1': (233, 185, 110),
'chocolate2': (193, 125,  17),
'chocolate3': (143,  89,   2),
'scarletred1': (239,  41,  41),
'scarletred2': (204,   0,   0),
'scarletred3': (164,   0,   0),
'aluminium1': (238, 238, 236),
'aluminium2': (211, 215, 207),
'aluminium3': (186, 189, 182),
'aluminium4': (136, 138, 133),
'aluminium5': ( 85,  87,  83),
'aluminium6': ( 46,  52,  54)
}

def path2colorint(path):
    '''Calculate an integer representation deduced from path's definition.'''
    s = sum([ord(char) for char in path.phase.definition()])
    return s

def light(color, factor=0.2):
    return tuple( 1-(1-c)*factor for c in color )

def dark(color, factor=0.5):
    return tuple( c*factor for c in color )

def to01(c):
    return c[0]/255., c[1]/255., c[2]/255.

colors = [ to01(tango_colors[x+i]) for i in '321' for x in 'scarletred chameleon skyblue chocolate orange plum butter'.split() ]
shades = [ light(to01(tango_colors['chocolate1']), i*0.1) for i in xrange(1,9) ]
shades2 = [ light(to01(tango_colors['orange1']), i*0.1) for i in xrange(1,9) ]

def plot_xt(paths, zstart, zstop, axes=None, vred=None, distances=None, coloring='by_phase_definition'):
    if distances is not None:
        xmin, xmax = distances.min(), distances.max()
    axes = getaxes(axes)
    all_x = []
    all_t = []
    for ipath, path in enumerate(paths):
        if distances is not None:
            if path.xmax() < xmin or path.xmin() > xmax:
                continue
        if coloring == 'by_phase_definition':
            int_rep = path2colorint(path)
            color = colors[(int_rep+int_rep%7)%len(colors)]        
        else:
            color = colors[ipath%len(colors)]
        p,x,t = path.draft_pxt(path.endgaps(zstart, zstop))
        if p.size == 0:
            continue
        all_x.append(x)
        all_t.append(t)
        if vred is not None:
            axes.plot(x,t-x/vred, linewidth=2, color=color)
            axes.plot([x[0]], [t[0]-x[0]/vred], 'o', color=color)
            axes.plot([x[-1]], [t[-1]-x[-1]/vred], 'o', color=color)
            axes.text(x[len(x)/2], t[len(x)/2]-x[len(x)/2]/vred, path.used_phase().used_repr(), color=color,
                va='center', ha='center', clip_on=True, bbox=dict(ec=color, fc=light(color), pad=8, lw=1), fontsize=10)
        else:
            axes.plot(x,t, linewidth=2, color=color)
            axes.plot([x[0]], [t[0]], 'o', color=color)
            axes.plot([x[-1]], [t[-1]], 'o', color=color)
            axes.text(x[len(x)/2], t[len(x)/2], path.used_phase().used_repr(), color=color,
                va='center', ha='center', clip_on=True, bbox=dict(ec=color, fc=light(color), pad=8, lw=1), fontsize=10)
   
    all_x = num.concatenate(all_x)
    all_t = num.concatenate(all_t)
    if vred is not None:
        all_t -= all_x/vred
    xxx = num.sort( all_x )
    ttt = num.sort( all_t )
    return xxx.min(), xxx[99*len(xxx)/100], ttt.min(), ttt[99*len(ttt)/100]

def labels_xt(axes=None, vred=None, as_degrees=False):
    axes = getaxes(axes)
    if as_degrees:
        axes.set_xlabel('Distance [deg]')
    else:
        axes.set_xlabel('Distance [km]')
        xscaled(d2r*cake.earthradius/cake.km, axes)
        
    if vred is None:
        axes.set_ylabel('Time [s]')
    else:
        if as_degrees:
            axes.set_ylabel('Time - Distance / %g deg/s [ s ]' % (vred))
        else:
            axes.set_ylabel('Time - Distance / %g km/s [ s ]' % (d2r*vred*cake.earthradius/cake.km))

def troffset(dx,dy, axes=None):
    axes = getaxes(axes)
    from matplotlib import transforms
    return axes.transData + transforms.ScaledTranslation(dx/72., dy/72., axes.gcf().dpi_scale_trans)

def plot_xp(paths, zstart, zstop, axes=None, coloring='by_phase_definition'):
    axes = getaxes(axes)
    all_x = []
    for ipath, path in enumerate(paths):
        if coloring == 'by_phase_definition':
            int_rep = path2colorint(path)
            color = colors[(int_rep+int_rep%7)%len(colors)]        
        else:
            color = colors[ipath%len(colors)]
        p, x, t = path.draft_pxt(path.endgaps(zstart, zstop))
        axes.plot(x, p, linewidth=2, color=color)
        axes.plot(x[:1], p[:1], 'o', color=color)
        axes.plot(x[-1:], p[-1:], 'o', color=color)
        axes.text(x[len(x)/2], p[len(x)/2], path.used_phase().used_repr(), color=color,
                va='center', ha='center', clip_on=True, bbox=dict(ec=color, fc=light(color), pad=8, lw=1))
        all_x.append(x)
    
    xxx = num.sort( num.concatenate(all_x) )
    return xxx.min(), xxx[99*len(xxx)/100] 

def labels_xp(axes=None, as_degrees=False):
    axes = getaxes(axes)
    if as_degrees:
        axes.set_xlabel('Distance [deg]')
    else:
        axes.set_xlabel('Distance [km]')
        xscaled(d2r*cake.earthradius*0.001, axes)
    axes.set_ylabel('Ray Parameter [s/deg]')

def labels_model(axes=None):
    axes = getaxes(axes)
    axes.set_xlabel('S-wave and P-wave velocity [km/s]')
    xscaled(0.001, axes)
    axes.set_ylabel('Depth [km]')
    yscaled(0.001, axes)

def plot_rays(paths, rays, zstart, zstop, axes=None, coloring='by_phase_definition', legend=True,
                                                                            avoid_same_colors=True):

    axes = getaxes(axes)
    path_to_color = {}
    available_colors = set()

    for ipath, path in enumerate(paths):
        if coloring == 'by_phase_definition':
            int_rep = path2colorint(path)
            color_id = (int_rep+int_rep % 5) % len(colors)

            if not path.phase.definition() in path_to_color.keys():
                if avoid_same_colors:
                    if len(available_colors) == 0:
                        available_colors = set(range(0, len(colors)-1))
                    if color_id in available_colors:
                        available_colors.remove(color_id)
                    else:
                        color_id = available_colors.pop()

                    assert color_id not in available_colors

                path_to_color[path.phase.definition()] = colors[color_id]
        else:
            path_to_color[path] = colors[ipath % len(colors)]

    if rays is None:
        rays = paths

    labels = set()

    for iray, ray in enumerate(rays):
        if isinstance(ray, cake.RayPath):
            path = ray
            pmin, pmax, xmin, xmax, tmin, tmax = path.ranges(path.endgaps(zstart, zstop))
            if not path._is_headwave:
                p = num.linspace(pmin, pmax, 6)
                x = None

            else:
                x = num.linspace(xmin, xmin*10, 6)
                p = num.atleast_1d(pmin)

            fanz, fanx, _ = path.zxt_path_subdivided(p, path.endgaps(zstart, zstop), x_for_headwave=x)

        else:
            fanz, fanx, _ = ray.zxt_path_subdivided()
            path = ray.path

        if coloring == 'by_phase_definition':
            color = path_to_color[path.phase.definition()]
            phase_label = path.phase.definition()

        else:
            color = path_to_color[path]
            phase_label = path

        for zs, xs in zip(fanz, fanx):
            if phase_label in labels:
                phase_label = ""

            l = axes.plot( xs, zs, color=color, label=phase_label)
            if legend:
                labels.add(phase_label)

    if legend:
        axes.legend(loc=4, prop={'size': 11})


def sketch_model(mod, axes=None):
    from matplotlib import transforms
    axes = getaxes(axes)
    trans = transforms.BlendedGenericTransform(axes.transAxes, axes.transData)
    
    for dis in mod.discontinuities():
        color = shades[-1]
        axes.axhline( dis.z, color=dark(color), lw=1.5)
        if dis.name is not None:
            axes.text(0.90, dis.z, dis.name, transform=trans, va='center', ha='right', color=dark(color),
                    bbox=dict(ec=dark(color), fc=light(color, 0.3), pad=8, lw=1))

    for ilay, lay in enumerate(mod.layers()):
        if isinstance(lay, cake.GradientLayer):
            tab = shades
        else:
            tab = shades2
        color = tab[ilay%len(tab)]
        axes.axhspan( lay.ztop, lay.zbot, fc=color, ec=dark(color), label='abc')
        if lay.name is not None:
            axes.text(0.95, (lay.ztop + lay.zbot)*0.5, lay.name, transform=trans, va='center', ha='right', color=dark(color),
                    bbox=dict(ec=dark(color), fc=light(color, 0.3), pad=8, lw=1))

def plot_source(zstart, axes=None):
    axes = getaxes(axes)
    axes.plot([0], [zstart], 'o', color='black')

def plot_receivers(zstop, distances, axes=None):
    axes = getaxes(axes)
    axes.plot(distances, cake.filled(zstop, len(distances)), '^', color='black')

def getaxes(axes=None):
    from matplotlib import pyplot as plt
    if axes is None:
        return plt.gca()
    else:
        return axes

def mk_sc_classes():
    from matplotlib.ticker import FormatStrFormatter, AutoLocator

    class Scaled(FormatStrFormatter):
        def __init__(self, factor):
            FormatStrFormatter.__init__(self, '%g')
            self._factor = factor

        def __call__(self, v, i=0):
            return FormatStrFormatter.__call__(self, v*self._factor, i)

    class ScaledLocator(AutoLocator):
        def __init__(self, factor):
            AutoLocator.__init__(self)
            self._factor = factor

        def bin_boundaries(self, vmin, vmax):
            return [ x/self._factor for x in AutoLocator.bin_boundaries(self, vmin*self._factor, vmax*self._factor) ]

    return Scaled, ScaledLocator
    
def xscaled(factor, axes):
    Scaled, ScaledLocator = mk_sc_classes()
    xaxis = axes.get_xaxis()
    xaxis.set_major_formatter( Scaled(factor) )
    xaxis.set_major_locator( ScaledLocator(factor) )

def yscaled(factor, axes):
    Scaled, ScaledLocator = mk_sc_classes()
    yaxis = axes.get_yaxis()
    yaxis.set_major_formatter( Scaled(factor) )
    yaxis.set_major_locator( ScaledLocator(factor) )

def labelspace(axes):
    xa = axes.get_xaxis()
    ya = axes.get_yaxis()
    for attr in ('labelpad', 'LABELPAD'):
        if hasattr(xa,attr):
            setattr(xa, attr, xa.get_label().get_fontsize())
            setattr(ya, attr, ya.get_label().get_fontsize())
            break

def labels_rays(axes=None, as_degrees=False):
    axes = getaxes(axes)
    if as_degrees:
        axes.set_xlabel('Distance [deg]')
    else:
        axes.set_xlabel('Distance [km]')
        xscaled(d2r*cake.earthradius/cake.km, axes)
    axes.set_ylabel('Depth [km]')
    yscaled(1./cake.km, axes)

def plot_surface_efficiency(mat):
    from matplotlib import pyplot as plt
    data = []
    for angle in num.linspace(0., 90., 910.):
        pp = math.sin(angle*d2r)/mat.vp
        ps = math.sin(angle*d2r)/mat.vs

        # Unresolved reference: psb_surface and psv_surface_ind
        escp = psv_surface(mat, pp, energy=True) 
        escs = psv_surface(mat, ps, energy=True)
        data.append((angle, escp[psv_surface_ind(P,P)], escp[psv_surface_ind(P,S)], 
                            escs[psv_surface_ind(S,S)], escs[psv_surface_ind(S,P)]))

    a,pp,ps,ss,sp = num.array(data).T

    plt.plot(a,pp, label='PP')
    plt.plot(a,ps, label='PS')
    plt.plot(a,ss, label='SS')
    plt.plot(a,sp, label='SP')
    plt.xlabel('Incident Angle')
    plt.ylabel('Energy Normalized Coefficient', position=(-2.,0.5))
    plt.legend()
    plt.show()

def mpl_init():
    import matplotlib
    matplotlib.rcdefaults()
    matplotlib.rc('axes', linewidth=1.5)
    matplotlib.rc('xtick', direction='out')
    matplotlib.rc('ytick', direction='out')
    matplotlib.rc('xtick.major', size=5)
    matplotlib.rc('ytick.major', size=5)
    matplotlib.rc('figure', facecolor='white')

def my_xt_plot(paths, zstart, zstop, distances=None, as_degrees=False, vred=None, axes=None):

    if axes is None:
        from matplotlib import pyplot as plt
        mpl_init()
        axes = plt.gca()
    else:
        plt = None

    labelspace(axes)
    xmin, xmax, ymin, ymax = plot_xt(paths, zstart, zstop, vred=vred, distances=distances, axes=axes)
    if distances is not None:
        xmin, xmax = distances.min(), distances.max()
    axes.set_xlim(xmin, xmax)
    axes.set_ylim(ymin, ymax)
    labels_xt(as_degrees=as_degrees, vred=vred, axes=axes)
    if plt:
        plt.show()

def my_xp_plot(paths, zstart, zstop, distances=None, as_degrees=False, axes=None):

    if axes is None:
        from matplotlib import pyplot as plt
        mpl_init()
        axes = plt.gca()
    else:
        plt = None

    labelspace(axes)
    xmin, xmax = plot_xp(paths, zstart, zstop, axes=axes)
    if distances is not None:
        xmin, xmax = distances.min(), distances.max()
    axes.set_xlim(xmin, xmax)
    labels_xp(as_degrees=as_degrees, axes=axes)

    if plt:
        plt.show()

def my_rays_plot_gcs(mod, paths, rays, zstart, zstop, distances=None):
    from matplotlib import pyplot as plt
    mpl_init()

    globe_cross_section()
    axes = plt.subplot(1,1,1, projection='globe_cross_section')
    plot_rays(paths, rays, zstart, zstop, axes=axes)
    plot_source(zstart, axes=axes)
    if distances is not None:
        plot_receivers(zstop, distances, axes=axes)

    axes.set_ylim(0.,cake.earthradius)
    axes.get_yaxis().set_visible(False)

    if plt:
        plt.show() 

def my_rays_plot(mod, paths, rays, zstart, zstop, distances=None, as_degrees=False, axes=None):

    if axes is None:
        from matplotlib import pyplot as plt
        mpl_init()
        axes = plt.gca()
    else:
        plt = None

    if paths is None:
        paths = list(set([ x.path for x in rays ]))

    labelspace(axes)
    plot_rays(paths, rays, zstart, zstop, axes=axes)
    xmin, xmax = axes.get_xlim()
    ymin, ymax = axes.get_ylim()
    sketch_model(mod, axes=axes)

    plot_source(zstart, axes=axes)
    if distances is not None:
        plot_receivers(zstop, distances, axes=axes)
    labels_rays(as_degrees=as_degrees, axes=axes)
    mx = (xmax-xmin)*0.05
    my = (ymax-ymin)*0.05
    axes.set_xlim(xmin-mx, xmax+mx)
    axes.set_ylim(ymax+my, ymin-my)

    if plt:
        plt.show()

def my_combi_plot(mod, paths, rays, zstart, zstop, distances=None, as_degrees=False, vred=None):
    from matplotlib import pyplot as plt
    mpl_init()
    ax1 = plt.subplot(211)
    labelspace(plt.gca())
    xmin, xmax, ymin, ymax = plot_xt(paths, zstart, zstop, vred=vred, distances=distances)
    if distances is None:
        plt.xlim(xmin, xmax)

    labels_xt(vred=vred, as_degrees=as_degrees)
    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.xlabel('')

    ax2 = plt.subplot(212, sharex=ax1)
    labelspace(plt.gca())
    plot_rays(paths, rays, zstart, zstop)
    xmin, xmax = plt.xlim()
    ymin, ymax = plt.ylim()
    sketch_model(mod)
    
    plot_source(zstart)
    if distances is not None:
        plot_receivers(zstop, distances)
    labels_rays(as_degrees=as_degrees)
    mx = (xmax-xmin)*0.05
    my = (ymax-ymin)*0.05
    ax2.set_xlim(xmin-mx, xmax+mx)
    ax2.set_ylim(ymax+my, ymin-my)
    plt.show()

def my_model_plot(mod, axes=None):

    if axes is None:
        from matplotlib import pyplot as plt
        mpl_init()
        axes = plt.gca()
    else:
        plt = None

    labelspace(axes)
    labels_model(axes=axes)
    sketch_model(mod, axes=axes)
    z = mod.profile('z')
    vp = mod.profile('vp')
    vs = mod.profile('vs')
    axes.plot(vp, z, color=colors[0], lw=2.)
    axes.plot(vs, z, color=colors[2], lw=2.)
    ymin, ymax = axes.get_ylim()
    xmin, xmax = axes.get_xlim()
    xmin = 0.
    my = (ymax-ymin)*0.05
    mx = (xmax-xmin)*0.2
    axes.set_ylim(ymax+my, ymin-my)
    axes.set_xlim(xmin, xmax+mx)
    if plt:
        plt.show()
