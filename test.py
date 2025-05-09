import sqlite3
def run_query(db_file, query):
    # Chuẩn hóa câu truy vấn về 1 dòng
    query = ' '.join(query.split())

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute(query)

    if query.strip().upper().startswith('SELECT'):
        rows = cursor.fetchall()
        col_names = [description[0] for description in cursor.description]

        if not rows:
            return "Không có kết quả."

        # Ghép tên cột và giá trị tương ứng
        result_lines = []
        for row in rows:
            row_text = '\n'.join(f"{col}: {val}" for col, val in zip(col_names, row))
            result_lines.append(row_text)

        return '\n\n'.join(result_lines)
    else:
        conn.commit()
        return "Truy vấn thực thi thành công."

    conn.close()

text ='''
'''
output=run_query('db.sqlite3', text)
print(output)
