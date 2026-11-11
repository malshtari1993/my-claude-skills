import cv2, numpy as np
img=cv2.imread("s1.png").astype(np.float32); H,W=img.shape[:2]
rng=np.random.default_rng(7)
n=70
sx=rng.uniform(0,W,n); sy=rng.uniform(0,H,n); sp=rng.uniform(120,420,n); sr=rng.uniform(1.5,5,n); sb=rng.uniform(0.4,1,n); sw=rng.uniform(0,6.28,n)
N=132; fps=30
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
for i in range(N):
    t=i/fps
    f=img*(1+0.04*np.sin(2*np.pi*t*0.8))
    # warm light flicker on the left
    f+= 18*np.exp(-(((xx-120)**2+(yy-120)**2)/(2*200**2)))[...,None]*(0.6+0.4*np.sin(2*np.pi*t*1.3))*np.array([0.6,0.85,1.0])
    layer=np.zeros((H,W,3),np.float32)
    for k in range(n):
        y=(sy[k]+sp[k]*t)%(H+40)-20; x=sx[k]+12*np.sin(t*2+sw[k])
        cv2.circle(layer,(int(x),int(y)),int(sr[k]),(120*sb[k],190*sb[k],255*sb[k]),-1)
    ker=np.zeros((13,13),np.float32); ker[:,6]=1/13
    layer=cv2.filter2D(cv2.GaussianBlur(layer,(0,0),1.2),-1,ker)
    f=np.clip(f+layer*0.9,0,255)
    cv2.imwrite(f"s1f/{i+1:04d}.png",f.astype(np.uint8))
