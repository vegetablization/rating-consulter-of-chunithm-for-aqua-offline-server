import os
import sqlite3
import read
import argparse
import configparser


def upgrade():
    reader = read.reader()
    reader.load_files()
    del reader


get_record = """SELECT level,music_id,score_max FROM chusan_user_music_detail"""

create = """CREATE TABLE user_music_detail (
    music_id integer,
    music_level integer,
    score_max integer,
    primary key(music_level,music_id)
);
"""

create_result = """CREATE TABLE result (
    music_id integer,
    music_name varchar(30) not null,
    music_level integer,
    level_name varchar(10),
    music_rate integer,
    music_rate_decimal integer,
    score_max integer,
    rate float,
    primary key(music_level,music_id)
);
"""

insert = """INSERT into user_music_detail(music_level,music_id,score_max) values(?,?,?);"""

insert_result = """INSERT into result(  music_id,
                                        music_level,
                                        score_max,
                                        music_name,
                                        level_name,
                                        music_rate,
                                        music_rate_decimal,
                                        rate) values(?,?,?,?,?,?,?,0);"""

get_result = """SELECT *
FROM user_music_detail 
INNER JOIN music_detail 
ON user_music_detail.music_id=music_detail.music_id
AND user_music_detail.music_level=music_detail.music_level
"""

update = """update result set rate=? where (music_id,music_level)=(?,?); """

if __name__ == "__main__":

    conn = sqlite3.connect(".\\music_level.sqlite")
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table = cur.fetchall()

    if not table or 'music_detail' not in table[0]:
        reader = read.reader()
        reader.createTable()
        reader.load_files()
        del reader
    cur.close()
    conn.close()
    parser = argparse.ArgumentParser()
    parser.add_argument("--upgrade",
                        "-u",
                        help="to upgrade music level database",
                        action='store_true')
    args = parser.parse_args()
    if args.upgrade:
        upgrade()
        exit(1)

    conf = configparser.ConfigParser()
    conf.read(".\\config.cfg")
    dir = os.getcwd()
    sql_dir = conf.get(section='path', option='sql_dir')

    os.chdir(sql_dir)
    connDB = sqlite3.connect('.\\db.sqlite')
    curDB = connDB.cursor()
    record = curDB.execute(get_record)

    os.chdir(dir)
    conn = sqlite3.connect(".\\music_level.sqlite")
    cur = conn.cursor()
    try:
        cur.execute(create)
    except Exception as e:
        if str(e) == "table user_music_detail already exists":
            pass
        else:
            print(e)
    cur.execute("DELETE FROM user_music_detail;")

    try:
        cur.execute(create_result)
    except Exception as e:
        if str(e) == "table result already exists":
            pass
        else:
            print(e)
    cur.execute("DELETE FROM result;")

    cur.executemany(insert, record.fetchall())
    conn.commit()
    curDB.close()
    connDB.close()

    result = cur.execute(get_result)
    for Result in result.fetchall():
        cur.executemany(insert_result,
                        [(Result[0], Result[1], Result[2], Result[4],
                          Result[6], Result[7], Result[8])])
    conn.commit()

    temp = cur.execute("SELECT * FROM result")
    for row in temp.fetchall():
        rate_0 = row[4] + row[5] / 100.0
        score = row[6]
        music_id = row[0]
        music_level = row[2]
        if score > 100_9000:
            rate_fin = rate_0 + 2.15
        elif score > 100_7500:
            rate_fin = rate_0 + 2 + 0.1 * (score - 100_7500) / 1000
        elif score > 100_5000:
            rate_fin = rate_0 + 1.5 + 0.1 * (score - 100_5000) / 500
        elif score > 100_0000:
            rate_fin = rate_0 + 1 + 0.1 * (score - 100_0000) / 1000
        elif score > 97_5000:
            rate_fin = rate_0 + 0 + 0.1 * (score - 97_5000) / 2500
        elif score > 92_5000:
            rate_fin = rate_0 - 3 + 0.1 * (score - 92_5000) / 2500
        elif score > 90_0000:
            rate_fin = rate_0 - 5 + 0.1 * (score - 90_0000) / 1250
        else:
            rate_fin = 0
        rate_fin = ('%.4f' % rate_fin)
        cur.executemany(update, [(rate_fin, music_id, music_level)])
    conn.commit()

    temp = cur.execute(
        "SELECT music_name,level_name,music_rate+music_rate_decimal/100.0,score_max,rate FROM result ORDER BY rate DESC"
    )
    for i in range(30):
        print(i + 1, temp.fetchone())

    cur.close()
    conn.close()


