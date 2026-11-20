import random


def corpus(count=300):
    rng = random.Random(0xC81)
    out = ['use chip8', 'let mut cpu = chip8::new()']
    operations = ['set', 'add', 'copy', 'or', 'and', 'xor', 'carry', 'sub', 'shr', 'reverse_sub', 'shl', 'eq', 'ne', 'eq_regs', 'ne_regs', 'index', 'jump_v0', 'key_down', 'key_up', 'get_timer', 'delay', 'sound', 'index_add', 'font', 'bcd', 'store', 'load', 'random_zero']
    arithmetic = dict(copy=0, **{'or': 1}, and_=2, xor=3, carry=4, sub=5, shr=6, reverse_sub=7, shl=14)
    arithmetic['and'] = arithmetic.pop('and_')
    for case in range(count):
        op = operations[case % len(operations)]
        x, y = rng.randrange(16), rng.randrange(16)
        if case % 7 == 0:
            y = x
        if case % 5 == 0:
            x = 15
        registers = [rng.randrange(256) for _ in range(16)]
        before = list(registers)
        vx, vy = registers[x], registers[y]
        byte = rng.randrange(256)
        address = rng.randrange(512, 4096)
        index = 768
        delay, sound = 20, 30
        pc = 514
        memory = [rng.randrange(256) for _ in range(16)]
        expected_memory = list(memory)
        keys = [bool(rng.randrange(2)) for _ in range(16)]
        if op in arithmetic:
            opcode = 0x8000 | x << 8 | y << 4 | arithmetic[op]
            if op == 'copy': registers[x] = vy
            elif op == 'or': registers[x] = vx | vy
            elif op == 'and': registers[x] = vx & vy
            elif op == 'xor': registers[x] = vx ^ vy
            elif op == 'carry':
                carry, registers[x] = divmod(vx + vy, 256)
                registers[15] = carry
            elif op in ['sub', 'reverse_sub']:
                left, right = (vx, vy) if op == 'sub' else (vy, vx)
                registers[x] = (left - right) % 256
                registers[15] = int(left >= right)
            elif op == 'shr':
                registers[x], registers[15] = vx // 2, vx % 2
            else:
                registers[x], registers[15] = (vx * 2) % 256, vx // 128
        elif op == 'set': opcode = 0x6000 | x << 8 | byte; registers[x] = byte
        elif op == 'add': opcode = 0x7000 | x << 8 | byte; registers[x] = (vx + byte) % 256
        elif op in ['eq', 'ne']:
            if case % 2 == 0: byte = vx
            opcode = (0x3000 if op == 'eq' else 0x4000) | x << 8 | byte
            pc += 2 * int((vx == byte) == (op == 'eq'))
        elif op in ['eq_regs', 'ne_regs']:
            opcode = (0x5000 if op == 'eq_regs' else 0x9000) | x << 8 | y << 4
            pc += 2 * int((vx == vy) == (op == 'eq_regs'))
        elif op == 'index': opcode = 0xA000 | address; index = address
        elif op == 'jump_v0': opcode = 0xB000 | address; pc = address + registers[0]
        elif op in ['key_down', 'key_up']:
            opcode = 0xE000 | x << 8 | (0x9E if op == 'key_down' else 0xA1)
            pc += 2 * int(keys[vx % 16] == (op == 'key_down'))
        else:
            suffix = dict(get_timer=7, delay=21, sound=24, index_add=30, font=41, bcd=51, store=85, load=101, random_zero=0)[op]
            opcode = (0xC000 if op == 'random_zero' else 0xF000) | x << 8 | suffix
            if op == 'get_timer': registers[x] = delay
            elif op == 'delay': delay = vx
            elif op == 'sound': sound = vx
            elif op == 'index_add': index = (index + vx) % 4096
            elif op == 'font': index = (vx % 16) * 5
            elif op == 'bcd': expected_memory[:3] = [vx // 100, vx // 10 % 10, vx % 10]
            elif op == 'store': expected_memory[:x + 1] = before[:x + 1]
            elif op == 'load': registers[:x + 1] = memory[:x + 1]
            else: registers[x] = 0
        out += ['{', f'cpu.load_rom(vec![{opcode >> 8}, {opcode & 255}]).unwrap()', 'cpu.i = 768', 'cpu.delay_timer = 20', 'cpu.sound_timer = 30']
        out += [f'cpu.v[{j}] = {value}' for j, value in enumerate(before)]
        out += [f'cpu.memory[{768 + j}] = {value}' for j, value in enumerate(memory)]
        out += [f'cpu.keys[{j}] = {str(value).lower()}' for j, value in enumerate(keys)]
        out += ['cpu.cycle().unwrap()', f'let expected_v = vec!{registers}', f'let expected_memory = vec!{expected_memory}']
        out += [f'for j in 0..16 {{ if cpu.v[j] != expected_v[j] || (cpu.memory[768 + j] as int) != expected_memory[j] {{ panic("oracle case {case} ({op}) register/memory") }} }}']
        out += [f'if cpu.pc != {pc} || cpu.i != {index} || cpu.delay_timer != {delay} || cpu.sound_timer != {sound} {{ panic("oracle case {case} ({op}) state") }}', '}']
    out += [f'println("PASS: {count} independent opcode oracle cases")']
    return '\n'.join(out) + '\n'
