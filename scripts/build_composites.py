"""Build the two six-panel composites from the publication maps."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
PANELS=[("a_lte800","(a) LTE 800"),("b_mobile900","(b) 900 MHz Mobile Band"),
        ("c_lte1800","(c) LTE 1800"),("d_mobile2100","(d) 2100 MHz Mobile Band"),
        ("e_lte2600","(e) LTE 2600"),("f_nr3600","(f) 5G NR 3600")]
P85={"KT":[2.44,1.58,1.70,1.05,1.28,1.52],"MKA":[1.67,1.36,1.44,1.08,1.75,1.46]}

def font(size,bold=False):
    names=["DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf","arialbd.ttf" if bold else "arial.ttf"]
    for name in names:
        try:return ImageFont.truetype(name,size)
        except OSError:pass
    return ImageFont.load_default()

def centered(draw,x,y,text,f):
    box=draw.textbbox((0,0),text,font=f); draw.text((x-(box[2]-box[0])/2,y),text,font=f,fill="#111827")

def build(prefix):
    folder=ROOT/"outputs"/"figures"/f"{prefix.lower()}_square"
    canvas=Image.new("RGB",(4500,2915),"white"); draw=ImageDraw.Draw(canvas)
    title=("Karl Topia (KT)" if prefix=="KT" else "Mustafa Kemal Atatürk (MKA)")
    n=86 if prefix=="KT" else 85
    centered(draw,2250,35,f"IDW-Interpolated RF-EMF Exposure at {title} Square, Tirana (N = {n})",font(48,True))
    for i,(slug,label) in enumerate(PANELS):
        path=folder/f"{prefix}_IDW_{slug}.png"
        if not path.exists():raise FileNotFoundError(path)
        image=Image.open(path).convert("RGB").crop((250,300,2750,2700)).resize((1420,1110),Image.Resampling.LANCZOS)
        col,row=i%3,i//3; x=col*1500+40; y=150+row*1230
        centered(draw,x+710,y,label,font(36,True)); canvas.paste(image,(x,y+55))
        draw.rounded_rectangle((x+10,y+1120,x+260,y+1175),radius=8,fill="white",outline="#7A8492",width=2)
        draw.text((x+22,y+1130),f"P85 = {P85[prefix][i]:.2f} V/m",font=font(25,True),fill="#1F2937")
    ly=2660; draw.line((280,ly+35,410,ly+35),fill="#0A2292",width=12); draw.text((435,ly+12),"Study area boundary",font=font(31),fill="#111827")
    draw.ellipse((1560,ly+15,1605,ly+60),fill="white",outline="#34406A",width=6); draw.text((1635,ly+12),"Measurement points",font=font(31),fill="#111827")
    draw.line((2860,ly+35,2990,ly+35),fill="#00E7EB",width=12); draw.text((3015,ly),"Hotspot threshold\n85th percentile (band-specific)",font=font(28),fill="#111827")
    out=folder/f"{prefix}_IDW_all_bands_composite.png"; canvas.save(out,dpi=(300,300),optimize=True); print(out)

if __name__=="__main__":
    build("KT"); build("MKA")
