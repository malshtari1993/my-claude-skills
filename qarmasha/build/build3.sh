set -e
FB="scale=-2:1920:flags=lanczos,scale=w='iw*(1+0.012*t)':h=-2:eval=frame,crop=1080:1920:x='(iw-1080)/2+OFF+DX*(t-2)*15':y='(ih-1920)/2',unsharp=5:5:0.6,noise=alls=7:allf=t,vignette=PI/5,format=yuv420p"
ffmpeg -y -loglevel error -framerate 30 -i s1f/%04d.png -vf "$(echo "$FB" | sed 's/DX/1/;s/OFF/0/')" -c:v libx264 -crf 17 c1.mp4
ffmpeg -y -loglevel error -framerate 30 -i hero/%04d.png -vf "$(echo "$FB" | sed 's/DX/-1/;s/OFF/300/')" -c:v libx264 -crf 17 c2.mp4
ffmpeg -y -loglevel error -i c1.mp4 -i c2.mp4 -loop 1 -t 10 -i grad.png -loop 1 -t 10 -i t1.png -loop 1 -t 10 -i t2.png -loop 1 -t 10 -i t3.png -i voice.mp3 -filter_complex "
[0][1]xfade=transition=fade:duration=0.4:offset=4.0,fade=t=in:st=0:d=0.3[x];
[3:v]format=rgba,fade=t=in:st=0.5:d=0.3:alpha=1,fade=t=out:st=2.7:d=0.25:alpha=1[o1];
[4:v]format=rgba,fade=t=in:st=3.0:d=0.3:alpha=1,fade=t=out:st=5.5:d=0.25:alpha=1[o2];
[5:v]format=rgba,fade=t=in:st=5.8:d=0.3:alpha=1[o3];
[x][2:v]overlay[g];[g][o1]overlay[y1];[y1][o2]overlay[y2];[y2][o3]overlay,fade=t=out:st=9.1:d=0.4,format=yuv420p[v];
[6:a]adelay=500|500,volume=1.3,apad,afade=t=out:st=9.0:d=0.5[a]" -map "[v]" -map "[a]" -t 9.5 -c:v libx264 -crf 18 -c:a aac -b:a 192k ../qarmasha_ad_v3.mp4
