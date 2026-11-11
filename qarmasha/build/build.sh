set -e
mk() { # in out dir zoomrate
ffmpeg -y -loglevel error -loop 1 -framerate 30 -i $1 -filter_complex "[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5,eq=brightness=-0.12[bg];[b]scale=w='2044*(1+$4*t)':h=-2:eval=frame,crop=1080:1150:x='(iw-1080)/2+$3*(t-1.85)*60':y='(ih-1150)/2'[fg];[bg][fg]overlay=0:385,format=yuv420p[v]" -map "[v]" -t 3.7 -c:v libx264 $2
}
mk s1.png c1.mp4 1 0.012
mk s2.png c2.mp4 -1 0.010
mk s3.png c3.mp4 1 0.012
ffmpeg -y -loglevel error -i c1.mp4 -i c2.mp4 -i c3.mp4 -loop 1 -t 11 -i t1.png -loop 1 -t 11 -i t2.png -loop 1 -t 11 -i t3.png -i voice.mp3 -filter_complex "
[0][1]xfade=transition=fade:duration=0.4:offset=3.3[x1];
[x1][2]xfade=transition=fade:duration=0.4:offset=6.6[x2];
[3:v]format=rgba,fade=t=in:st=0.6:d=0.4:alpha=1,fade=t=out:st=3.0:d=0.3:alpha=1[o1];
[4:v]format=rgba,fade=t=in:st=4.0:d=0.4:alpha=1,fade=t=out:st=6.4:d=0.3:alpha=1[o2];
[5:v]format=rgba,fade=t=in:st=7.4:d=0.4:alpha=1[o3];
[x2][o1]overlay[y1];
[y1][o2]overlay[y2];
[y2][o3]overlay,fade=t=out:st=9.9:d=0.4[v];
[6:a]adelay=500|500,volume=1.3,apad,afade=t=out:st=9.8:d=0.5[a]" -map "[v]" -map "[a]" -t 10.3 -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -b:a 192k ../qarmasha_ad_v2.mp4
