import json
import psycopg2

# Kết nối tới PostgreSQL trên Render
conn = psycopg2.connect(
    host="dpg-d0htkmi4d50c73at5rgg-a.singapore-postgres.render.com",
    database="db_2025_python_agri_tracechain_414m",
    user="db_2025_python_agri_tracechain_414m_user",
    password="KdBQDQcQ81GQzlQhK4qWnoQQTrye4TOQ",
    port=5432
)
cur = conn.cursor()

# Đọc file tree.json
with open('tree.json', encoding='utf-8') as f:
    data = json.load(f)

def insert_location(code, name, level, parent_code):
    cur.execute(
        "INSERT INTO locations (code, name, level, parent_code) VALUES (%s, %s, %s, %s) ON CONFLICT (code) DO NOTHING",
        (code, name, level, parent_code)
    )

for province_code, province in data.items():
    insert_location(province['code'], province['name'], 'province', None)
    print(f"Đã import tỉnh/thành: {province['name']}")
    for district_code, district in province.get('quan-huyen', {}).items():
        insert_location(district_code, district['name'], 'district', province['code'])
        print(f"  Đã import quận/huyện: {district['name']}")
        for ward_code, ward in district.get('xa-phuong', {}).items():
            insert_location(ward_code, ward['name'], 'ward', district_code)
            print(f"    Đã import xã/phường: {ward['name']}")
            if 'thon-xom' in ward:
                for hamlet_code, hamlet in ward['thon-xom'].items():
                    insert_location(hamlet_code, hamlet['name'], 'hamlet', ward_code)
                    print(f"      Đã import ấp/thôn: {hamlet['name']}")

conn.commit()
cur.close()
conn.close()
print("Import thành công!") 