from .formats import green_bg, red_bg, discreet


def output_diff_chunk(dc, colorized_a, colorized_b):
    results = [discreet(dc.diff_line)]
    for instr in dc.output_instructions:
        if instr[0] == ' ':
            results.append(' ' + dc.a_hunk.get_current_line(colorized_a))
            dc.b_hunk.get_current_line(colorized_b)  # for side effect
        if instr[0] == '-':
            results.append(red_bg('-') + dc.a_hunk.get_current_line(colorized_a))
        if instr[0] == '+':
            results.append(green_bg('+') + dc.b_hunk.get_current_line(colorized_b))
    return results


def output(diff, colorized_a, colorized_b):
    print(discreet(diff.header))
    print(discreet(diff.index))
    print(discreet(diff.line_a))
    print(discreet(diff.line_b))
    for dc in diff.dcs:
        for o in output_diff_chunk(dc, colorized_a, colorized_b):
            print(o)
