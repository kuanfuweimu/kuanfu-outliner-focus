"""Create an explicitly illustrative GIF, not a simulated screen recording.

Requires Pillow; first run render_demo.py with Blender in background mode.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = Path(__file__).resolve().parents[1]
FONT = Path('C:/Windows/Fonts')
def font(size, bold=False):
    return ImageFont.truetype(str(FONT / ('segoeuib.ttf' if bold else 'segoeui.ttf')), size)

W, H = 1200, 700
BG = '#15191f'
TEXT = '#eef1f5'
MUTED = '#a7b1bd'
ACCENT = '#ffac58'
models = Image.open(ROOT / 'work/models.png').convert('RGBA').resize((780,446), Image.Resampling.LANCZOS)
names = ['Ring', 'Sphere', 'Cube']
groups = ['Sculptures', 'Studies', 'Primitives']
centers = [186, 405, 624]
frames = []

def draw_frame(stage, tick):
    revealed = tick >= 3
    selected = stage
    expanded = set(range(stage + (1 if revealed else 0)))
    im = Image.new('RGB', (W,H), BG)
    d = ImageDraw.Draw(im)
    d.text((34,24), 'Kuanfu Outliner Focus', font=font(30,True), fill=TEXT)
    d.text((35,67), 'Select an object. Find it in the hierarchy.', font=font(19), fill=MUTED)
    d.rounded_rectangle((30,119,809,581), radius=14, fill='#20262f')
    d.rounded_rectangle((825,119,1170,581), radius=14, fill='#20262f')
    d.text((49,136), 'Scene', font=font(17,True), fill=TEXT)
    d.text((845,136), 'Outliner', font=font(17,True), fill=TEXT)
    d.rounded_rectangle((1022,134,1153,162),radius=12,fill='#293d34')
    d.ellipse((1033,144,1040,151),fill='#83d8a6')
    d.text((1048,136),'Auto reveal',font=font(15),fill='#b9ebcd')
    # A real Blender render, composited into a deliberately simplified diagram.
    mask = models.getchannel('A')
    region = Image.new('L',models.size,0)
    rd = ImageDraw.Draw(region)
    bounds = [(0,270),(270,510),(510,780)][selected]
    rd.rectangle((bounds[0],0,bounds[1],446),fill=255)
    selected_mask = ImageChops.multiply(mask,region)
    outline = ImageChops.subtract(selected_mask.filter(ImageFilter.MaxFilter(7)),selected_mask)
    im.paste(Image.new('RGB',models.size,ACCENT),(30,133),outline)
    im.paste(models,(30,133),mask)
    d = ImageDraw.Draw(im)
    for i, name in enumerate(names):
        x = centers[i]
        if i == selected:
            d.rounded_rectangle((x-54,476,x+54,510),radius=9,fill='#493a2b')
        box = d.textbbox((0,0),name,font=font(19,i==selected))
        d.text((x-(box[2]-box[0])/2,480),name,font=font(19,i==selected),fill=ACCENT if i==selected else MUTED)
    d.text((49,541),'Active object: '+names[selected],font=font(17),fill=TEXT)
    # Expanded groups remain open between steps, matching the add-on.
    y = 192
    d.polygon([(846,y+7),(856,y+7),(851,y+13)],fill=MUTED)
    d.text((865,y),'Scene Collection',font=font(18,True),fill=TEXT)
    y += 42
    for i, group in enumerate(groups):
        opened = i in expanded
        if opened:
            d.polygon([(867,y+8),(877,y+8),(872,y+14)],fill=MUTED)
        else:
            d.polygon([(869,y+4),(869,y+15),(876,y+10)],fill=MUTED)
        d.rounded_rectangle((887,y+5,903,y+18),radius=2,outline='#9da9b9',width=1)
        d.text((913,y),group,font=font(18),fill=TEXT)
        y += 36
        if opened:
            active = i==stage and revealed
            if active:
                d.rounded_rectangle((850,y-2,1154,y+31),radius=6,fill='#3c5674')
            d.line((875,y-12,875,y+15,895,y+15),fill='#56616e',width=1)
            d.polygon([(904,y+6),(918,y+6),(911,y+19)],outline=ACCENT if active else MUTED,width=2)
            d.text((930,y),names[i],font=font(18,active),fill=TEXT)
            y += 40
    d.text((846,546),'View Layer',font=font(15),fill=MUTED)
    status = f'{names[stage]} selected' if not revealed else f'{groups[stage]} expanded  /  {names[stage]} revealed'
    d.text((35,608),status,font=font(23,True),fill=TEXT)
    d.text((35,652),'Illustrated workflow with Blender-rendered models · Not a screen recording',font=font(15),fill=MUTED)
    for i in range(3):
        d.rounded_rectangle((1065+i*32,618,1086+i*32,623),radius=2,fill=ACCENT if i==stage else '#424c59')
    return im

for stage in range(3):
    for tick in range(24):
        frames.append(draw_frame(stage,tick))

palette = frames[30].quantize(colors=192,method=Image.Quantize.MEDIANCUT)
indexed = [f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
target = ROOT / 'assets/outliner-focus-demo.gif'
indexed[0].save(target,save_all=True,append_images=indexed[1:],duration=125,loop=0,optimize=True,disposal=2)
frames[30].save(ROOT/'work/demo-preview.png')
with Image.open(target) as gif:
    assert gif.is_animated and gif.size==(W,H)
    duration = 0
    for i in range(gif.n_frames):
        gif.seek(i)
        duration += gif.info.get('duration',0)
    print(f'{target}: {gif.n_frames} frames, {duration} ms, {target.stat().st_size} bytes')
