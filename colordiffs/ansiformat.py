from pygments.console import codes, dark_colors, light_colors, esc

def patch_codes():
    dark_bg = [s + '_bg' for s in dark_colors]
    light_bg = [s + '_bg' for s in light_colors]

    x = 40
    for d, l in zip(dark_bg, light_bg):
        codes[d] = esc + "%im" % x
        codes[l] = esc + "%i;01m" % x
        x += 1
