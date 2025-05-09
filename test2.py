def tach_mo_ta_va_sql(doan_text: str):
    lines = doan_text.strip().splitlines()
    mo_ta = ''
    sql_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('--'):
            mo_ta = stripped_line[2:].strip()  # Bỏ dấu -- và khoảng trắng
        elif stripped_line != '':
            sql_lines.append(line)  # Giữ nguyên dòng gốc (gồm cả khoảng trắng và xuống dòng)

    sql = '\n'.join(sql_lines)
    return mo_ta, sql

text =''' 

'''
mota, sql = tach_mo_ta_va_sql(text)
print("Mô tả:", mota)
print("SQL:", sql) 