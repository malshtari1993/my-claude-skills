import cv2, numpy as np, math
img=cv2.imread("s2.png"); H,W=img.shape[:2]
def ell_mask(cx,cy,rx,ry,feather=5):
    m=np.zeros((H,W),np.uint8); cv2.ellipse(m,(cx,cy),(rx,ry),0,0,360,255,-1)
    return cv2.GaussianBlur(m,(0,0),feather)
parts=[(722,88,34,36),(713,182,30,28),(812,142,40,34)]
# inpaint originals
im_mask=np.zeros((H,W),np.uint8)
for cx,cy,rx,ry in parts: cv2.ellipse(im_mask,(cx,cy),(rx+8,ry+8),0,0,360,255,-1)
bg=cv2.inpaint(img,im_mask,6,cv2.INPAINT_TELEA)
sprites=[]
for cx,cy,rx,ry in parts:
    m=ell_mask(cx,cy,rx,ry,3)
    x0,y0,x1,y1=cx-rx-12,cy-ry-12,cx+rx+12,cy+ry+12
    sprites.append((img[y0:y1,x0:x1].copy(), m[y0:y1,x0:x1].copy()))
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
# milk stream mask: slanted band
stream=np.zeros((H,W),np.uint8)
pts=np.array([[903,0],[957,0],[878,325],[826,325]],np.int32); cv2.fillPoly(stream,[pts],255)
stream=cv2.GaussianBlur(stream,(0,0),6).astype(np.float32)/255
def g(cx,cy,s): return np.exp(-(((xx-cx)**2+(yy-cy)**2)/(2*s*s)))
N=165; fps=30
for i in range(N):
    t=i/fps
    dx=np.zeros((H,W),np.float32); dy=np.zeros((H,W),np.float32)
    # stream wobble
    dx+=stream*1.2*np.sin(2*np.pi*(yy/90.0 - t*2.0))
    # splash pulse
    w=g(880,300,70); dx+=w*(xx-880)*0.035*math.sin(2*math.pi*t*1.4); dy+=w*(yy-300)*0.05*math.sin(2*math.pi*t*1.4+0.7)
    w2=g(700,260,55); dy+=w2*-4*math.sin(2*math.pi*t*1.2)
    # berries bobbing
    dy+=g(918,273,30)*3.5*math.sin(2*math.pi*t*0.9)+g(790,265,28)*3.0*math.sin(2*math.pi*t*0.9+1.5)
    frame=cv2.remap(bg,xx+dx,yy+dy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    # stream flowing highlights
    streak=1+0.05*np.sin(2*np.pi*(yy/80.0 - t*3.0))
    frame=frame*(1+((streak-1)*stream)[...,None])
    # falling pieces
    for k,(sp,sm) in enumerate(sprites):
        ph=[0.0,0.38,0.7][k]; p=(t/2.4+ph)%1.0
        sy=-50+p*400; sx=parts[k][0]+ (p-0.3)*40*(1 if k%2==0 else -1)
        ang=p*(300 if k%2==0 else -240)
        h,w=sp.shape[:2]
        Mrot=cv2.getRotationMatrix2D((w/2,h/2),ang,1.0)
        s=cv2.warpAffine(sp,Mrot,(w,h),borderMode=cv2.BORDER_REPLICATE)
        m=cv2.warpAffine(sm,Mrot,(w,h)).astype(np.float32)/255
        k_=9; ker=np.zeros((k_,k_),np.float32); ker[:,k_//2]=1/k_
        s=cv2.filter2D(s,-1,ker); m=cv2.filter2D(m,-1,ker)
        alpha=min(1,p/0.08,(1-p)/0.12)
        x0=int(sx-w/2); y0=int(sy-h/2)
        xa,ya=max(x0,0),max(y0,0); xb,yb=min(x0+w,W),min(y0+h,H)
        if xb>xa and yb>ya:
            sub=s[ya-y0:yb-y0,xa-x0:xb-x0].astype(np.float32); mm=(m[ya-y0:yb-y0,xa-x0:xb-x0]*alpha)[...,None]
            frame[ya:yb,xa:xb]=frame[ya:yb,xa:xb]*(1-mm)+sub*mm
    cv2.imwrite(f"hero/{i+1:04d}.png",np.clip(frame,0,255).astype(np.uint8))
print("frames",N)
