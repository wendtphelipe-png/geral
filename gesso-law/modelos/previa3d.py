# Prévia 3D (frente, 3/4, de baixo, lado). Uso: python previa3d.py peca.stl saida.png  -> frente, 3/4, de baixo, lado (sombreado com normais reais)
import sys, numpy as np, trimesh
from numba import njit
from PIL import Image
@njit(cache=True)
def rast(tri, nrm, x0, y0, dx, n):
    z=np.full((n,n),-1e9); N=np.zeros((n,n,3))
    for t in range(tri.shape[0]):
        ax,ay,az=tri[t,0]; bx,by,bz=tri[t,1]; cx,cy,cz=tri[t,2]
        den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(den)<1e-12: continue
        i0=max(int((min(ax,bx,cx)-x0)/dx)-1,0); i1=min(int((max(ax,bx,cx)-x0)/dx)+1,n-1)
        j0=max(int((min(ay,by,cy)-y0)/dx)-1,0); j1=min(int((max(ay,by,cy)-y0)/dx)+1,n-1)
        for j in range(j0,j1+1):
            py=y0+(j+.5)*dx
            for i in range(i0,i1+1):
                px=x0+(i+.5)*dx
                w1=((by-cy)*(px-cx)+(cx-bx)*(py-cy))/den; w2=((cy-ay)*(px-cx)+(ax-cx)*(py-cy))/den; w3=1-w1-w2
                if w1>=0 and w2>=0 and w3>=0:
                    zz=w1*az+w2*bz+w3*cz
                    if zz>z[j,i]:
                        z[j,i]=zz
                        for k in range(3): N[j,i,k]=w1*nrm[t,0,k]+w2*nrm[t,1,k]+w3*nrm[t,2,k]
    return z,N
base=trimesh.load(sys.argv[1])
def vista(rx,ry,px=700):
    m=base.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(ry),[0,1,0]))
    m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rx),[1,0,0]))
    m.apply_translation(-m.bounds.mean(0)); dx=80/px
    z,N=rast(m.vertices[m.faces].astype(float), m.vertex_normals[m.faces].astype(float), -40,-40,dx,px)
    N/=np.maximum(np.linalg.norm(N,axis=2,keepdims=True),1e-9)
    L=np.array([-.45,.55,.7]); L/=np.linalg.norm(L); H=(L+[0,0,1]); H/=np.linalg.norm(H)
    dif=np.clip(N@L,0,1); spec=np.clip(N@H,0,1)**40; fill=np.clip(N@np.array([.5,-.3,.6]),0,1)
    cor=np.array([236,230,220])/255
    img=cor*(0.22+0.68*dif[...,None]+0.15*fill[...,None])+0.10*spec[...,None]
    img=np.clip(img,0,1); img[z<-1e8]=1
    return (img[::-1]*255).astype(np.uint8)
Image.fromarray(np.hstack([vista(0,0),vista(-20,-35),vista(-50,0),vista(0,-80)])).save(sys.argv[2])
