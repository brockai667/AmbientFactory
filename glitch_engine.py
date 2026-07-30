# -*- coding: utf-8 -*-
"""Money-glitch reel engine (Lumora prerobena na deadpan 'ako zbohatnut' videa).
Datovo-riadeny: dostane 'scheme' dict (kroky) -> vyrenderuje 9:16 MP4 (maskot + ikony +
velke farebne cisla + loop diagram + rucne pisany font + SUVISLY edge-tts hlas + lip-sync).
Bezi na Windows (lokal test) aj Ubuntu (GitHub Actions) — fonty z repo, ffmpeg auto-detect."""
import os, subprocess, asyncio, math, wave, shutil
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import edge_tts

ROOT = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(ROOT, "fonts", "PatrickHand-Regular.ttf")
W, H, FPS, SR = 1080, 1920, 30, 44100
VOICE, RATE = "en-US-AndrewNeural", "-4%"
BRAND = "@dailymoneyloops"      # placeholder watermark (mozes zmenit)

def _ffmpeg():
    p = shutil.which("ffmpeg")
    if p: return p
    import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
FFMPEG = _ffmpeg()

PAPER=(245,243,236); INK=(38,33,28); RED=(196,54,44); GREEN=(31,138,60)
COL={"red":RED,"green":GREEN,"ink":INK}
SILV=(202,204,210); SILV_R=(140,142,150); GOLDC=(228,192,88); GOLDC_R=(168,132,42)
BILL=(126,176,132); BILL_R=(70,120,80); BILL_INK=(38,92,56)
CARD=(58,86,140); CARDD=(36,58,110); CHIP=(224,192,92); GIFT=(198,76,98); GIFTD=(150,50,70)
ORDER=(240,238,228); ORDER_O=(150,148,138); COPP=(183,115,51); NICK=(178,180,186)
SKIN=(233,209,181); SKIN_O=(122,98,74); HAIR=(150,150,156); MUST=(120,112,110)
BROW=(104,98,94); DARK=(44,38,32); WHITE=(250,250,247)

_FC={}
def F(px):
    px=int(px)
    if px not in _FC: _FC[px]=ImageFont.truetype(FONT, px)
    return _FC[px]
def fit_font(text, size, maxw):
    dd=ImageDraw.Draw(Image.new("RGBA",(1,1))); w=dd.textlength(text,font=F(size))
    return F(size if w<=maxw else max(24,int(size*maxw/w)))
FCAP=F(88); FNUM=F(158); FEQ=F(78); FSMALL=F(60); FWM=F(40)

_noise=(np.random.default_rng(7).normal(0,4,(H//4,W//4,1))).astype(np.int16)
PAPER_IMG=Image.fromarray(np.clip(np.zeros((H//4,W//4,3),np.int16)+np.array(PAPER,np.int16)+_noise,0,255).astype(np.uint8),"RGB").resize((W,H))
def _rr(d,box,r,fill,outline,w): d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=w)

# ================= IKONY (kreslene, priehladne) =================
def ic_dollar(s):
    im=Image.new("RGBA",(s,int(s*0.62)),(0,0,0,0)); d=ImageDraw.Draw(im); w,h=im.size
    _rr(d,(3,3,w-3,h-3),int(h*0.12),BILL,BILL_R,max(3,s//60)); d.ellipse((w*0.36,h*0.24,w*0.64,h*0.76),outline=BILL_INK,width=max(2,s//80))
    d.text((w/2,h/2),"$",font=F(int(h*0.5)),fill=BILL_INK,anchor="mm"); return im
def _coin(s,gold=False,label=None):
    im=Image.new("RGBA",(s,s),(0,0,0,0)); d=ImageDraw.Draw(im); c,r=(GOLDC,GOLDC_R) if gold else (SILV,SILV_R)
    d.ellipse((3,3,s-3,s-3),fill=r); d.ellipse((int(s*.08),int(s*.08),int(s*.92),int(s*.92)),fill=c,outline=r,width=max(2,s//55))
    d.arc((int(s*.2),int(s*.16),int(s*.62),int(s*.6)),200,320,fill=(255,255,255,150),width=max(2,s//40))
    if label: d.text((s/2,s/2),label,font=F(int(s*0.28)),fill=r,anchor="mm")
    return im
def ic_coin(s): return _coin(s,False)
def ic_goldcoin(s): return _coin(s,True)
def ic_cash(s):
    im=Image.new("RGBA",(s,int(s*0.8)),(0,0,0,0)); d=ImageDraw.Draw(im); w,h=im.size
    for i in range(4):
        y=h-18-i*int(h*0.15); _rr(d,(10,y-int(h*0.22),w-10,y),int(h*0.05),BILL,BILL_R,max(2,s//70)); d.text((w/2,y-int(h*0.11)),"$",font=F(int(h*0.14)),fill=BILL_INK,anchor="mm")
    return im
def ic_bag(s):
    im=Image.new("RGBA",(s,s),(0,0,0,0)); d=ImageDraw.Draw(im); w=s
    d.polygon([(w*0.36,w*0.2),(w*0.64,w*0.2),(w*0.58,w*0.32),(w*0.42,w*0.32)],fill=(200,180,120))
    d.ellipse((w*0.16,w*0.3,w*0.84,w*0.92),fill=(206,178,110),outline=(150,120,60),width=max(2,s//55))
    d.text((w/2,w*0.62),"$",font=F(int(s*0.4)),fill=(120,90,40),anchor="mm"); return im
def ic_card(s):
    w,h=s,int(s*0.63); im=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    _rr(d,(3,3,w-3,h-3),int(h*0.12),CARD,CARDD,max(2,s//55)); _rr(d,(int(w*0.1),int(h*0.26),int(w*0.27),int(h*0.5)),4,CHIP,(150,120,40),2)
    d.rectangle((int(w*0.08),int(h*0.6),w-int(w*0.08),int(h*0.7)),fill=(228,228,234)); d.text((w-int(w*0.09),int(h*0.28)),"VISA",font=F(int(s*0.13)),fill=(236,236,242),anchor="ra"); return im
def ic_gift(s):
    w,h=s,int(s*0.63); im=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    _rr(d,(3,3,w-3,h-3),int(h*0.12),GIFT,GIFTD,max(2,s//55)); d.rectangle((int(w*0.44),3,int(w*0.56),h-3),fill=(245,225,120))
    d.rectangle((3,int(h*0.42),w-3,int(h*0.56)),fill=(245,225,120)); d.ellipse((int(w*0.42),int(h*0.34),int(w*0.58),int(h*0.5)),fill=(250,235,150),outline=(200,180,90),width=2); return im
def ic_order(s):
    w,h=int(s*1.12),int(s*0.6); im=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    _rr(d,(3,3,w-3,h-3),6,ORDER,ORDER_O,2)
    for yy in (0.3,0.48): d.line((int(w*0.08),int(h*yy),int(w*0.52),int(h*yy)),fill=(184,182,172),width=3)
    bx0,bx1=int(w*0.6),int(w*0.93); d.rectangle((bx0,int(h*0.28),bx1,int(h*0.72)),outline=(160,158,148),width=2); d.text(((bx0+bx1)//2,int(h*0.5)),"$",font=F(int(s*0.32)),fill=BILL_INK,anchor="mm"); return im
def _metal(s,base,label):
    im=Image.new("RGBA",(s,s),(0,0,0,0)); d=ImageDraw.Draw(im); dk=tuple(max(0,x-45) for x in base); lt=tuple(min(255,x+40) for x in base)
    poly=[(int(x*s),int(y*s)) for x,y in [(0.12,0.55),(0.28,0.3),(0.5,0.24),(0.72,0.32),(0.9,0.52),(0.82,0.78),(0.55,0.9),(0.26,0.82)]]
    d.polygon(poly,fill=base,outline=dk,width=max(2,s//60))
    d.polygon([(int(0.5*s),int(0.24*s)),(int(0.72*s),int(0.32*s)),(int(0.6*s),int(0.55*s)),(int(0.42*s),int(0.5*s))],fill=lt)
    if label: d.text((s/2,int(s*0.56)),label,font=F(int(s*0.22)),fill=(30,28,26),anchor="mm")
    return im
def ic_nickel(s): return _metal(s,NICK,"Ni")
def ic_copper(s): return _metal(s,COPP,"Cu")
def ic_goldbar(s):
    w,h=s,int(s*0.6); im=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.polygon([(int(w*0.16),int(h*0.32)),(int(w*0.84),int(h*0.32)),(int(w*0.96),h-4),(int(w*0.04),h-4)],fill=(228,192,88),outline=(168,132,42),width=max(2,s//60))
    d.polygon([(int(w*0.16),int(h*0.32)),(int(w*0.84),int(h*0.32)),(int(w*0.9),int(h*0.16)),(int(w*0.1),int(h*0.16))],fill=(240,212,120),outline=(168,132,42),width=max(2,s//60))
    return im
def ic_can(s):
    w,hh=int(s*0.5),s; im=Image.new("RGBA",(w,hh),(0,0,0,0)); d=ImageDraw.Draw(im)
    _rr(d,(3,int(hh*0.1),w-3,hh-4),int(w*0.22),(206,58,52),(120,30,28),max(2,s//65)); d.ellipse((3,3,w-3,int(hh*0.19)),fill=(198,198,203),outline=(120,120,125),width=2)
    d.ellipse((int(w*0.22),int(hh*0.05),int(w*0.78),int(hh*0.15)),fill=(168,168,173)); d.rectangle((4,int(hh*0.42),w-4,int(hh*0.6)),fill=(244,244,240)); return im
def ic_phone(s):
    w,h=int(s*0.56),s; im=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    _rr(d,(3,3,w-3,h-3),int(w*0.16),(46,46,52),(20,20,24),max(2,s//55)); _rr(d,(int(w*0.1),int(h*0.08),w-int(w*0.1),int(h*0.9)),int(w*0.08),(150,200,235),None,1)
    d.text((w/2,h*0.49),"$",font=F(int(s*0.34)),fill=(40,110,70),anchor="mm"); return im
def ic_house(s):
    im=Image.new("RGBA",(s,int(s*0.9)),(0,0,0,0)); d=ImageDraw.Draw(im); w,h=im.size
    d.polygon([(w*0.5,h*0.1),(w*0.94,h*0.44),(w*0.06,h*0.44)],fill=(180,80,70),outline=(120,50,44),width=max(2,s//60))
    d.rectangle((w*0.16,h*0.44,w*0.84,h*0.92),fill=(232,214,180),outline=(150,120,90),width=max(2,s//60))
    d.rectangle((w*0.4,h*0.62,w*0.6,h*0.92),fill=(120,90,60)); return im
def ic_chart(s):
    im=Image.new("RGBA",(s,s),(0,0,0,0)); d=ImageDraw.Draw(im); w=s
    d.line((w*0.12,w*0.9,w*0.12,w*0.1),fill=(120,120,125),width=max(2,s//60)); d.line((w*0.12,w*0.9,w*0.9,w*0.9),fill=(120,120,125),width=max(2,s//60))
    pts=[(0.12,0.8),(0.32,0.62),(0.5,0.7),(0.68,0.4),(0.88,0.18)]; d.line([(int(x*w),int(y*w)) for x,y in pts],fill=GREEN,width=max(3,s//30),joint="curve")
    d.polygon([(int(0.88*w),int(0.18*w)),(int(0.78*w),int(0.2*w)),(int(0.86*w),int(0.3*w))],fill=GREEN); return im
def ic_coffee(s):
    im=Image.new("RGBA",(s,s),(0,0,0,0)); d=ImageDraw.Draw(im); w=s
    _rr(d,(w*0.2,w*0.3,w*0.68,w*0.86),int(w*0.06),(238,238,240),(120,120,125),max(2,s//60)); d.arc((int(w*0.62),int(w*0.4),int(w*0.86),int(w*0.66)),300,60,fill=(120,120,125),width=max(2,s//60))
    d.rectangle((w*0.2,w*0.3,w*0.68,w*0.4),fill=(150,100,60)); return im
def ic_gem(s):
    im=Image.new("RGBA",(s,s),(0,0,0,0)); d=ImageDraw.Draw(im); w=s
    d.polygon([(w*0.5,w*0.18),(w*0.82,w*0.42),(w*0.5,w*0.86),(w*0.18,w*0.42)],fill=(120,205,225),outline=(70,150,170),width=max(2,s//55))
    d.line((w*0.18,w*0.42,w*0.82,w*0.42),fill=(70,150,170),width=max(2,s//70)); d.line((w*0.5,w*0.18,w*0.5,w*0.86),fill=(70,150,170),width=max(2,s//80)); return im

ICONS={"dollar":ic_dollar,"coin":ic_coin,"goldcoin":ic_goldcoin,"cash":ic_cash,"bag":ic_bag,"card":ic_card,
       "gift":ic_gift,"order":ic_order,"nickel":ic_nickel,"copper":ic_copper,"goldbar":ic_goldbar,"can":ic_can,
       "phone":ic_phone,"house":ic_house,"chart":ic_chart,"coffee":ic_coffee,"gem":ic_gem}
def icon(name,s): return ICONS.get(name,ic_coin)(s)

def arrow(d,p1,p2,col=INK,w=9):
    d.line((p1,p2),fill=col,width=w); ang=math.atan2(p2[1]-p1[1],p2[0]-p1[0]); L=26
    for a in (ang+2.6,ang-2.6): d.line((p2,(p2[0]+L*math.cos(a),p2[1]+L*math.sin(a))),fill=col,width=w)

# ================= MASKOT (unaveny plesaty chlap, lip-sync) =================
TW,TH=560,820; MCX=TW//2
def draw_char(level,blink):
    im=Image.new("RGBA",(TW,TH),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.polygon([(MCX-100,820),(MCX-100,724),(MCX,772),(MCX+100,724),(MCX+100,820)],fill=(92,118,158))
    d.polygon([(MCX-42,820),(MCX-42,740),(MCX,780),(MCX+42,740),(MCX+42,820)],fill=(236,236,238))
    for sx in (-1,1): d.ellipse((MCX+sx*150-24,398,MCX+sx*150+24,462),fill=SKIN,outline=SKIN_O,width=3)
    d.ellipse((MCX-152,206,MCX+152,676),fill=SKIN,outline=SKIN_O,width=4)
    d.chord((MCX-152,300,MCX-92,520),95,265,fill=HAIR); d.chord((MCX+92,300,MCX+152,520),275,85,fill=HAIR)
    for sx in (-1,1):
        ex=MCX+sx*68; d.line((ex-42,364,ex+40,358),fill=BROW,width=13)
    for sx in (-1,1):
        ex=MCX+sx*68; ey=420
        if blink: d.line((ex-33,ey+2,ex+33,ey+5),fill=DARK,width=7)
        else:
            d.ellipse((ex-35,ey-22,ex+35,ey+22),fill=WHITE,outline=SKIN_O,width=2)
            d.chord((ex-37,ey-30,ex+37,ey+13),184,359,fill=SKIN); d.arc((ex-35,ey-20,ex+35,ey+20),187,357,fill=DARK,width=5)
            d.ellipse((ex-12,ey-1,ex+12,ey+23),fill=DARK)
        d.arc((ex-28,ey+16,ex+28,ey+46),20,160,fill=(198,170,142),width=4)
    d.ellipse((MCX-22,470,MCX+22,524),fill=SKIN,outline=SKIN_O,width=3)
    d.chord((MCX-78,520,MCX-2,582),0,180,fill=MUST); d.chord((MCX+2,520,MCX+78,582),0,180,fill=MUST)
    my=612
    if level<=0: d.line((MCX-32,my,MCX+32,my),fill=DARK,width=6)
    else:
        h=4+6.0*level; d.ellipse((MCX-30,my-h,MCX+30,my+h),fill=DARK); d.ellipse((MCX-12,my+2,MCX+12,my+h*0.7),fill=(150,70,66))
    return im
CHARS={(lv,bl):draw_char(lv,bl) for lv in range(6) for bl in (0,1)}

# ================= audio (suvisle) + casovanie viet =================
def _decode(p):
    r=subprocess.run([FFMPEG,"-v","error","-i",p,"-ac","1","-ar",str(SR),"-f","f32le","-"],capture_output=True).stdout
    return np.frombuffer(r,dtype=np.float32)
def build_audio(steps,tmp):
    FULL=" ".join(s["vo"] for s in steps); mp3=os.path.join(tmp,"vo.mp3")
    async def synth():
        com=edge_tts.Communicate(FULL,VOICE,rate=RATE); sents=[]
        with open(mp3,"wb") as f:
            async for ch in com.stream():
                if ch["type"]=="audio": f.write(ch["data"])
                elif ch["type"]=="SentenceBoundary": sents.append((ch["offset"]/1e7,ch["duration"]/1e7))
        return sents
    sents=asyncio.run(synth()); pcm=_decode(mp3); a=pcm/(np.max(np.abs(pcm)) or 1)*0.95
    a=np.concatenate([a, np.zeros(int(0.5*SR),dtype=np.float32)])   # chvost ticha -> audio >= video (ziadny -shortest orez -> ziadny broken pipe)
    wav=os.path.join(tmp,"vo.wav")
    with wave.open(wav,"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((a*32767).astype("<i2").tobytes())
    total=len(a)/SR
    if len(sents)==len(steps):
        starts=[s[0] for s in sents]
    else:
        L=[len(s["vo"]) for s in steps]; tot=sum(L) or 1; acc=0.0; starts=[]
        for l in L: starts.append(acc/tot*total); acc+=l
    return a,starts,wav,total
def lip_env(a,n):
    win=SR//FPS; env=np.zeros(n)
    for f in range(n):
        seg=a[f*win:(f+1)*win]
        if len(seg): env[f]=math.sqrt(float(np.mean(seg**2)))
    return np.convolve(np.clip((env/(env.max() or 1))**0.6,0,1),np.ones(3)/3,mode="same")

def pop(fr,xy,text,font,color,rev,shadow=False,maxw=1000):
    if rev<=0: return
    d0=ImageDraw.Draw(Image.new("RGBA",(1,1))); wtxt=d0.textlength(text,font=font)
    if wtxt>maxw: font=F(max(20,int(getattr(font,"size",80)*maxw/wtxt)))
    bb=d0.textbbox((0,0),text,font=font); tw,th=bb[2]-bb[0],bb[3]-bb[1]
    lay=Image.new("RGBA",(tw+40,th+40),(0,0,0,0)); ld=ImageDraw.Draw(lay); ox,oy=20-bb[0],20-bb[1]
    if shadow: ld.text((ox+4,oy+5),text,font=font,fill=(0,0,0,60))
    ld.text((ox,oy),text,font=font,fill=color+(int(255*min(1,rev)),))
    x,y=xy; y-=int(18*(1-rev)); fr.paste(lay,(int(x-lay.width//2),int(y-lay.height//2)),lay)
def paste_c(fr,tile,cx,cy,rev=1.0):
    if rev<1: tile=tile.resize((max(1,int(tile.width*(0.85+0.15*rev))),max(1,int(tile.height*(0.85+0.15*rev)))))
    fr.paste(tile,(int(cx-tile.width/2),int(cy-tile.height/2)),tile)

def _scene(fr,d,st,tin,env,blink):
    lay=st.get("layout","icon"); r=max(0,min(1,tin/0.28)); r2=max(0,min(1,(tin-0.28)/0.24))
    num=st.get("num"); ncol=COL.get(st.get("col","green"),GREEN)
    if lay=="mascot":
        lv=int(round(env*5)); bob=int(3*math.sin(tin*1.6)); paste_c(fr,CHARS[(lv,blink)],540,1010+bob,1)
    elif lay=="icon":
        paste_c(fr,icon(st.get("icon","coin"),380),540,880 if num else 980,r)
        if num: pop(fr,(540,1150),num,FNUM,ncol,r2,shadow=True)
    elif lay=="icons":
        for k,(dx,dy) in enumerate([(-200,-10),(-70,40),(60,-20),(190,50),(20,-120)]):
            paste_c(fr,icon(st.get("icon","coin"),185),540+dx,930+dy,min(1,(r*5-k)))
        if num: pop(fr,(540,1230),num,FNUM,ncol,r2,shadow=True)
    elif lay=="two":
        paste_c(fr,icon(st.get("a","dollar"),300),380,900,r)
        if r>0.5: arrow(d,(560,905),(700,905))
        paste_c(fr,icon(st.get("b","cash"),300),790,900,r)
        if num: pop(fr,(540,1180),num,FNUM,ncol,r2,shadow=True)
    elif lay=="equation":
        pop(fr,(540,830),st.get("eq",""),FEQ,INK,r);
        if num: pop(fr,(540,1050),num,FNUM,ncol,r2,shadow=True)
    elif lay=="loop":
        cx,cy,R=540,880,240; P=[(cx,cy-R),(cx+R,cy),(cx,cy+R),(cx-R,cy)]; ic=st.get("loop",["dollar","coin","cash","bag"])
        def edge(a,b,g=92):
            ax,ay=a; bx,by=b; dx,dy=bx-ax,by-ay; L=math.hypot(dx,dy) or 1; ux,uy=dx/L,dy/L; arrow(d,(ax+ux*g,ay+uy*g),(bx-ux*g,by-uy*g))
        if r>0.4:
            for i in range(4): edge(P[i-1],P[i]) if i>0 else edge(P[3],P[0])
        szs=[160,175,150,165]
        for i,nm in enumerate(ic[:4]): paste_c(fr,icon(nm,szs[i]),*P[i],r)
        if num: pop(fr,(cx,cy+R+150),num,FNUM,ncol,r2,shadow=True)

_WM=Image.new("RGBA",(W,60),(0,0,0,0)); ImageDraw.Draw(_WM).text((W/2,20),BRAND,font=FWM,fill=(150,150,150),anchor="mm")

def render(scheme, out_path, tmp=None):
    """scheme = {'steps':[{cap,vo,layout,...}, ...]} -> vyrenderuje MP4 do out_path. Vrati out_path."""
    tmp=tmp or os.path.dirname(os.path.abspath(out_path)) or "."
    steps=scheme["steps"]
    audio,starts,wav,total=build_audio(steps,tmp)
    n=int(total*FPS); env=lip_env(audio,n)
    def step_at(tt):
        i=0
        for k,s in enumerate(starts):
            if tt>=s: i=k
        return i
    blink=set(); fb=25
    while fb<n:
        for k in range(4): blink.add(fb+k)
        fb+=int(3.4*FPS)
    p=subprocess.Popen([FFMPEG,"-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),
        "-i","-","-i",wav,"-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","160k","-shortest",out_path],stdin=subprocess.PIPE)
    for f in range(n):
        tt=f/FPS; ci=step_at(tt); tin=tt-starts[ci]; fr=PAPER_IMG.copy(); d=ImageDraw.Draw(fr)
        _scene(fr,d,steps[ci],tin,env[f],1 if f in blink else 0)
        pop(fr,(540,300),steps[ci]["cap"],FCAP,INK,max(0,min(1,tin/0.25)))
        fr.paste(_WM,(0,H-120),_WM)
        try:
            p.stdin.write(fr.tobytes())
        except (BrokenPipeError, OSError):
            break
    try:
        p.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    p.wait()
    return out_path
