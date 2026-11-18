# Floco de neve original, com volume (tubos arredondados), para virar peça de gesso.
import numpy as np, trimesh
from skimage.measure import marching_cubes
from scipy import ndimage
dx=0.25; L=30
xs=np.arange(-L,L,dx); X,Y,Z=np.meshgrid(xs,xs,np.arange(-6,8,dx),indexing='ij')
def seg(p,q,r):
    p=np.array(p);q=np.array(q);v=q-p;t=np.clip(((X-p[0])*v[0]+(Y-p[1])*v[1])/(v@v),0,1)
    d2=np.hypot(X-p[0]-t*v[0],Y-p[1]-t*v[1]); return np.sqrt(d2**2+Z**2)-r
def smin(a,b,k):
    h=np.clip(0.5+0.5*(b-a)/k,0,1); return b*(1-h)+a*h-k*h*(1-h)
d=np.hypot(X,Y)  # miolo hexagonal arredondado
ang=np.arctan2(Y,X); hexr=6.5/np.cos(((ang+np.pi/6)%(np.pi/3))-np.pi/6)
d=np.sqrt(np.maximum(d-hexr,0)**2+ (Z/1.4)**2)-3.2
for i in range(6):
    a=np.pi/2+i*np.pi/3; u=np.array([np.cos(a),np.sin(a)]); n=np.array([-u[1],u[0]])
    d=smin(d,seg((0,0),25*u,2.4),1.5)
    for t,l in ((11,7.5),(18,5.5)):
        b=t*u
        for s in (1,-1):
            d=smin(d,seg(b,b+l*(0.55*u+s*0.84*n),1.8),1.2)
    tip=27.5*u; d=smin(d,np.sqrt((X-tip[0])**2+(Y-tip[1])**2+Z**2)-3.2,1.0)
v,f,_,_=marching_cubes(d,0,spacing=(dx,dx,dx))
v=v+np.array([xs[0],xs[0],-6])
m=trimesh.Trimesh(v,f[:,::-1]); trimesh.smoothing.filter_taubin(m,iterations=8)
if m.volume<0: m.invert()
m.export('/tmp/claude-0/natal/floco_fig.stl'); print(m.extents, m.is_watertight)
