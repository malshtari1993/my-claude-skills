import numpy as np, wave
SR=48000; D=12.0; n=int(SR*D); t=np.arange(n)/SR
rng=np.random.default_rng(5)
out=np.zeros((n,2))
def add(sig,start,gain=1.0,pan=0.0):
    i=int(start*SR); j=min(n,i+len(sig)); s=sig[:j-i]*gain
    out[i:j,0]+=s*(1-pan)*0.5*2**0.5*0.75+s*0.25; out[i:j,1]+=s*(1+pan)*0.5*2**0.5*0.75+s*0.25
def lp(x,a): 
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def env(L,att,dec):
    e=np.ones(L); a=int(att*SR); e[:a]=np.linspace(0,1,a); e*=np.exp(-np.arange(L)/SR/dec); return e
# pad: low warm chord with slow swell
pad=np.zeros(n)
for f,amp in [(55,0.5),(82.41,0.35),(110,0.3),(130.81,0.18),(164.81,0.12)]:
    pad+=amp*np.sin(2*np.pi*f*t+np.sin(2*np.pi*0.2*t)*0.5)*(0.7+0.3*np.sin(2*np.pi*0.13*t+f))
pad*=np.clip(t/1.5,0,1)*np.clip((D-t)/1.5,0,1)*0.10
out[:,0]+=pad; out[:,1]+=pad
# riser 0-0.9
L=int(0.9*SR); x=rng.normal(0,1,L); r=np.linspace(0,1,L)
riser=np.diff(np.concatenate([[0],x]))*r**2*0.5 + np.sin(2*np.pi*np.cumsum(200+800*r**2)/SR)*r**3*0.15
add(riser,0.0,0.5)
def boom(dur=1.6,f0=70,f1=32):
    L=int(dur*SR); tt=np.arange(L)/SR; f=f1+(f0-f1)*np.exp(-tt*6)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*2.2)
def crunch(dur=0.35,dens=260,bright=0.6):
    L=int(dur*SR); s=np.zeros(L)
    for _ in range(int(dens*dur)):
        p=rng.integers(0,L-800); gl=int(rng.uniform(80,600)); g=rng.normal(0,1,gl)*np.exp(-np.arange(gl)/(gl/4))
        g=np.diff(np.concatenate([[0],g])) if rng.random()<bright else g
        s[p:p+gl]+=g*rng.uniform(0.3,1)
    return s*np.exp(-np.arange(L)/SR/(dur/2.5))
def whoosh(dur=0.45):
    L=int(dur*SR); x=rng.normal(0,1,L); a=0.02+0.25*np.sin(np.pi*np.arange(L)/L)
    y=np.zeros(L); acc=0
    for k in range(L): acc+=a[k]*(x[k]-acc); y[k]=acc
    return y*np.sin(np.pi*np.arange(L)/L)**2*3
add(boom(),0.9,0.9); add(crunch(0.45,320),0.9,0.55,-0.2); add(crunch(0.3,200),0.98,0.4,0.3)
for c in (3.4,6.4,8.8): add(whoosh(),c-0.25,0.5)
add(boom(1.0,60,35),3.42,0.35)
# rain crunch ticks
for k in range(14):
    add(crunch(0.12,180),6.5+k*0.17+rng.uniform(-0.04,0.04),0.18,rng.uniform(-0.7,0.7))
add(boom(1.8,75,30),8.95,0.8); add(crunch(0.5,340),8.95,0.5)
# soft shimmer on logo
L=int(1.5*SR); tt=np.arange(L)/SR
sh=sum(np.sin(2*np.pi*f*tt)*np.exp(-tt*2.5) for f in (1318.5,1975.5,2637))*0.06
add(sh,9.0,1.0)
out/=max(1e-9,np.abs(out).max())/0.8
pcm=(out*32767).astype(np.int16)
w=wave.open("sfx.wav","wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print("ok")
