import cv2, numpy as np, math
img=cv2.imread("s2.png"); H,W=img.shape[:2]
rng=np.random.default_rng(3)
def ell(cx,cy,rx,ry,f=3):
    m=np.zeros((H,W),np.uint8); cv2.ellipse(m,(cx,cy),(rx,ry),0,0,360,255,-1); return cv2.GaussianBlur(m,(0,0),f)
parts=[(722,88,34,36),(713,182,30,28),(812,142,40,34)]
im_mask=np.zeros((H,W),np.uint8)
for cx,cy,rx,ry in parts: cv2.ellipse(im_mask,(cx,cy),(rx+8,ry+8),0,0,360,255,-1)
bg=cv2.inpaint(img,im_mask,6,cv2.INPAINT_TELEA)
sprites=[]
for cx,cy,rx,ry in parts:
    m=ell(cx,cy,rx,ry); x0,y0,x1,y1=cx-rx-12,cy-ry-12,cx+rx+12,cy+ry+12
    sprites.append((img[y0:y1,x0:x1].copy(),m[y0:y1,x0:x1].astype(np.float32)/255))
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
stream=np.zeros((H,W),np.uint8)
cv2.fillPoly(stream,[np.array([[903,0],[957,0],[878,325],[826,325]],np.int32)],255)
stream=cv2.GaussianBlur(stream,(0,0),6).astype(np.float32)/255
def g(cx,cy,s): return np.exp(-(((xx-cx)**2+(yy-cy)**2)/(2*s*s)))
N=165; fps=30; FALL=0.75
# drops: one piece every 0.32s
drops=[]
t0=-0.5
while t0<N/fps:
    lx=rng.uniform(640,900); ly=rng.uniform(290,330)
    drops.append(dict(t0=t0,lx=lx,ly=ly,sx=lx+rng.uniform(-40,40),sp=int(rng.integers(0,3)),sc=rng.uniform(0.8,1.3),rot=rng.uniform(-400,400),
        spl=[(rng.uniform(-1,1)*rng.uniform(80,260),-rng.uniform(220,480),rng.uniform(3,9)) for _ in range(int(rng.integers(18,27)))]))
    t0+=rng.uniform(0.26,0.38)
ker=np.zeros((11,11),np.float32); ker[:,5]=1/11
for i in range(N):
    t=i/fps
    dx=stream*1.2*np.sin(2*np.pi*(yy/90.0-t*2.0)); dy=np.zeros((H,W),np.float32)
    w=g(880,300,70); dx+=w*(xx-880)*0.035*math.sin(2*math.pi*t*1.4); dy+=w*(yy-300)*0.05*math.sin(2*math.pi*t*1.4+0.7)
    dy+=g(918,273,30)*3.5*math.sin(2*math.pi*t*0.9)+g(790,265,28)*3.0*math.sin(2*math.pi*t*0.9+1.5)
    # surface ripples where pieces landed recently
    for d in drops:
        a=t-(d['t0']+FALL)
        if 0<a<0.8:
            r=np.sqrt((xx-d['lx'])**2+((yy-d['ly'])*2.2)**2)
            dy+=np.exp(-((r-a*90)**2)/(2*12**2))*3.0*(1-a/0.8)
    f=cv2.remap(bg,xx+dx,yy+dy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    f*= (1+((0.05*np.sin(2*np.pi*(yy/80.0-t*3.0)))*stream))[...,None]
    milk=np.zeros((H,W,3),np.float32); malpha=np.zeros((H,W),np.float32)
    for d in drops:
        a=t-d['t0']
        if 0<=a<FALL:
            p=a/FALL; y=-70+(d['ly']+70)*p*p; x=d['sx']+(d['lx']-d['sx'])*p
            sp,sm=sprites[d['sp']]; h0,w0=sp.shape[:2]; sc=d['sc']
            s=cv2.resize(sp,(int(w0*sc),int(h0*sc))); m=cv2.resize(sm,(int(w0*sc),int(h0*sc)))
            h,w=s.shape[:2]; M=cv2.getRotationMatrix2D((w/2,h/2),d['rot']*p,1)
            s=cv2.warpAffine(s,M,(w,h),borderMode=cv2.BORDER_REPLICATE); m=cv2.warpAffine(m,M,(w,h))
            if p>0.35: s=cv2.filter2D(s,-1,ker); m=cv2.filter2D(m,-1,ker)
            al=min(1,a/0.1)*(1 if p<0.88 else (1-p)/0.12)
            x0=int(x-w/2); y0=int(y-h/2); xa,ya=max(x0,0),max(y0,0); xb,yb=min(x0+w,W),min(y0+h,H)
            if xb>xa and yb>ya:
                mm=(m[ya-y0:yb-y0,xa-x0:xb-x0]*al)[...,None]
                f[ya:yb,xa:xb]=f[ya:yb,xa:xb]*(1-mm)+s[ya-y0:yb-y0,xa-x0:xb-x0].astype(np.float32)*mm
        b=a-FALL
        if 0<=b<0.7:
            if b<0.45:
                jh=int(6+38*math.sin(math.pi*b/0.45)); jw=int(10+10*(1-b/0.45))
                cv2.ellipse(milk,(int(d['lx']),int(d['ly'])-jh//2),(jw,max(3,jh//2)),0,0,360,(238,242,245),-1)
                cv2.ellipse(malpha,(int(d['lx']),int(d['ly'])-jh//2),(jw,max(3,jh//2)),0,0,360,0.9,-1)
            for vx,vy,r in d['spl']:
                px=d['lx']+vx*b; py=d['ly']+vy*b+0.5*900*b*b
                if py<d['ly']+5:
                    cv2.circle(milk,(int(px),int(py)),int(r),(240,244,246),-1); cv2.circle(malpha,(int(px),int(py)),int(r),0.95*(1-b/0.7)+0.05,-1)
    malpha=cv2.GaussianBlur(malpha,(0,0),1.2)[...,None]; milk=np.full((H,W,3),(236,241,244),np.float32)
    f=f*(1-malpha)+milk*malpha
    cv2.imwrite(f"hero/{i+1:04d}.png",np.clip(f,0,255).astype(np.uint8))
print("ok",len(drops))
